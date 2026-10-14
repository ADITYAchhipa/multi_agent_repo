from app.ingestion.artifacts import ArtifactStore
from app.ingestion.quote_verifier import verify_quote
from app.models.promises import SourceVerification, Verification, VerificationCheck
from app.promise_seal.crypto import verify_bytes
from app.promise_seal.models import ReceiptEnvelope
from app.promise_seal.registry import configured_registry
from app.services.history import verify_history
from app.services.mutations import now as _timestamp


def evaluate_receipt(
    settings, repository, receipt: ReceiptEnvelope, tenant_id: str, standing: str
) -> Verification:
    registry = configured_registry(settings)
    artifacts = ArtifactStore(settings.source_storage_root)
    byte_result = verify_bytes(receipt, registry, tenant_id=tenant_id)
    source_results = []
    for ref in receipt.payload.source_refs:
        try:
            raw = artifacts.read(tenant_id, ref.source_hash, "raw")
            representation = artifacts.read(
                tenant_id, ref.representation_hash, "representation"
            ).decode("utf-8", errors="strict")
            matching = verify_quote(raw, representation, ref)
            source_results.append(
                SourceVerification(
                    evidence_ref_id=ref.evidence_ref_id,
                    result="MATCH" if matching else "MISMATCH",
                    reason="Exact retained bytes and quote match."
                    if matching
                    else "Retained bytes or exact quote do not match.",
                )
            )
        except FileNotFoundError:
            source_results.append(
                SourceVerification(
                    evidence_ref_id=ref.evidence_ref_id,
                    result="UNAVAILABLE",
                    reason="Retained source artifact is unavailable.",
                )
            )
        except ValueError, UnicodeDecodeError:
            source_results.append(
                SourceVerification(
                    evidence_ref_id=ref.evidence_ref_id,
                    result="MISMATCH",
                    reason="Retained source artifact failed validation.",
                )
            )
    source_check = (
        "FAIL"
        if any(item.result == "MISMATCH" for item in source_results)
        else "UNAVAILABLE"
        if any(item.result == "UNAVAILABLE" for item in source_results)
        else "PASS"
    )
    history_result = "PASS"
    history_reason = None
    try:
        history_result, history_reason = verify_history(
            settings, repository, registry, tenant_id, receipt
        )
    except ValueError, TypeError, KeyError:
        history_result = "FAIL"
        history_reason = "Receipt history validation failed."
    checks = [
        VerificationCheck(
            code="PAYLOAD_AND_SIGNATURE",
            result="PASS" if byte_result.integrity == "VALID" else "FAIL",
            reason=None
            if byte_result.integrity == "VALID"
            else ",".join(byte_result.failures) or byte_result.integrity,
        ),
        VerificationCheck(
            code="RETAINED_SOURCE_BYTES",
            result=source_check,
            reason=None if source_check == "PASS" else "Source evidence is not fully verified.",
        ),
        VerificationCheck(
            code="AUDIT_CHAIN",
            result=history_result,
            reason=history_reason,
        ),
        VerificationCheck(
            code="RECEIPT_HISTORY",
            result=history_result,
            reason=history_reason,
        ),
    ]
    return Verification(
        integrity=byte_result.integrity,
        standing=standing,
        checked_at=_timestamp(),
        checks=checks,
        source_results=source_results,
        key_trust=byte_result.key_trust,
        eligible_for_action=False,
    )
