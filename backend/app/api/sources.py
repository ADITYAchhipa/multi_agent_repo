"""Bounded local text upload and source/version read-back."""

import hashlib
import json
import re
from pathlib import PurePath
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.auth import authenticate, require_role
from app.config import Settings
from app.graph.repository import GraphRepository
from app.ingestion.candidates import CandidateLimitExceeded
from app.ingestion.chunks import ChunkLimitExceeded
from app.ingestion.quote_verifier import verify_quote
from app.models.api import EvidenceRef
from app.models.common import Id
from app.models.sources import (
    Operation,
    OperationProgress,
    OperationResponse,
    SourceDetail,
    SourceSummary,
    SourceVersionResponse,
    SourceVersionSummary,
    UploadAccepted,
    UploadNoChange,
)
from app.services.source_ingest import SourceIngestService

MAX_SOURCE_BYTES = 20 * 1024 * 1024


def router(
    settings: Settings, repository: GraphRepository, service: SourceIngestService
) -> APIRouter:
    api = APIRouter()

    @api.post("/api/sources/upload", response_model=UploadAccepted | UploadNoChange)
    def upload(
        request: Request,
        file: Annotated[UploadFile, File()],
        source_type: Annotated[Literal["TRANSCRIPT", "NOTES", "CONTRACT"], Form()],
        access_label: Annotated[Literal["PUBLIC_DEMO", "INTERNAL", "RESTRICTED"], Form()],
        idempotency_key: Annotated[
            str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
        ],
        source_key: Annotated[str | None, Form(max_length=128)] = None,
        meeting_context: Annotated[str | None, Form(max_length=4096)] = None,
    ):
        actor = authenticate(request, settings)
        require_role(actor, "admin")
        if meeting_context is not None:
            raise HTTPException(422)
        if source_key is not None and not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", source_key):
            raise HTTPException(422)
        filename = file.filename or ""
        if (
            not filename
            or len(filename) > 128
            or filename in {".", ".."}
            or filename != PurePath(filename).name
            or "\\" in filename
            or not filename.lower().endswith((".txt", ".md"))
        ):
            raise HTTPException(415)
        if file.content_type not in {"text/plain", "text/markdown"}:
            raise HTTPException(415)
        if (
            request.headers.get("content-length", "").isdigit()
            and int(request.headers["content-length"]) > MAX_SOURCE_BYTES + 8192
        ):
            raise HTTPException(413)
        raw = file.file.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            raise HTTPException(413)
        try:
            raw.decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError:
            raise HTTPException(422) from None
        try:
            status, result = service.ingest(
                actor,
                raw=raw,
                source_type=source_type,
                title=filename,
                source_key=source_key,
                access_label=access_label,
                content_type=file.content_type,
                idempotency_key=idempotency_key,
                request_id=request.state.request_id,
            )
        except ChunkLimitExceeded, CandidateLimitExceeded:
            raise HTTPException(422) from None
        model = UploadAccepted if status == 202 else UploadNoChange
        return JSONResponse(model.model_validate(result).model_dump(), status_code=status)

    @api.get("/api/sources/{source_id}", response_model=SourceDetail)
    def source(
        request: Request,
        source_id: Id,
        version_id: Id | None = None,
        chunk_id: Id | None = None,
    ):
        actor = authenticate(request, settings)
        rows = repository.source_detail(actor.tenant_id, source_id, "admin" in actor.roles)
        if not rows:
            raise HTTPException(404)
        first = rows[0]
        selected = next((row for row in rows if row[9] == (version_id or first[3])), None)
        if selected is None:
            raise HTTPException(404)
        chunks = repository.source_chunks(
            actor.tenant_id, source_id, selected[9], chunk_id, "admin" in actor.roles
        )
        if chunk_id is not None and not chunks:
            raise HTTPException(404)
        raw = representation = None
        artifact_status = "UNAVAILABLE"
        if chunks and selected[13] == "AVAILABLE":
            try:
                raw = service.artifacts.read(actor.tenant_id, selected[11], "raw")
                representation = service.artifacts.read(
                    actor.tenant_id, selected[12], "representation"
                ).decode("utf-8", errors="strict")
                artifact_status = "VERIFIED"
            except FileNotFoundError:
                pass
            except ValueError, UnicodeDecodeError:
                artifact_status = "REJECTED"
        snippets = []
        for chunk in chunks:
            evidence = EvidenceRef(
                evidence_ref_id=chunk[0],
                source_id=source_id,
                source_version_id=selected[9],
                source_hash=selected[11],
                representation_hash=selected[12],
                origin_reference=f"source:{source_id}",
                quote=chunk[1],
                start_offset=chunk[2],
                end_offset=chunk[3],
                start_ms=None,
                end_ms=None,
                structured_pointer=None,
                source_updated_at=selected[14],
                observed_at=chunk[6],
                verification=artifact_status,
                access_label=chunk[5],
            )
            if artifact_status == "VERIFIED" and (
                not verify_quote(raw, representation, evidence)
                or hashlib.sha256(chunk[1].encode()).hexdigest() != chunk[4]
            ):
                evidence = evidence.model_copy(update={"verification": "REJECTED"})
            snippets.append(evidence)
        summary = SourceSummary(
            id=first[0],
            source_type=first[1],
            title=first[2],
            current_version_id=first[3],
            source_updated_at=first[4],
            ingested_at=first[5],
            content_hash=first[6],
            retention_state=first[7],
            parse_status=first[8],
            mode="IMPORT",
        )
        return SourceDetail(
            request_id=request.state.request_id,
            source=summary,
            version=SourceVersionResponse(
                id=selected[9],
                source_hash=selected[11],
                representation_hash=selected[12],
                availability=selected[13],
            ),
            snippets=snippets,
            versions=[
                SourceVersionSummary(
                    id=row[9],
                    version=row[10],
                    source_updated_at=row[14],
                    availability=row[13],
                )
                for row in rows
            ],
        )

    @api.get("/api/operations/{operation_id}", response_model=OperationResponse)
    def operation(request: Request, operation_id: Id):
        actor = authenticate(request, settings)
        row = repository.operation(actor.tenant_id, actor.id, operation_id, "admin" in actor.roles)
        if row is None:
            raise HTTPException(404)
        return OperationResponse(
            request_id=request.state.request_id,
            operation=Operation(
                id=row[0],
                kind=row[1],
                status=row[2],
                phase=row[3],
                created_at=row[4],
                started_at=row[5],
                finished_at=row[6],
                result=json.loads(row[7]) if row[7] else None,
                errors=json.loads(row[8]),
                progress=OperationProgress(completed=1, total=1),
            ),
        )

    return api
