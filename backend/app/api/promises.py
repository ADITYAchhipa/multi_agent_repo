import base64
import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query, Request
from redis.exceptions import RedisError

from app.auth import authenticate, require_role
from app.config import Settings
from app.graph.connection import GraphUnavailable
from app.graph.queries import promises
from app.graph.repository import GraphRepository
from app.ingestion.artifacts import ArtifactStore
from app.ingestion.quote_verifier import verify_quote
from app.models.api import EvidenceRef
from app.models.common import Id
from app.models.promises import (
    Freshness,
    GraphPath,
    PromiseCollection,
    PromiseDetail,
    PromiseSummary,
    ReceiptVerifyRequest,
    ReceiptVerifyResponse,
    ReviewRequest,
    ReviewResponse,
    ScopeAssessment,
    VerifyResponse,
    VersionSummary,
)
from app.promise_seal.canonicalize import canonical_bytes, digest, strict_json
from app.promise_seal.crypto import load_private_key, sign
from app.promise_seal.lifecycle import check_parent, next_state
from app.promise_seal.models import ReceiptEnvelope, ReceiptPayload
from app.promise_seal.registry import configured_registry
from app.services.audit import sign_audit
from app.services.verification import evaluate_receipt


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
        row = repository.promise_detail(current.tenant_id, promise_id, version_id)
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
            promise=_summary(row, _timestamp()).model_copy(
                update={
                    "customer_id": payload.customer_id,
                    "project_id": payload.project_id,
                    "deliverable": payload.deliverable,
                    "deadline": payload.deadline.instant
                    or payload.deadline.local_date
                    or payload.deadline.original_text,
                }
            ),
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

    def evaluate(receipt: ReceiptEnvelope, tenant_id: str, standing: str):
        return evaluate_receipt(settings, repository, receipt, tenant_id, standing)

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

    @api.post("/api/promises/{promise_id}/review", response_model=ReviewResponse)
    def review(
        request: Request,
        promise_id: Id,
        body: ReviewRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ):
        actor = authenticate(request, settings)
        require_role(actor, "reviewer")
        input_digest = hashlib.sha256(
            canonical_bytes({"promise_id": promise_id, "body": body.model_dump(mode="json")})
        ).hexdigest()
        operation_id = (
            "review-"
            + hashlib.sha256(
                f"{actor.tenant_id}\0{actor.id}\0{promise_id}\0{idempotency_key}".encode()
            ).hexdigest()[:40]
        )

        def replay():
            previous = repository.review_ledger(actor.tenant_id, actor.id, operation_id)
            if previous is None:
                return None
            if previous[0] != input_digest:
                raise HTTPException(409)
            result = ReviewResponse.model_validate(strict_json(previous[1].encode()))
            accessible = detail(request, promise_id, result.receipt.payload.receipt_id)
            if accessible.receipt != result.receipt:
                raise HTTPException(409)
            return result.model_copy(update={"request_id": request.state.request_id})

        previous = replay()
        if previous is not None:
            return previous
        current_state = repository.review_state(actor.tenant_id, promise_id)
        if current_state is None:
            raise HTTPException(404)
        graph_revision, sequence, prev_hash = current_state[:3]
        current_detail = detail(request, promise_id)
        if (
            current_detail.promise.current_version_id != body.expected_version_id
            or current_detail.promise.revision != body.expected_revision
        ):
            previous = replay()
            if previous is not None:
                return previous
            raise HTTPException(409)
        parent = current_detail.receipt
        parent_refs = {ref.evidence_ref_id: ref for ref in parent.payload.source_refs}
        if body.decision in {"CONFIRM", "FULFILL", "DISPUTE"} and not body.evidence_ref_ids:
            raise HTTPException(422)
        if body.decision == "CONFIRM" and not set(parent_refs).issubset(body.evidence_ref_ids):
            raise HTTPException(409)
        new_refs = []
        for evidence_id in body.evidence_ref_ids:
            if evidence_id in parent_refs:
                continue
            row = repository.review_evidence(actor.tenant_id, evidence_id)
            if row is None:
                raise HTTPException(422)
            try:
                raw = artifacts.read(actor.tenant_id, row[2], "raw")
                representation = artifacts.read(actor.tenant_id, row[3], "representation").decode(
                    "utf-8", errors="strict"
                )
                evidence = EvidenceRef(
                    evidence_ref_id=evidence_id,
                    source_id=row[0],
                    source_version_id=row[1],
                    source_hash=row[2],
                    representation_hash=row[3],
                    origin_reference=f"source:{row[0]}",
                    quote=row[4],
                    start_offset=row[5],
                    end_offset=row[6],
                    start_ms=None,
                    end_ms=None,
                    structured_pointer=None,
                    source_updated_at=row[9],
                    observed_at=row[8],
                    verification="VERIFIED",
                    access_label="PUBLIC_DEMO",
                )
                if (
                    not verify_quote(raw, representation, evidence)
                    or hashlib.sha256(row[4].encode()).hexdigest() != row[7]
                ):
                    raise ValueError("review evidence mismatch")
                new_refs.append(evidence)
            except OSError, ValueError, UnicodeDecodeError:
                raise HTTPException(409) from None
        if body.decision == "FULFILL":
            if parent.payload.confirmation is None or not new_refs:
                raise HTTPException(409)
        if body.decision == "CONFIRM" and current_detail.promise.current_state == "DISPUTED":
            # Conflict resolution is a separate, currently unsupported workflow.
            raise HTTPException(409)
        evidence_check = evaluate(parent, actor.tenant_id, current_detail.promise.receipt_standing)
        if evidence_check.integrity != "VALID" or any(
            check.result != "PASS" for check in evidence_check.checks
        ):
            previous = replay()
            if previous is not None:
                return previous
            raise HTTPException(409)
        try:
            state = next_state(current_detail.promise.current_state, body.decision)
        except ValueError:
            raise HTTPException(409) from None
        now = _timestamp()
        event_id = "audit-" + uuid4().hex
        values = parent.payload.model_dump(mode="json")
        values["source_refs"] = [
            item.model_dump(mode="json")
            for item in sorted(
                [*parent.payload.source_refs, *new_refs],
                key=lambda ref: (
                    ref.source_version_id,
                    ref.start_offset if ref.start_offset is not None else -1,
                    ref.end_offset if ref.end_offset is not None else -1,
                    ref.evidence_ref_id,
                ),
            )
        ]
        content_fields = {
            "statement",
            "deliverable",
            "customer_id",
            "project_id",
            "deadline",
            "price_condition",
            "commercial_value",
            "commitment_class",
        }
        if body.decision == "REVISE":
            if not content_fields.issuperset(body.revised_content):
                raise HTTPException(422)
            values.update(body.revised_content)
        values.update(
            {
                "receipt_id": f"{promise_id}-v{parent.payload.version + 1}",
                "version": parent.payload.version + 1,
                "created_at": now,
                "issued_at": now,
                "status_at_issuance": state,
                "review_event_id": event_id,
                "previous_receipt_version_id": parent.payload.receipt_id,
                "previous_payload_sha256": parent.payload_sha256,
                "confirmation": None,
                "signing_key_id": settings.signing_key_id,
            }
        )
        if state == "CONFIRMED":
            # Bind confirmation to the reviewed content, not the mutable status fields.
            values["confirmation"] = {
                "confirmed_by": actor.id,
                "confirmed_at": now,
                "confirmation_event_id": event_id,
                "authority_scope": "configured reviewer role for tenant",
                "reviewed_content_hash": digest(
                    {
                        key: values[key]
                        for key in (
                            "promise_id",
                            "tenant_id",
                            "statement",
                            "deliverable",
                            "customer_id",
                            "project_id",
                            "deadline",
                            "price_condition",
                            "commercial_value",
                            "commitment_class",
                            "source_refs",
                            "contract_refs",
                            "jira_refs",
                            "workload_refs",
                        )
                    }
                ),
            }
        elif state == "FULFILLED":
            values["confirmation"] = {
                "confirmed_by": actor.id,
                "confirmed_at": now,
                "confirmation_event_id": event_id,
                "authority_scope": "configured reviewer role for tenant",
                "reviewed_content_hash": digest(
                    {
                        key: values[key]
                        for key in (
                            "promise_id",
                            "tenant_id",
                            "statement",
                            "deliverable",
                            "customer_id",
                            "project_id",
                            "deadline",
                            "price_condition",
                            "commercial_value",
                            "commitment_class",
                            "source_refs",
                            "contract_refs",
                            "jira_refs",
                            "workload_refs",
                        )
                    }
                ),
            }
        if settings.signing_private_key_path is None or settings.signing_key_id is None:
            raise GraphUnavailable("review signing is not configured")
        try:
            payload = ReceiptPayload.model_validate(values)
            trusted = registry.get((actor.tenant_id, payload.issuer_id, settings.signing_key_id))
            if trusted is None:
                raise ValueError("review signing key is not trusted")
            receipt = sign(payload, load_private_key(settings.signing_private_key_path), trusted)
            check_parent(receipt, parent)
        except ValueError, OSError, KeyError, TypeError:
            raise HTTPException(422) from None
        graph = repository.connection.graph_for_tenant(actor.tenant_id)
        response_promise = current_detail.promise.model_copy(
            update={
                "current_version_id": payload.receipt_id,
                "revision": body.expected_revision + 1,
                "current_state": state,
                "receipt_standing": "ACTIVE",
                "customer_id": payload.customer_id,
                "project_id": payload.project_id,
                "deliverable": payload.deliverable,
                "deadline": payload.deadline.instant
                or payload.deadline.local_date
                or payload.deadline.original_text,
            }
        )
        response = ReviewResponse(
            request_id=request.state.request_id,
            promise=response_promise,
            receipt=receipt,
            audit_event_id=event_id,
        )
        audit_payload = {
            "protocol_version": "promiseops-audit-v1",
            "event_id": event_id,
            "tenant_id": actor.tenant_id,
            "sequence": sequence + 1,
            "event_type": "PROMISE_REVIEW",
            "actor_id": actor.id,
            "occurred_at": now,
            "request_id": request.state.request_id,
            "payload": {
                "promise_id": promise_id,
                "receipt_id": payload.receipt_id,
                "payload_sha256": receipt.payload_sha256,
                "decision": body.decision,
                "reason": body.reason,
                "evidence_ref_ids": body.evidence_ref_ids,
            },
            "prev_event_hash": prev_hash,
            "signing_key_id": settings.signing_key_id,
        }
        try:
            audit = sign_audit(audit_payload, settings.signing_private_key_path)
        except (OSError, ValueError) as exc:
            raise GraphUnavailable("review signing key is unavailable") from exc
        params = {
            "tenant": actor.tenant_id,
            "promise": promise_id,
            "expected_version": body.expected_version_id,
            "expected_revision": body.expected_revision,
            "expected_graph_revision": graph_revision,
            "expected_sequence": sequence,
            "receipt_id": payload.receipt_id,
            "version": payload.version,
            "now": now,
            "payload_json": canonical_bytes(payload.model_dump(mode="json")).decode(),
            "payload_hash": receipt.payload_sha256,
            "signature": receipt.signature_base64url,
            "statement": payload.statement.exact_excerpt,
            "deliverable": payload.deliverable,
            "customer_id": payload.customer_id,
            "project_id": payload.project_id,
            "deadline_iso": payload.deadline.instant or payload.deadline.local_date,
            "deadline_text": payload.deadline.original_text,
            "commitment_class": payload.commitment_class,
            "new_state": state,
            "price_condition": payload.price_condition.kind,
            "version_edge": f"edge-{uuid4().hex}",
            "supersedes_edge": f"edge-{uuid4().hex}",
            "event_edge": f"edge-{uuid4().hex}",
            "provenance": canonical_bytes(
                [
                    {
                        "review_event_id": event_id,
                        "actor_id": actor.id,
                        "evidence_ref_ids": body.evidence_ref_ids,
                    }
                ]
            ).decode(),
            "access_label": "PUBLIC_DEMO",
            "actor": actor.id,
            "audit_id": event_id,
            "sequence": sequence + 1,
            "prev_hash": prev_hash,
            "audit_payload": audit.payload_json,
            "audit_hash": audit.event_hash,
            "audit_signature": audit.signature,
            "key_id": settings.signing_key_id,
            "request_id": request.state.request_id,
            "operation": operation_id,
            "input_digest": input_digest,
            "input_json": canonical_bytes(
                {"promise_id": promise_id, "body": body.model_dump(mode="json")}
            ).decode(),
            "result_json": canonical_bytes(response.model_dump(mode="json")).decode(),
            "operation_event_edge": f"edge-{uuid4().hex}",
        }
        try:
            rows = graph.query(
                promises.PUBLISH_REVIEW, params=params, timeout=settings.falkordb_query_timeout_ms
            ).result_set
        except RedisError as exc:
            raise GraphUnavailable("review publication failed") from exc
        if not rows:
            previous = replay()
            if previous is not None:
                return previous
            raise HTTPException(409)
        return response

    @api.post("/api/receipts/verify", response_model=ReceiptVerifyResponse)
    def verify_copy(request: Request, body: ReceiptVerifyRequest):
        actor = authenticate(request, settings)
        receipt = body.receipt
        if receipt.payload.tenant_id != actor.tenant_id:
            raise HTTPException(404)
        if len(receipt.model_dump_json().encode("utf-8")) > 1024 * 1024:
            raise HTTPException(413)
        stored = detail(request, receipt.payload.promise_id, receipt.payload.receipt_id)
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
