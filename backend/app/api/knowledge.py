"""Read-only graph, operation trace, health and evidence excerpts."""

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from app.auth import authenticate
from app.models.common import Id


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)


def router(settings, service):
    api = APIRouter()

    @api.get("/api/graph/{entity_id}")
    def graph(
        request: Request,
        entity_id: Id,
        depth: int = Query(2, ge=1, le=3),
        limit: int = Query(100, ge=1, le=200),
    ):
        return {
            "request_id": request.state.request_id,
            **service.graph(authenticate(request, settings), entity_id, depth, limit),
        }

    @api.get("/api/trace/{trace_request_id}")
    def trace(request: Request, trace_request_id: Id):
        return {
            "request_id": request.state.request_id,
            **service.trace(authenticate(request, settings), trace_request_id),
        }

    @api.get("/api/knowledge/health")
    def health(request: Request):
        return {
            "request_id": request.state.request_id,
            **service.health(authenticate(request, settings)),
        }

    @api.post("/api/chat")
    def chat(request: Request, body: Question):
        return {
            "request_id": request.state.request_id,
            **service.ask(authenticate(request, settings), body.question),
        }

    return api
