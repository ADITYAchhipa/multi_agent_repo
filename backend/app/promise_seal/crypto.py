"""Byte integrity only. Graph history, source truth and authorization are separate gates."""

import base64
import hashlib
import hmac
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from app.promise_seal.canonicalize import canonical_bytes
from app.promise_seal.models import ReceiptEnvelope, ReceiptPayload


@dataclass(frozen=True)
class TrustedKey:
    tenant_id: str
    issuer_id: str
    key_id: str
    public_key: Ed25519PublicKey
    trust: Literal["TRUSTED", "RETIRED", "COMPROMISED"] = "TRUSTED"


@dataclass(frozen=True)
class ByteIntegrity:
    integrity: Literal["VALID", "INVALID", "UNSIGNED", "INDETERMINATE"]
    failures: tuple[str, ...]
    key_trust: Literal["TRUSTED", "RETIRED", "COMPROMISED", "UNKNOWN"]


def load_private_key(path: Path) -> Ed25519PrivateKey:
    # Caller supplies a secure runtime mount, never a path from receipt/document/HTTP.
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("Ed25519 private key required")
    return key


def sign(
    payload: ReceiptPayload, key: Ed25519PrivateKey, trusted_key: TrustedKey
) -> ReceiptEnvelope:
    # Revalidate: frozen Pydantic objects can still contain mutable lists.
    payload = ReceiptPayload.model_validate(payload.model_dump(mode="json"))
    ordered_sources = sorted(
        payload.source_refs,
        key=lambda ref: (
            ref.source_version_id,
            ref.start_offset if ref.start_offset is not None else -1,
            ref.end_offset if ref.end_offset is not None else -1,
            ref.evidence_ref_id,
        ),
    )
    if payload.source_refs != ordered_sources:
        raise ValueError("producer must sort source references before signing")
    for refs in (payload.contract_refs, payload.jira_refs, payload.workload_refs):
        if refs != sorted(refs, key=lambda ref: (ref.entity_id, ref.source_version_id)):
            raise ValueError("producer must sort entity references before signing")
        if any(ref.evidence_ref_ids != sorted(ref.evidence_ref_ids) for ref in refs):
            raise ValueError("producer must sort nested evidence IDs before signing")
    if (payload.tenant_id, payload.issuer_id, payload.signing_key_id) != (
        trusted_key.tenant_id,
        trusted_key.issuer_id,
        trusted_key.key_id,
    ):
        raise ValueError("payload does not match the configured signing identity")
    if trusted_key.trust != "TRUSTED":
        raise ValueError("retired or compromised key cannot issue receipts")
    if key.public_key().public_bytes_raw() != trusted_key.public_key.public_bytes_raw():
        raise ValueError("private key does not match trusted registry")
    raw = canonical_bytes(payload.model_dump(mode="json"))
    return ReceiptEnvelope(
        payload=payload,
        payload_sha256=hashlib.sha256(raw).hexdigest(),
        signature_base64url=base64.urlsafe_b64encode(key.sign(raw)).rstrip(b"=").decode("ascii"),
    )


def verify_bytes(
    receipt: ReceiptEnvelope,
    registry: dict[tuple[str, str, str], TrustedKey],
    *,
    tenant_id: str,
) -> ByteIntegrity:
    receipt = ReceiptEnvelope.model_validate(receipt.model_dump(mode="json"))
    payload = receipt.payload
    if payload.tenant_id != tenant_id:
        return ByteIntegrity("INVALID", ("TENANT_MISMATCH",), "UNKNOWN")
    raw = canonical_bytes(payload.model_dump(mode="json"))
    failures = []
    if not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), receipt.payload_sha256):
        failures.append("PAYLOAD_DIGEST_MISMATCH")
    if receipt.signature_base64url is None:
        return ByteIntegrity("INVALID" if failures else "UNSIGNED", tuple(failures), "UNKNOWN")
    key = registry.get((tenant_id, payload.issuer_id, payload.signing_key_id))
    if key is None or (key.tenant_id, key.issuer_id, key.key_id) != (
        tenant_id,
        payload.issuer_id,
        payload.signing_key_id,
    ):
        return ByteIntegrity("INVALID", (*failures, "UNKNOWN_KEY_ID"), "UNKNOWN")
    signature = base64.urlsafe_b64decode(receipt.signature_base64url + "==")
    if base64.urlsafe_b64encode(signature).rstrip(b"=").decode() != receipt.signature_base64url:
        failures.append("NONCANONICAL_SIGNATURE")
    try:
        key.public_key.verify(signature, raw)
    except InvalidSignature:
        failures.append("INVALID_SIGNATURE")
    integrity = "INVALID" if failures else "VALID"
    if key.trust == "COMPROMISED" and not failures:
        integrity = "INDETERMINATE"
        failures.append("COMPROMISED_KEY")
    return ByteIntegrity(integrity, tuple(failures), key.trust)
