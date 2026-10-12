from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import Field

from app.auth import authenticate, authenticate_credential, issue_session
from app.config import Settings
from app.models.common import StrictModel, Timestamp


class BootstrapRequest(StrictModel):
    credential: str = Field(min_length=1, max_length=512)


class ActorResponse(StrictModel):
    id: str
    roles: list[str]


class SessionResponse(StrictModel):
    request_id: str
    actor: ActorResponse
    mode: str
    expires_at: Timestamp


def _utc(exp: int) -> str:
    return (
        datetime.fromtimestamp(exp, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    )


def router(settings: Settings) -> APIRouter:
    api = APIRouter()

    @api.post("/api/session", response_model=SessionResponse)
    def bootstrap(request: Request, body: BootstrapRequest):
        if not settings.demo_mode or not settings.demo_users or settings.session_secret is None:
            raise HTTPException(503)
        origin = request.headers.get("origin")
        if origin is not None and origin not in settings.frontend_origins:
            raise HTTPException(403)
        actor_id = authenticate_credential(settings, body.credential)
        if actor_id is None:
            raise HTTPException(401)
        token, exp = issue_session(settings, actor_id)
        user = settings.demo_users[actor_id]
        from fastapi.responses import JSONResponse

        result = SessionResponse(
            request_id=request.state.request_id,
            actor=ActorResponse(id=actor_id, roles=sorted(user.roles)),
            mode="MOCK",
            expires_at=_utc(exp),
        )
        response = JSONResponse(result.model_dump())
        response.set_cookie(
            "promiseops_session",
            token,
            max_age=3600,
            httponly=True,
            samesite="strict",
            secure=False,
            path="/api",
        )
        return response

    @api.get("/api/session", response_model=SessionResponse)
    def current(request: Request):
        actor = authenticate(request, settings)
        return SessionResponse(
            request_id=request.state.request_id,
            actor=ActorResponse(id=actor.id, roles=sorted(actor.roles)),
            mode="MOCK",
            expires_at=_utc(actor.expires_at),
        )

    return api
