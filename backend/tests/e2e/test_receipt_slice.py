"""Offline source-to-receipt slice; NOT the FalkorDB business workflow demo."""

from app.ingestion.quote_verifier import parse_text, verify_quote
from app.promise_seal.canonicalize import canonical_bytes
from app.promise_seal.crypto import sign, verify_bytes
from app.promise_seal.models import parse_receipt


def test_source_proposal_signature_and_tamper(payload, keys):
    raw = payload.statement.exact_excerpt.encode()
    assert verify_quote(raw, parse_text(raw), payload.source_refs[0])
    private, trusted, registry = keys
    receipt = sign(payload, private, trusted)
    assert receipt.payload.status_at_issuance == "PROPOSED"
    assert receipt.payload.confirmation is None
    stored_bytes = canonical_bytes(receipt.model_dump(mode="json"))
    assert (
        verify_bytes(parse_receipt(stored_bytes), registry, tenant_id="tenant-demo").integrity
        == "VALID"
    )
    tampered = stored_bytes.replace(
        b'"deliverable":"Loyalty integration"', b'"deliverable":"Unapproved free work"'
    )
    assert (
        verify_bytes(parse_receipt(tampered), registry, tenant_id="tenant-demo").integrity
        == "INVALID"
    )
    assert sign(payload, private, trusted) == receipt
