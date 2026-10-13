from types import SimpleNamespace

import pytest

from app.promise_seal.crypto import sign
from app.promise_seal.models import ReceiptPayload
from app.services.audit import SNAPSHOT_ATTEMPTS
from app.services.history import validate_receipt_event, verify_history


@pytest.mark.parametrize("event_type", ["SOURCE_IMPORTED", "SOURCE_UPDATED"])
def test_genesis_only_accepts_source_publication(payload, keys, event_type):
    private, trusted, _ = keys
    receipt = sign(payload, private, trusted)
    ref = payload.source_refs[0]
    event = {
        "event_type": event_type,
        "payload": {
            "source_id": ref.source_id,
            "source_version_id": ref.source_version_id,
            "content_hash": ref.source_hash,
        },
    }
    validate_receipt_event(receipt, None, event, "audit-source", event_type)
    with pytest.raises(ValueError, match="source publication"):
        validate_receipt_event(
            receipt,
            None,
            {**event, "event_type": "PROMISE_REVIEW"},
            "audit-source",
            "PROMISE_REVIEW",
        )


def test_successor_requires_review_type_and_valid_transition(payload, keys):
    private, trusted, _ = keys
    parent = sign(payload, private, trusted)
    child_payload = ReceiptPayload.model_validate(
        {
            **payload.model_dump(mode="json"),
            "receipt_id": "receipt-loyalty-v2",
            "version": 2,
            "previous_receipt_version_id": payload.receipt_id,
            "previous_payload_sha256": parent.payload_sha256,
            "review_event_id": "audit-review",
        }
    )
    child = sign(child_payload, private, trusted)
    event = {
        "event_type": "PROMISE_REVIEW",
        "actor_id": "reviewer",
        "payload": {
            "promise_id": payload.promise_id,
            "receipt_id": child_payload.receipt_id,
            "decision": "REVISE",
        },
    }
    validate_receipt_event(child, parent, event, "audit-review", "PROMISE_REVIEW")
    with pytest.raises(ValueError, match="review event"):
        validate_receipt_event(
            child,
            parent,
            {**event, "event_type": "SOURCE_IMPORTED"},
            "audit-review",
            "SOURCE_IMPORTED",
        )
    with pytest.raises(ValueError, match="does not produce receipt state"):
        validate_receipt_event(
            child,
            parent,
            {**event, "payload": {**event["payload"], "decision": "REJECT"}},
            "audit-review",
            "PROMISE_REVIEW",
        )
    rejected = SimpleNamespace(
        payload=parent.payload.model_copy(update={"status_at_issuance": "REJECTED"})
    )
    with pytest.raises(ValueError, match="invalid review transition"):
        validate_receipt_event(child, rejected, event, "audit-review", "PROMISE_REVIEW")


def test_changing_receipt_boundaries_exhaust_retries():
    class ChangingRepository:
        reads = 0

        def audit_boundary(self, _tenant):
            self.reads += 1
            return [0, None, self.reads]

        def history_state(self, _tenant, _promise):
            return None

    repository = ChangingRepository()
    result, reason = verify_history(
        None,
        repository,
        {},
        "tenant-demo",
        SimpleNamespace(payload=SimpleNamespace(promise_id="promise-one")),
    )
    assert repository.reads == SNAPSHOT_ATTEMPTS * 2
    assert result == "UNAVAILABLE"
    assert "changed during history verification" in reason
