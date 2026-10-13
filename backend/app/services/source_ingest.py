"""Idempotent source-version publication under a graph revision compare-and-set."""

import hashlib
import hmac
import json
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from redis.exceptions import RedisError

from app.auth import Actor
from app.config import Settings
from app.graph.connection import GraphConnection, GraphUnavailable
from app.graph.queries import sources
from app.ingestion.artifacts import ArtifactStore
from app.ingestion.candidates import PROFILE, extract_candidates
from app.ingestion.chunks import chunk_text
from app.ingestion.quote_verifier import parse_text
from app.promise_seal.canonicalize import canonical_bytes
from app.promise_seal.crypto import load_private_key
from app.promise_seal.registry import configured_registry
from app.services.audit import sign_audit
from app.services.proposals import build_proposal


class SourceConflict(Exception):
    pass


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _id(prefix: str, *parts: str) -> str:
    return prefix + hashlib.sha256("\x00".join(parts).encode()).hexdigest()[:32]


class SourceIngestService:
    def __init__(self, settings: Settings, connection: GraphConnection):
        self.settings = settings
        self.connection = connection
        self.artifacts = ArtifactStore(settings.source_storage_root)
        self._lock = Lock()

    def _signing_key(self, tenant_id: str):
        settings = self.settings
        if not all(
            (settings.signing_private_key_path, settings.signing_key_id, settings.signing_issuer_id)
        ):
            raise GraphUnavailable("source publication signing is not configured")
        try:
            key = load_private_key(settings.signing_private_key_path)
        except (OSError, ValueError) as exc:
            raise GraphUnavailable("source publication signing key is unavailable") from exc
        trusted = configured_registry(settings).get(
            (tenant_id, settings.signing_issuer_id, settings.signing_key_id)
        )
        if (
            trusted is None
            or trusted.trust != "TRUSTED"
            or not hmac.compare_digest(
                key.public_key().public_bytes_raw(), trusted.public_key.public_bytes_raw()
            )
        ):
            raise GraphUnavailable("source publication signing key is not trusted")
        return key

    def ingest(
        self,
        actor: Actor,
        *,
        raw: bytes,
        source_type: str,
        title: str,
        source_key: str | None,
        access_label: str,
        content_type: str,
        idempotency_key: str,
        request_id: str,
    ) -> tuple[int, dict]:
        tenant = actor.tenant_id
        private_key = self._signing_key(tenant)
        trusted_key = configured_registry(self.settings)[
            (tenant, self.settings.signing_issuer_id, self.settings.signing_key_id)
        ]
        chunks = chunk_text(parse_text(raw))
        candidates = extract_candidates(parse_text(raw), chunks)
        stored = self.artifacts.save_text(tenant, raw)
        identity = source_key or stored.raw_hash
        source_id = _id("source-", tenant, source_type, identity)
        operation_id = _id(
            "operation-", tenant, actor.id, "POST", "/api/sources/upload", idempotency_key
        )
        input_digest = hashlib.sha256(
            canonical_bytes(
                {
                    "source_type": source_type,
                    "source_key": source_key,
                    "title": title,
                    "access_label": access_label,
                    "content_type": content_type,
                    "raw_hash": stored.raw_hash,
                }
            )
        ).hexdigest()
        with self._lock:
            graph = self.connection.graph_for_tenant(tenant)
            try:

                def replay():
                    previous = graph.ro_query(
                        sources.LEDGER,
                        {"operation": operation_id, "tenant": tenant},
                        timeout=self.settings.falkordb_query_timeout_ms,
                    ).result_set
                    if not previous:
                        return None
                    if previous[0][0] != input_digest:
                        raise SourceConflict("idempotency key reused with different upload")
                    repeated = json.loads(previous[0][1])
                    repeated["request_id"] = request_id
                    return 202, repeated

                repeated = replay()
                if repeated is not None:
                    return repeated
                state = graph.ro_query(
                    sources.STATE,
                    {"tenant": tenant, "source": source_id},
                    timeout=self.settings.falkordb_query_timeout_ms,
                ).result_set
                if not state:
                    raise GraphUnavailable("tenant graph state is unavailable")
                (
                    revision,
                    sequence,
                    prev_hash,
                    prior_version,
                    prior_hash,
                    prior_number,
                    ontology_version,
                    policy_version,
                    prior_access_label,
                    accessible_version,
                ) = state[0]
                repeated = replay()
                if repeated is not None:
                    return repeated
                if prior_version is not None and accessible_version != prior_version:
                    raise SourceConflict("source current-version traversal is invalid")
                if ontology_version != "v1" or policy_version != "v1":
                    raise GraphUnavailable("unsupported graph ontology or policy version")
                if prior_access_label is not None and prior_access_label != access_label:
                    raise SourceConflict("source access label cannot change on upload")
                if prior_hash == stored.raw_hash:
                    return 200, {
                        "request_id": request_id,
                        "source_id": source_id,
                        "source_version_id": prior_version,
                        "outcome": "NO_CHANGE",
                    }
                version_number = (prior_number or 0) + 1
                version_id = f"{source_id}-v{version_number}"
                now = _now()
                audit_id = "audit-" + uuid4().hex
                candidate_ids = [
                    _id("promise-", tenant, source_id, PROFILE, item.assertion_key)
                    for item in candidates
                ]
                existing = (
                    graph.ro_query(
                        sources.EXISTING_PROMISES,
                        {"tenant": tenant, "ids": candidate_ids},
                        timeout=self.settings.falkordb_query_timeout_ms,
                    ).result_set
                    if candidates
                    else []
                )
                existing_ids = {row[0] for row in existing}
                proposals = []
                if candidates:
                    retained_raw = self.artifacts.read(tenant, stored.raw_hash, "raw")
                    retained_text = self.artifacts.read(
                        tenant, stored.representation_hash, "representation"
                    ).decode("utf-8", errors="strict")
                for candidate, promise_id in zip(candidates, candidate_ids, strict=True):
                    if promise_id in existing_ids:
                        continue
                    receipt_id = promise_id + "-v1"
                    receipt = build_proposal(
                        candidate,
                        tenant=tenant,
                        source=source_id,
                        version=version_id,
                        promise_id=promise_id,
                        receipt_id=receipt_id,
                        evidence_id=_id(
                            "evidence-", tenant, version_id, str(candidate.start_offset)
                        ),
                        access_label=access_label,
                        raw=retained_raw,
                        representation=retained_text,
                        raw_hash=stored.raw_hash,
                        representation_hash=stored.representation_hash,
                        now=now,
                        private_key=private_key,
                        trusted_key=trusted_key,
                    )
                    proposals.append(
                        {
                            "promise_id": promise_id,
                            "receipt_id": receipt_id,
                            "chunk_start": candidate.chunk_start,
                            "start_offset": candidate.start_offset,
                            "end_offset": candidate.end_offset,
                            "payload_json": canonical_bytes(receipt.payload.model_dump()).decode(),
                            "payload_hash": receipt.payload_sha256,
                            "signature": receipt.signature_base64url,
                            "statement": candidate.exact_excerpt,
                            "deliverable": candidate.deliverable,
                            "provenance": canonical_bytes(
                                [receipt.payload.source_refs[0].model_dump()]
                            ).decode(),
                            "version_edge": _id("edge-", tenant, promise_id, receipt_id),
                            "proposes_edge": _id("edge-proposes-", tenant, version_id, receipt_id),
                            "support_edge": _id("edge-support-", tenant, version_id, receipt_id),
                            "event_edge": _id("edge-event-", tenant, receipt_id, audit_id),
                        }
                    )
                audit_payload = {
                    "protocol_version": "promiseops-audit-v1",
                    "event_id": audit_id,
                    "tenant_id": tenant,
                    "sequence": sequence + 1,
                    "event_type": "SOURCE_UPDATED" if prior_version else "SOURCE_IMPORTED",
                    "actor_id": actor.id,
                    "occurred_at": now,
                    "request_id": request_id,
                    "payload": {
                        "source_id": source_id,
                        "source_version_id": version_id,
                        "content_hash": stored.raw_hash,
                        "extraction_profile": PROFILE,
                        "receipts": [
                            {
                                "receipt_id": item["receipt_id"],
                                "payload_sha256": item["payload_hash"],
                            }
                            for item in proposals
                        ],
                    },
                    "prev_event_hash": prev_hash,
                    "signing_key_id": self.settings.signing_key_id,
                }
                try:
                    audit = sign_audit(audit_payload, self.settings.signing_private_key_path)
                except (OSError, ValueError) as exc:
                    raise GraphUnavailable("source publication signing key is unavailable") from exc
                result = {
                    "request_id": request_id,
                    "operation_id": operation_id,
                    "source_id": source_id,
                    "status_url": f"/api/operations/{operation_id}",
                }
                params = {
                    "tenant": tenant,
                    "source": source_id,
                    "source_type": source_type,
                    "external_id": identity,
                    "title": title,
                    "access_label": access_label,
                    "content_type": content_type,
                    "raw_hash": stored.raw_hash,
                    "representation_hash": stored.representation_hash,
                    "version": version_id,
                    "version_number": version_number,
                    "source_edge": _id("edge-", tenant, source_id, version_id),
                    "operation": operation_id,
                    "actor": actor.id,
                    "request_id": request_id,
                    "input_digest": input_digest,
                    "result_json": canonical_bytes(result).decode(),
                    "audit_id": audit_id,
                    "audit_payload": audit.payload_json,
                    "audit_hash": audit.event_hash,
                    "audit_signature": audit.signature,
                    "audit_edge": _id("edge-", tenant, source_id, audit_id),
                    "key_id": self.settings.signing_key_id,
                    "now": now,
                    "expected_revision": revision,
                    "expected_sequence": sequence,
                    "sequence": sequence + 1,
                    "prev_hash": prev_hash,
                    "previous_version": prior_version,
                    "previous_hash": prior_hash,
                    "proposals": proposals,
                    "chunks": [
                        {
                            "id": _id("chunk-", tenant, version_id, str(chunk.start)),
                            "edge_id": _id("edge-", tenant, version_id, str(chunk.start)),
                            "start": chunk.start,
                            "end": chunk.end,
                            "text": chunk.text,
                            "hash": chunk.digest,
                        }
                        for chunk in chunks
                    ],
                }
                query = sources.UPDATE_SOURCE if prior_version else sources.CREATE_SOURCE
                published = graph.query(
                    query, params=params, timeout=self.settings.falkordb_query_timeout_ms
                ).result_set
                if not published:
                    repeated = replay()
                    if repeated is not None:
                        return repeated
                    raise SourceConflict("graph state changed during source publication")
                return 202, result
            except (RedisError, OSError) as exc:
                raise GraphUnavailable("source publication failed") from exc
