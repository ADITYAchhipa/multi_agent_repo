"""Tenant-bound connector import. Registry is configuration, never user input."""

import hashlib
import json
from typing import Annotated, Literal

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.auth import authenticate, require_role
from app.connectors import Connection
from app.connectors.http import ConnectorError
from app.connectors.teams import TeamsClient
from app.ingestion.candidates import CandidateLimitExceeded
from app.ingestion.chunks import ChunkLimitExceeded


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    organizer_id: str | None = Field(default=None, min_length=1, max_length=512)
    meeting_id: str | None = Field(default=None, min_length=1, max_length=2048)
    transcript_id: str | None = Field(default=None, min_length=1, max_length=2048)
    jql: str | None = Field(default=None, min_length=1, max_length=4000)
    access_label: Literal["PUBLIC_DEMO", "INTERNAL", "RESTRICTED"] = "RESTRICTED"


def router(settings, service, registry: dict[tuple[str, str], Connection]) -> APIRouter:
    api = APIRouter()

    def connection(request, connector_id):
        actor = authenticate(request, settings)
        require_role(actor, "admin")
        configured = registry.get((actor.tenant_id, connector_id))
        if configured is None:
            raise HTTPException(404)
        return actor, configured

    @api.get("/api/connectors")
    def listing(request: Request):
        actor = authenticate(request, settings)
        require_role(actor, "admin")
        return {
            "request_id": request.state.request_id,
            "items": [
                {
                    "id": key,
                    "type": "TEAMS" if isinstance(value.client, TeamsClient) else "JIRA",
                    "mode": "LIVE",
                    "status": "CONFIGURED",
                }
                for (tenant, key), value in registry.items()
                if tenant == actor.tenant_id
            ],
        }

    @api.get("/api/connectors/{connector_id}/health")
    def health(request: Request, connector_id: str):
        _, configured = connection(request, connector_id)
        try:
            if isinstance(configured.client, TeamsClient):
                if not configured.organizer_id or not configured.meeting_id:
                    raise HTTPException(409, "Teams health probe requires a configured meeting")
                configured.client.transcripts(configured.organizer_id, configured.meeting_id)
            else:
                configured.client.health()
        except ConnectorError:
            raise HTTPException(502) from None
        return {
            "request_id": request.state.request_id,
            "connector_id": connector_id,
            "status": "AVAILABLE",
            "mode": "LIVE",
        }

    @api.post("/api/connectors/{connector_id}/import")
    def importing(
        request: Request,
        connector_id: str,
        body: ImportRequest,
        idempotency_key: Annotated[
            str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
        ],
    ):
        actor, configured = connection(request, connector_id)
        try:
            if isinstance(configured.client, TeamsClient):
                if not all((body.organizer_id, body.meeting_id, body.transcript_id)) or body.jql:
                    raise HTTPException(422)
                raw = configured.client.transcript(
                    body.organizer_id, body.meeting_id, body.transcript_id
                )
                identity = [connector_id, body.organizer_id, body.meeting_id, body.transcript_id]
                source_type = "TRANSCRIPT"
                title = "teams-transcript.txt"
                prefix = "Microsoft Teams transcript reference: " + json.dumps(identity) + "\n"
                raw = prefix.encode() + raw
            else:
                if not body.jql or any((body.organizer_id, body.meeting_id, body.transcript_id)):
                    raise HTTPException(422)
                issues = configured.client.search(body.jql)
                identity = [connector_id, body.jql]
                source_type = "NOTES"
                title = "jira-issues.txt"
                raw = json.dumps(
                    {"connector_id": connector_id, "jql": body.jql, "issues": issues},
                    sort_keys=True,
                    indent=2,
                ).encode()
            if len(raw) > 20 * 1024 * 1024:
                raise HTTPException(413)
            source_key = "connector:" + hashlib.sha256(json.dumps(identity).encode()).hexdigest()
            status, result = service.ingest(
                actor,
                raw=raw,
                source_type=source_type,
                title=title,
                source_key=source_key,
                access_label=body.access_label,
                content_type="text/plain",
                idempotency_key=idempotency_key,
                request_id=request.state.request_id,
            )
        except ConnectorError:
            raise HTTPException(502) from None
        except ChunkLimitExceeded, CandidateLimitExceeded:
            raise HTTPException(422) from None
        return JSONResponse(result, status_code=status)

    return api
