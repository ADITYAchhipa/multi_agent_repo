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
from app.promise_seal.canonicalize import canonical_bytes
from app.promise_seal.crypto import load_private_key
from app.promise_seal.registry import configured_registry
from app.services.audit import sign_audit


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
        self._signing_key(tenant)
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
                previous = graph.ro_query(
                    sources.LEDGER,
                    {"operation": operation_id, "tenant": tenant},
                    timeout=self.settings.falkordb_query_timeout_ms,
                ).result_set
                if previous:
                    if previous[0][0] != input_digest:
                        raise SourceConflict("idempotency key reused with different upload")
                    repeated = json.loads(previous[0][1])
                    repeated["request_id"] = request_id
                    return 202, repeated
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
                ) = state[0]
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
                }
                query = sources.UPDATE_SOURCE if prior_version else sources.CREATE_SOURCE
                published = graph.query(
                    query, params=params, timeout=self.settings.falkordb_query_timeout_ms
                ).result_set
                if not published:
                    raise SourceConflict("graph state changed during source publication")
                return 202, result
            except (RedisError, OSError) as exc:
                raise GraphUnavailable("source publication failed") from exc
