import base64
import hmac
import json
import time
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.auth import authenticate
from app.config import Settings
from app.graph.connection import GraphUnavailable
from app.graph.repository import GraphRepository
from app.ingestion.artifacts import ArtifactStore
from app.ingestion.quote_verifier import verify_quote
from app.models.common import Id
from app.models.promises import (
    Freshness,
    GraphPath,
    PromiseCollection,
    PromiseDetail,
    PromiseSummary,
    ReceiptVerifyRequest,
    ReceiptVerifyResponse,
    ScopeAssessment,
    SourceVerification,
    Verification,
    VerificationCheck,
    VerifyResponse,
    VersionSummary,
)
from app.promise_seal.canonicalize import strict_json
from app.promise_seal.crypto import verify_bytes
from app.promise_seal.models import ReceiptEnvelope, ReceiptPayload
from app.promise_seal.registry import configured_registry


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _cursor_secret(settings: Settings) -> bytes:
    if settings.session_secret is None:
        raise HTTPException(503)
    return settings.session_secret.get_secret_value().encode()


def _encode_cursor(settings: Settings, tenant: str, filters: dict, after: str) -> str:
    body = json.dumps(
        {"tenant": tenant, "filters": filters, "after": after, "exp": int(time.time()) + 900},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    sig = hmac.digest(_cursor_secret(settings), body, "sha256")
    return base64.urlsafe_b64encode(body + sig).rstrip(b"=").decode()


def _decode_cursor(settings: Settings, cursor: str, tenant: str, filters: dict) -> str:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        body, sig = raw[:-32], raw[-32:]
        if not hmac.compare_digest(sig, hmac.digest(_cursor_secret(settings), body, "sha256")):
            raise ValueError
        data = json.loads(body)
        if data["tenant"] != tenant or data["filters"] != filters or data["exp"] <= time.time():
            raise ValueError
        if not isinstance(data["after"], str):
            raise ValueError
        return data["after"]
    except ValueError, KeyError, UnicodeDecodeError, json.JSONDecodeError, base64.binascii.Error:
        raise HTTPException(400) from None


def _summary(row: list, now: str) -> PromiseSummary:
    (
        promise_id,
        current_version_id,
        revision,
        state,
        standing,
        customer_id,
        project_id,
        deliverable,
        deadline_iso,
        deadline_text,
        scope_status,
        *_rest,
    ) = row
    return PromiseSummary(
        id=promise_id,
        current_version_id=current_version_id,
        revision=revision,
        current_state=state,
        receipt_standing=standing,
        customer_id=customer_id,
        project_id=project_id,
        deliverable=deliverable,
        deadline=deadline_iso or deadline_text,
        scope_status=scope_status or "UNKNOWN",
        risk_flags=[],
        freshness=Freshness(
            level="UNKNOWN",
            as_of=None,
            evaluated_at=now,
            threshold_seconds=0,
            source_version_ids=[],
        ),
        open_conflict_ids=[],
    )


def router(settings: Settings, repository: GraphRepository) -> APIRouter:
    api = APIRouter()
    registry = configured_registry(settings)
    artifacts = ArtifactStore(settings.source_storage_root)

    @api.get("/api/promises", response_model=PromiseCollection)
    def list_promises(
        request: Request,
        status: Literal[
            "PROPOSED",
            "NEEDS_REVIEW",
            "CONFIRMED",
            "DISPUTED",
            "SUPERSEDED",
            "FULFILLED",
            "REJECTED",
        ]
        | None = None,
        customer_id: Id | None = None,
        deadline_from: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
        deadline_to: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
        risk: str | None = None,
        cursor: str | None = Query(default=None, max_length=2048),
        limit: int = Query(default=25, ge=1, le=100),
    ):
        current = authenticate(request, settings)
        if risk is not None:
            raise HTTPException(400)
        filters = {
            "status": status or "",
            "customer": customer_id or "",
            "from": deadline_from or "",
            "to": deadline_to or "",
        }
        after = _decode_cursor(settings, cursor, current.tenant_id, filters) if cursor else ""
        rows = repository.list_promises(
            current.tenant_id,
            after=after,
            status=filters["status"],
            customer=filters["customer"],
            deadline_from=filters["from"],
            deadline_to=filters["to"],
            limit=limit + 1,
        )
        now = _timestamp()
        items = [_summary(row, now) for row in rows[:limit]]
        next_cursor = (
            _encode_cursor(settings, current.tenant_id, filters, items[-1].id)
            if len(rows) > limit and items
            else None
        )
        return PromiseCollection(
            request_id=request.state.request_id, items=items, next_cursor=next_cursor
        )

    @api.get("/api/promises/{promise_id}", response_model=PromiseDetail)
    def detail(request: Request, promise_id: Id, version_id: Id | None = None):
        current = authenticate(request, settings)
        if version_id is not None:
            # Historical version access needs its own ACL/standing query.
            raise HTTPException(400)
        row = repository.promise_detail(current.tenant_id, promise_id)
        if row is None:
            raise HTTPException(404)
        try:
            payload = ReceiptPayload.model_validate(strict_json(row[11].encode("utf-8")))
            receipt = ReceiptEnvelope(
                payload=payload, payload_sha256=row[12], signature_base64url=row[13]
            )
            if (
                payload.tenant_id != current.tenant_id
                or payload.promise_id != row[0]
                or payload.receipt_id != row[14]
            ):
                raise ValueError("receipt projection mismatch")
        except (ValueError, TypeError) as exc:
            raise GraphUnavailable("stored receipt is invalid") from exc
        for ref in payload.source_refs:
            if ref.access_label != "PUBLIC_DEMO":
                raise HTTPException(404)
            source = repository.source_version(
                current.tenant_id, ref.source_id, ref.source_version_id
            )
            if source is None or source != [ref.source_hash, ref.representation_hash, "AVAILABLE"]:
                raise HTTPException(404)
        versions = [
            VersionSummary(
                receipt_id=item[0],
                version=item[1],
                status_at_issuance=item[2],
                standing=item[3],
            )
            for item in repository.promise_versions(current.tenant_id, promise_id)
        ]
        revision = repository.graph_revision(current.tenant_id)
        return PromiseDetail(
            request_id=request.state.request_id,
            promise=_summary(row, _timestamp()),
            receipt=receipt,
            versions=versions,
            evidence=payload.source_refs,
            scope_assessment=ScopeAssessment(
                status=row[10] or "UNKNOWN",
                claim="Scope has not been assessed.",
                clause_ids=[],
                evidence_refs=[],
                conflict_ids=[],
                missing_evidence=["contract scope assessment"],
                assessment_kind="DETERMINISTIC_RULE",
                reviewed_by=None,
            ),
            calculations=[],
            related_issue_ids=repository.related_issues(current.tenant_id, row[14]),
            milestone_ids=repository.milestones(current.tenant_id, row[14]),
            conflicts=[],
            graph_paths=[
                GraphPath(
                    path_id=f"path-{row[15]}",
                    template_id="PROMISE_CURRENT_VERSION",
                    node_ids=[row[0], row[14]],
                    edge_ids=[row[15]],
                    graph_revision=revision,
                    evidence_ref_ids=[],
                )
            ],
        )

    def evaluate(receipt: ReceiptEnvelope, tenant_id: str, standing: str) -> Verification:
        byte_result = verify_bytes(receipt, registry, tenant_id=tenant_id)
        source_results = []
        for ref in receipt.payload.source_refs:
            try:
                raw = artifacts.read(tenant_id, ref.source_hash, "raw")
                representation = artifacts.read(
                    tenant_id, ref.representation_hash, "representation"
                ).decode("utf-8", errors="strict")
                matching = verify_quote(raw, representation, ref)
                source_results.append(
                    SourceVerification(
                        evidence_ref_id=ref.evidence_ref_id,
                        result="MATCH" if matching else "MISMATCH",
                        reason="Exact retained bytes and quote match."
                        if matching
                        else "Retained bytes or exact quote do not match.",
                    )
                )
            except FileNotFoundError:
                source_results.append(
                    SourceVerification(
                        evidence_ref_id=ref.evidence_ref_id,
                        result="UNAVAILABLE",
                        reason="Retained source artifact is unavailable.",
                    )
                )
            except ValueError, UnicodeDecodeError:
                source_results.append(
                    SourceVerification(
                        evidence_ref_id=ref.evidence_ref_id,
                        result="MISMATCH",
                        reason="Retained source artifact failed validation.",
                    )
                )
        source_check = (
            "FAIL"
            if any(item.result == "MISMATCH" for item in source_results)
            else "UNAVAILABLE"
            if any(item.result == "UNAVAILABLE" for item in source_results)
            else "PASS"
        )
        checks = [
            VerificationCheck(
                code="PAYLOAD_AND_SIGNATURE",
                result="PASS" if byte_result.integrity == "VALID" else "FAIL",
                reason=None
                if byte_result.integrity == "VALID"
                else ",".join(byte_result.failures) or byte_result.integrity,
            ),
            VerificationCheck(
                code="RETAINED_SOURCE_BYTES",
                result=source_check,
                reason=None if source_check == "PASS" else "Source evidence is not fully verified.",
            ),
            VerificationCheck(
                code="AUDIT_CHAIN",
                result="UNAVAILABLE",
                reason="Graph audit-chain verification is not implemented.",
            ),
        ]
        return Verification(
            integrity=byte_result.integrity,
            standing=standing,
            checked_at=_timestamp(),
            checks=checks,
            source_results=source_results,
            key_trust=byte_result.key_trust,
            eligible_for_action=False,
        )

    @api.get("/api/promises/{promise_id}/verify", response_model=VerifyResponse)
    def verify(request: Request, promise_id: Id, version_id: Id | None = None):
        detail_result = detail(request, promise_id, version_id)
        current = authenticate(request, settings)
        return VerifyResponse(
            request_id=request.state.request_id,
            receipt_id=detail_result.receipt.payload.receipt_id,
            verification=evaluate(
                detail_result.receipt,
                current.tenant_id,
                detail_result.promise.receipt_standing,
            ),
        )

    @api.post("/api/receipts/verify", response_model=ReceiptVerifyResponse)
    def verify_copy(request: Request, body: ReceiptVerifyRequest):
        actor = authenticate(request, settings)
        receipt = body.receipt
        if receipt.payload.tenant_id != actor.tenant_id:
            raise HTTPException(404)
        if len(receipt.model_dump_json().encode("utf-8")) > 1024 * 1024:
            raise HTTPException(413)
        stored = detail(request, receipt.payload.promise_id)
        if stored.receipt.payload.receipt_id != receipt.payload.receipt_id:
            raise HTTPException(404)
        if [ref.evidence_ref_id for ref in stored.receipt.payload.source_refs] != [
            ref.evidence_ref_id for ref in receipt.payload.source_refs
        ]:
            raise HTTPException(404)
        return ReceiptVerifyResponse(
            request_id=request.state.request_id,
            verification=evaluate(receipt, actor.tenant_id, stored.promise.receipt_standing),
        )

    return api
