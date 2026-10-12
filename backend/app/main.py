import logging
import re
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from app.config import Settings
from app.graph.connection import GraphConnection, GraphUnavailable
from app.models.api import ErrorBody, ErrorResponse, HealthResponse, Services

logger = logging.getLogger("promiseops.api")


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def error(request: Request, status: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            request_id=request.state.request_id,
        )
    )
    return JSONResponse(body.model_dump(), status_code=status)


def create_app(settings: Settings | None = None, graph: GraphConnection | None = None) -> FastAPI:
    settings = settings or Settings()
    graph = graph or GraphConnection(settings)

    @asynccontextmanager
    async def lifespan(app):
        app.state.graph = graph
        try:
            yield
        finally:
            await run_in_threadpool(graph.close)

    app = FastAPI(
        title="PromiseOps",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.debug_docs else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context(request, call_next):
        hint = request.headers.get("x-request-id", "")
        request.state.request_id = hint if re.fullmatch(r"[\x21-\x7e]{1,64}", hint) else uuid4().hex
        started = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            # Do not log exception text, URL, body, headers, source text or stack locals.
            response = error(request, 500, "INTERNAL_ERROR", "Request could not be completed.")
        response.headers["X-Request-ID"] = request.state.request_id
        logger.info(
            "request_completed",
            extra={
                "request_id": request.state.request_id,
                "status": response.status_code,
                "duration_ms": round((time.monotonic() - started) * 1000),
            },
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_payload(request, exc):
        return error(request, 422, "VALIDATION_ERROR", "Request does not match the schema.")

    @app.exception_handler(GraphUnavailable)
    async def unavailable(request, exc):
        return error(request, 503, "GRAPH_UNAVAILABLE", "Required graph is unavailable.")

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 401: "UNAUTHORIZED", 403: "FORBIDDEN"}
        return error(
            request,
            exc.status_code,
            codes.get(exc.status_code, "REQUEST_ERROR"),
            "Request could not be completed.",
        )

    @app.get(
        "/api/health", response_model=HealthResponse, responses={503: {"model": HealthResponse}}
    )
    def health(request: Request):
        available = graph.ready()
        result = HealthResponse(
            request_id=request.state.request_id,
            status="OK" if available else "DEGRADED",
            services=Services(api="OK", graph="OK" if available else "UNAVAILABLE"),
            checked_at=utc_now(),
        )
        return JSONResponse(result.model_dump(), status_code=200 if available else 503)

    @app.get("/internal/live", include_in_schema=False)
    def live(request: Request):
        return {"request_id": request.state.request_id, "status": "OK"}

    return app
