import base64
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError

from app.promise_seal.canonicalize import canonical_bytes, digest
from app.promise_seal.crypto import sign, verify_bytes
from app.promise_seal.lifecycle import check_parent, content_hash, next_state
from app.promise_seal.models import ReceiptEnvelope, ReceiptPayload, parse_receipt


def test_sign_roundtrip_and_tamper(payload, keys):
    private, trusted, registry = keys
    receipt = sign(payload, private, trusted)
    assert sign(payload, private, trusted) == receipt
    parsed = parse_receipt(canonical_bytes(receipt.model_dump(mode="json")))
    assert verify_bytes(parsed, registry, tenant_id="tenant-demo").integrity == "VALID"
    copy = receipt.model_dump(mode="json")
    copy["payload"]["deliverable"] = "Altered deliverable"
    result = verify_bytes(ReceiptEnvelope.model_validate(copy), registry, tenant_id="tenant-demo")
    assert set(result.failures) == {"PAYLOAD_DIGEST_MISMATCH", "INVALID_SIGNATURE"}
    assert receipt.payload.deliverable == "Loyalty integration"


def test_wrong_unknown_compromised_retired_and_cross_tenant(payload, keys):
    private, trusted, registry = keys
    receipt = sign(payload, private, trusted)
    index = (trusted.tenant_id, trusted.issuer_id, trusted.key_id)
    wrong = replace(trusted, public_key=Ed25519PrivateKey.generate().public_key())
    assert (
        "INVALID_SIGNATURE"
        in verify_bytes(receipt, {index: wrong}, tenant_id="tenant-demo").failures
    )
    assert verify_bytes(receipt, {}, tenant_id="tenant-demo").failures == ("UNKNOWN_KEY_ID",)
    assert verify_bytes(receipt, registry, tenant_id="other").failures == ("TENANT_MISMATCH",)
    for state in ["COMPROMISED", "RETIRED"]:
        key = replace(trusted, trust=state)
        result = verify_bytes(receipt, {index: key}, tenant_id="tenant-demo")
        assert result.integrity == ("INDETERMINATE" if state == "COMPROMISED" else "VALID")
        with pytest.raises(ValueError):
            sign(payload, private, key)


def test_unsigned_and_signature_mutation(payload_dict, keys):
    private, trusted, registry = keys
    payload = ReceiptPayload.model_validate(payload_dict)
    receipt = sign(payload, private, trusted)
    copy = receipt.model_dump(mode="json")
    copy["signature_base64url"] = base64.urlsafe_b64encode(b"\0" * 64).rstrip(b"=").decode()
    assert (
        verify_bytes(
            ReceiptEnvelope.model_validate(copy), registry, tenant_id="tenant-demo"
        ).integrity
        == "INVALID"
    )
    payload_dict.update(issued_at=None, signing_key_id=None)
    unsigned = ReceiptEnvelope(
        payload=ReceiptPayload.model_validate(payload_dict),
        payload_sha256=digest(payload_dict),
        signature_base64url=None,
    )
    assert verify_bytes(unsigned, registry, tenant_id="tenant-demo").integrity == "UNSIGNED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("unknown", True),
        ("version", True),
        ("version", "1"),
        ("version", 0),
        ("created_at", "2026-02-30T09:00:00.000Z"),
        ("created_at", "2026-10-12T09:00:00Z"),
        ("signature_algorithm", "none"),
        ("canonicalization", "JCS"),
        ("status_at_issuance", "CONFIRMED"),
        ("status_at_issuance", "SUPERSEDED"),
        ("deliverable", "\ud800"),
        ("customer_id", None),
    ],
)
def test_payload_schema(payload_dict, field, value):
    payload_dict[field] = value
    if field == "customer_id":
        # Unresolved identity remains legitimate proposal data, never authorization.
        assert ReceiptPayload.model_validate(payload_dict).customer_id is None
    else:
        with pytest.raises((ValidationError, ValueError)):
            ReceiptPayload.model_validate(payload_dict)


@pytest.mark.parametrize("value", ["1.00", "01", "+1", "-0", "1e2", "NaN", "-1"])
def test_bad_money(payload_dict, value):
    payload_dict["commercial_value"] = {
        "amount": value,
        "currency": "USD",
        "evidence_ref_id": "evidence-meeting",
    }
    with pytest.raises(ValidationError):
        ReceiptPayload.model_validate(payload_dict)


def test_review_linkage_and_content_binding(payload, keys):
    private, trusted, _ = keys
    parent = sign(payload, private, trusted)
    data = payload.model_dump(mode="json")
    data.update(
        receipt_id="receipt-loyalty-v2",
        version=2,
        previous_receipt_version_id=payload.receipt_id,
        previous_payload_sha256=parent.payload_sha256,
        review_event_id="review-1",
        status_at_issuance="CONFIRMED",
        confirmation={
            "confirmed_by": "actor-reviewer",
            "confirmed_at": payload.created_at,
            "confirmation_event_id": "review-1",
            "authority_scope": "internal review",
            "reviewed_content_hash": content_hash(payload),
        },
    )
    child = sign(ReceiptPayload.model_validate(data), private, trusted)
    check_parent(child, parent)
    with pytest.raises(ValueError):
        check_parent(child, None)
    data["previous_payload_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        check_parent(sign(ReceiptPayload.model_validate(data), private, trusted), parent)
    data["previous_payload_sha256"] = parent.payload_sha256
    data["deliverable"] = "Unreviewed change"
    with pytest.raises(ValueError):
        check_parent(sign(ReceiptPayload.model_validate(data), private, trusted), parent)


@pytest.mark.parametrize(
    "current,decision,expected",
    [
        ("PROPOSED", "CONFIRM", "CONFIRMED"),
        ("CONFIRMED", "FULFILL", "FULFILLED"),
        ("FULFILLED", "DISPUTE", "DISPUTED"),
        ("DISPUTED", "REVISE", "PROPOSED"),
        ("CONFIRMED", "REJECT", None),
        ("REJECTED", "CONFIRM", None),
        ("PROPOSED", "FULFILL", None),
        ("SUPERSEDED", "CONFIRM", None),
    ],
)
def test_review_transition_table(current, decision, expected):
    if expected is None:
        with pytest.raises(ValueError):
            next_state(current, decision)
    else:
        assert next_state(current, decision) == expected


def test_signer_rejects_wrong_private_key(payload, keys):
    _, trusted, _ = keys
    with pytest.raises(ValueError):
        sign(payload, Ed25519PrivateKey.generate(), trusted)


def test_array_order_is_not_repaired_by_verifier(payload_dict, keys):
    private, trusted, registry = keys
    extra = dict(payload_dict["source_refs"][0])
    extra["evidence_ref_id"] = "z-evidence"
    payload_dict["source_refs"].append(extra)
    receipt = sign(ReceiptPayload.model_validate(payload_dict), private, trusted)
    copy = receipt.model_dump(mode="json")
    copy["payload"]["source_refs"].reverse()
    altered = ReceiptEnvelope.model_validate(copy)
    assert verify_bytes(altered, registry, tenant_id="tenant-demo").integrity == "INVALID"
    with pytest.raises(ValueError):
        sign(altered.payload, private, trusted)


def test_missing_or_extra_envelope_fields(payload, keys):
    private, trusted, _ = keys
    receipt = sign(payload, private, trusted).model_dump(mode="json")
    with pytest.raises(ValidationError):
        parse_receipt(canonical_bytes({**receipt, "eligible_for_action": True}))
    del receipt["payload"]["commercial_value"]
    with pytest.raises(ValidationError):
        parse_receipt(canonical_bytes(receipt))
