"""Atomic signed mutations with durable actor/route idempotency and graph-head CAS."""

import hashlib
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.graph.connection import GraphUnavailable
from app.promise_seal.canonicalize import canonical_bytes, strict_json
from app.promise_seal.crypto import load_private_key
from app.promise_seal.registry import configured_registry
from app.services.audit import sign_audit


def now():
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class MutationStore:
    def __init__(self, settings, repository):
        self.settings = settings
        self.repository = repository

    def identity(self, actor, route, key):
        return (
            "mutation-"
            + hashlib.sha256(canonical_bytes([actor.tenant_id, actor.id, route, key])).hexdigest()[
                :40
            ]
        )

    def replay(self, actor, route, key, body):
        ledger = self.identity(actor, route, key)
        rows = self.repository._read(
            actor.tenant_id,
            "MATCH (o:OperationRun {id:$id,tenant_id:$tenant,requested_by:$actor}) "
            "RETURN o.input_digest,o.result_json",
            {"id": ledger, "tenant": actor.tenant_id, "actor": actor.id},
        )
        if not rows:
            return None
        if rows[0][0] != hashlib.sha256(canonical_bytes(body)).hexdigest():
            raise HTTPException(409)
        return strict_json(rows[0][1].encode())

    def commit(
        self,
        actor,
        route,
        key,
        body,
        event_type,
        event_payload,
        response,
        *,
        match="",
        mutation="",
        params=None,
        boundary=None,
    ):
        """Fragments are internal constants, never supplied through HTTP input.

        Match must preserve s and its where guards. Mutation must preserve s to RETURN.
        All dependent entity guards belong in match (before the common WITH/WHERE).
        """
        replay = self.replay(actor, route, key, body)
        if replay is not None:
            return replay
        settings = self.settings
        if not settings.signing_private_key_path or not settings.signing_key_id:
            raise GraphUnavailable("mutation signing unavailable")
        registry = configured_registry(settings)
        trusted = registry.get(
            (actor.tenant_id, settings.signing_issuer_id, settings.signing_key_id)
        )
        try:
            private = load_private_key(settings.signing_private_key_path)
            if (
                trusted is None
                or trusted.trust != "TRUSTED"
                or (
                    private.public_key().public_bytes_raw() != trusted.public_key.public_bytes_raw()
                )
            ):
                raise ValueError("untrusted signing key")
            sequence, head, revision = boundary or self.repository.audit_boundary(actor.tenant_id)
            at, event_id = now(), "audit-" + uuid4().hex
            payload = dict(
                protocol_version="promiseops-audit-v1",
                event_id=event_id,
                tenant_id=actor.tenant_id,
                sequence=sequence + 1,
                event_type=event_type,
                actor_id=actor.id,
                occurred_at=at,
                request_id=response.get("request_id", "internal"),
                payload=event_payload,
                prev_event_hash=head,
                signing_key_id=settings.signing_key_id,
            )
            signed = sign_audit(payload, settings.signing_private_key_path)
        except (ValueError, OSError) as exc:
            raise GraphUnavailable("mutation signing unavailable") from exc
        result = {**response, "audit_event_id": event_id}
        ledger = self.identity(actor, route, key)
        values = dict(
            tenant=actor.tenant_id,
            actor=actor.id,
            ledger=ledger,
            input_digest=hashlib.sha256(canonical_bytes(body)).hexdigest(),
            result=canonical_bytes(result).decode(),
            sequence=sequence,
            revision=revision,
            head=head or "",
            event=event_id,
            at=at,
            event_type=event_type,
            signed=signed.payload_json,
            event_hash=signed.event_hash,
            signature=signed.signature,
            signing_key=settings.signing_key_id,
            request_id=response.get("request_id", "internal"),
            **(params or {}),
        )
        query = (
            """
        MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
        WHERE s.revision=$revision AND coalesce(s.audit_sequence,0)=$sequence
          AND coalesce(s.audit_head_hash,'')=$head
        OPTIONAL MATCH (prior:OperationRun {id:$ledger,tenant_id:$tenant})
        WITH s,prior WHERE prior IS NULL
        """
            + match
            + "\n"
            + mutation
            + """
        CREATE (a:AuditEvent {id:$event,tenant_id:$tenant,event_type:$event_type,
          actor_id:$actor,occurred_at:$at,sequence:$sequence+1,payload_json:$signed,
          prev_event_hash:CASE WHEN $head='' THEN null ELSE $head END,
          event_hash:$event_hash,signature:$signature,key_id:$signing_key,
          canonicalization:'promiseops-json-v1',request_id:$request_id,
          access_label:'PUBLIC_DEMO',created_at:$at,updated_at:$at})
        CREATE (o:OperationRun {id:$ledger,tenant_id:$tenant,requested_by:$actor,
          request_id:$request_id,input_digest:$input_digest,result_json:$result,
          kind:'ANALYSIS',status:'SUCCEEDED',phase:'PUBLISHED',created_at:$at,
          started_at:$at,finished_at:$at,errors_json:'[]',access_label:'PUBLIC_DEMO'})
        CREATE (o)-[:HAS_EVENT {id:$ledger+'-event',tenant_id:$tenant,status:'ACTIVE',
          access_label:'PUBLIC_DEMO',provenance_kind:'STRUCTURAL',provenance_json:'[]'}]->(a)
        SET s.revision=s.revision+1,s.audit_sequence=$sequence+1,
            s.audit_head_hash=$event_hash,s.updated_at=$at
        RETURN o.result_json
        """
        )
        try:
            rows = (
                self.repository.connection.graph_for_tenant(actor.tenant_id)
                .query(query, params=values, timeout=settings.falkordb_query_timeout_ms)
                .result_set
            )
        except (RedisError, OSError) as exc:
            raise GraphUnavailable("mutation publication failed") from exc
        if not rows:
            replay = self.replay(actor, route, key, body)
            if replay is not None:
                return replay
            raise HTTPException(409)
        return strict_json(rows[0][0].encode())
