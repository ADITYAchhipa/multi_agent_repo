"""Build signed initial receipts only after checking retained source evidence."""

from app.ingestion.candidates import PromiseCandidate
from app.ingestion.quote_verifier import verify_quote
from app.models.api import EvidenceRef
from app.promise_seal.crypto import sign
from app.promise_seal.models import ReceiptPayload


def build_proposal(
    candidate: PromiseCandidate,
    *,
    tenant: str,
    source: str,
    version: str,
    promise_id: str,
    receipt_id: str,
    evidence_id: str,
    access_label: str,
    raw: bytes,
    representation: str,
    raw_hash: str,
    representation_hash: str,
    now: str,
    private_key,
    trusted_key,
):
    evidence = EvidenceRef(
        evidence_ref_id=evidence_id,
        source_id=source,
        source_version_id=version,
        source_hash=raw_hash,
        representation_hash=representation_hash,
        origin_reference=f"source:{source}",
        quote=candidate.exact_excerpt,
        start_offset=candidate.start_offset,
        end_offset=candidate.end_offset,
        start_ms=None,
        end_ms=None,
        structured_pointer=None,
        source_updated_at=None,
        observed_at=now,
        verification="VERIFIED",
        access_label=access_label,
    )
    if not verify_quote(raw, representation, evidence):
        raise ValueError("candidate does not match retained evidence")
    payload = ReceiptPayload.model_validate(
        {
            "protocol_version": "promiseseal-v1",
            "receipt_id": receipt_id,
            "promise_id": promise_id,
            "tenant_id": tenant,
            "version": 1,
            "issuer_id": trusted_key.issuer_id,
            "created_at": now,
            "issued_at": now,
            "statement": {
                "exact_excerpt": candidate.exact_excerpt,
                "interpretation": candidate.interpretation,
            },
            "deliverable": candidate.deliverable,
            "customer_id": None,
            "project_id": None,
            "deadline": candidate.deadline.model_dump(),
            "price_condition": candidate.price_condition.model_dump(),
            "commercial_value": (
                {
                    "amount": candidate.commercial_amount,
                    "currency": candidate.commercial_currency,
                    "evidence_ref_id": evidence_id,
                }
                if candidate.commercial_amount is not None
                else None
            ),
            "commitment_class": candidate.commitment_class,
            "source_refs": [evidence.model_dump()],
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
            "signing_key_id": trusted_key.key_id,
        }
    )
    return sign(payload, private_key, trusted_key)
