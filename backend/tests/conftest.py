import hashlib

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.promise_seal.crypto import TrustedKey
from app.promise_seal.models import ReceiptPayload


@pytest.fixture
def keys():
    private = Ed25519PrivateKey.generate()
    trusted = TrustedKey("tenant-demo", "promiseops-demo", "test-key", private.public_key())
    registry = {(trusted.tenant_id, trusted.issuer_id, trusted.key_id): trusted}
    return private, trusted, registry


@pytest.fixture
def payload_dict():
    quote = "We can deliver the loyalty integration by Friday at no extra charge."
    source_hash = hashlib.sha256(quote.encode()).hexdigest()
    at = "2026-10-12T09:00:00.000Z"
    return {
        "protocol_version": "promiseseal-v1",
        "receipt_id": "receipt-loyalty-v1",
        "promise_id": "promise-loyalty",
        "tenant_id": "tenant-demo",
        "version": 1,
        "issuer_id": "promiseops-demo",
        "created_at": at,
        "issued_at": at,
        "statement": {"exact_excerpt": quote, "interpretation": "A proposed integration."},
        "deliverable": "Loyalty integration",
        "customer_id": "customer-acme",
        "project_id": "project-acme-pos",
        "deadline": {
            "original_text": "Friday",
            "precision": "UNKNOWN",
            "local_date": None,
            "instant": None,
            "timezone": None,
            "resolution_basis": None,
        },
        "price_condition": {"kind": "NO_ADDITIONAL_CHARGE", "original_text": "no extra charge"},
        "commercial_value": None,
        "commitment_class": "explicit",
        "source_refs": [
            {
                "evidence_ref_id": "evidence-meeting",
                "source_id": "src-meeting-1",
                "source_version_id": "src-meeting-1-v1",
                "source_hash": source_hash,
                "representation_hash": source_hash,
                "origin_reference": "source:src-meeting-1",
                "quote": quote,
                "start_offset": 0,
                "end_offset": len(quote),
                "start_ms": 12000,
                "end_ms": 18000,
                "structured_pointer": None,
                "source_updated_at": at,
                "observed_at": at,
                "verification": "VERIFIED",
                "access_label": "PUBLIC_DEMO",
            }
        ],
        "contract_refs": [],
        "jira_refs": [],
        "workload_refs": [],
        "status_at_issuance": "PROPOSED",
        "confirmation": None,
        "review_event_id": None,
        "previous_receipt_version_id": None,
        "previous_payload_sha256": None,
        "canonicalization": "promiseops-json-v1",
        "signature_algorithm": "Ed25519",
        "signing_key_id": "test-key",
    }


@pytest.fixture
def payload(payload_dict):
    return ReceiptPayload.model_validate(payload_dict)
