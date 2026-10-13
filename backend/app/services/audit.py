"""Canonical signed audit event builder; graph publication is handled separately."""

import base64
import hashlib
import hmac
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidSignature

from app.config import Settings
from app.promise_seal.canonicalize import canonical_bytes, strict_json
from app.promise_seal.crypto import load_private_key
from app.promise_seal.registry import configured_registry


@dataclass(frozen=True)
class SignedAudit:
    payload_json: str
    event_hash: str
    signature: str


SNAPSHOT_ATTEMPTS = 3
UNSTABLE_SNAPSHOT = "Graph changed during audit verification; retry when writes settle."


def sign_audit(payload: dict, key_path: Path) -> SignedAudit:
    raw = canonical_bytes(payload)
    private = load_private_key(key_path)
    return SignedAudit(
        payload_json=raw.decode("utf-8"),
        event_hash=hashlib.sha256(raw).hexdigest(),
        signature=base64.urlsafe_b64encode(private.sign(raw)).rstrip(b"=").decode(),
    )


def verify_audit_chain(
    settings: Settings,
    tenant_id: str,
    state: list,
    events: Iterable[list],
    *,
    collect_checks: bool = True,
) -> tuple[str, list[dict], list[str]]:
    """Verify the local chain against GraphState; no external rollback checkpoint is implied."""
    head_sequence, head_hash = state[:2]
    registry = configured_registry(settings)
    checks = []
    expected_hash = None
    invalid = False
    unknown = False
    count = 0
    for expected_sequence, row in enumerate(events, 1):
        count += 1
        event_hash = None
        try:
            (
                event_id,
                sequence,
                payload_json,
                event_hash,
                previous,
                signature,
                key_id,
                event_type,
            ) = row
            raw = payload_json.encode("utf-8")
            payload = strict_json(raw)
            if canonical_bytes(payload) != raw:
                raise ValueError("noncanonical audit payload")
            valid_fields = (
                payload["event_id"] == event_id
                and payload["tenant_id"] == tenant_id
                and payload["sequence"] == sequence == expected_sequence
                and payload["prev_event_hash"] == previous == expected_hash
                and payload["signing_key_id"] == key_id
                and payload["event_type"] == event_type
                and hmac.compare_digest(hashlib.sha256(raw).hexdigest(), event_hash)
            )
            if not valid_fields:
                raise ValueError("audit sequence or hash mismatch")
            trusted = registry.get((tenant_id, settings.signing_issuer_id, key_id))
            if trusted is None or trusted.trust == "COMPROMISED":
                unknown = True
                checks.append({"sequence": sequence, "code": "KEY_TRUST", "result": "UNAVAILABLE"})
            else:
                decoded = base64.urlsafe_b64decode(signature + "==")
                trusted.public_key.verify(decoded, raw)
                checks.append({"sequence": sequence, "code": "AUDIT_EVENT", "result": "PASS"})
        except ValueError, KeyError, TypeError, InvalidSignature, base64.binascii.Error:
            invalid = True
            checks.append({"sequence": expected_sequence, "code": "AUDIT_EVENT", "result": "FAIL"})
        if not collect_checks:
            checks.clear()
        expected_hash = event_hash
    if count != head_sequence or head_hash != expected_hash:
        invalid = True
        checks.append({"sequence": head_sequence, "code": "GRAPH_HEAD", "result": "FAIL"})
    result = "INVALID" if invalid else "INDETERMINATE" if unknown else "VALID"
    return result, checks, ["No independently trusted external checkpoint is configured."]


def verify_stable_audit(settings: Settings, repository, tenant_id: str):
    """Classify corruption only after the graph head stayed fixed across every page."""
    for _ in range(SNAPSHOT_ATTEMPTS):
        boundary, events = repository.audit_chain(tenant_id)
        result, checks, limitations = verify_audit_chain(settings, tenant_id, boundary, events)
        if boundary == repository.audit_boundary(tenant_id):
            return boundary, result, checks, limitations
    return boundary, "INDETERMINATE", [], [*limitations, UNSTABLE_SNAPSHOT]
