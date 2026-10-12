"""Canonical signed audit event builder; graph publication is handled separately."""

import base64
import hashlib
import hmac
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


def sign_audit(payload: dict, key_path: Path) -> SignedAudit:
    raw = canonical_bytes(payload)
    private = load_private_key(key_path)
    return SignedAudit(
        payload_json=raw.decode("utf-8"),
        event_hash=hashlib.sha256(raw).hexdigest(),
        signature=base64.urlsafe_b64encode(private.sign(raw)).rstrip(b"=").decode(),
    )


def verify_audit_chain(
    settings: Settings, tenant_id: str, state: list, events: list
) -> tuple[str, list[dict], list[str]]:
    """Verify the local chain against GraphState; no external rollback checkpoint is implied."""
    head_sequence, head_hash = state
    if len(events) > 1000:
        return "INDETERMINATE", [], ["Audit chain exceeds the bounded verifier limit."]
    registry = configured_registry(settings)
    checks = []
    expected_hash = None
    invalid = False
    unknown = False
    for expected_sequence, row in enumerate(events, 1):
        event_id, sequence, payload_json, event_hash, previous, signature, key_id = row
        try:
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
            checks.append({"sequence": sequence, "code": "AUDIT_EVENT", "result": "FAIL"})
        expected_hash = event_hash
    if len(events) != head_sequence or head_hash != expected_hash:
        invalid = True
        checks.append({"sequence": head_sequence, "code": "GRAPH_HEAD", "result": "FAIL"})
    result = "INVALID" if invalid else "INDETERMINATE" if unknown else "VALID"
    return result, checks, ["No independently trusted external checkpoint is configured."]
