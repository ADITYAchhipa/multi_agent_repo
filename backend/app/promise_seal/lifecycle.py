"""Pure guards only; publication and authorized events require the real graph gate."""

from app.promise_seal.canonicalize import digest
from app.promise_seal.models import ReceiptEnvelope, ReceiptPayload

CONTENT_FIELDS = (
    "promise_id",
    "tenant_id",
    "statement",
    "deliverable",
    "customer_id",
    "project_id",
    "deadline",
    "price_condition",
    "commercial_value",
    "commitment_class",
    "source_refs",
    "contract_refs",
    "jira_refs",
    "workload_refs",
)


def content_hash(payload: ReceiptPayload) -> str:
    data = payload.model_dump(mode="json")
    return digest({key: data[key] for key in CONTENT_FIELDS})


def next_state(current: str, decision: str) -> str:
    transitions = {
        "CONFIRM": ({"PROPOSED", "NEEDS_REVIEW", "DISPUTED"}, "CONFIRMED"),
        "DISPUTE": ({"PROPOSED", "NEEDS_REVIEW", "CONFIRMED", "FULFILLED"}, "DISPUTED"),
        "REJECT": ({"PROPOSED", "NEEDS_REVIEW", "DISPUTED"}, "REJECTED"),
        "FULFILL": ({"CONFIRMED"}, "FULFILLED"),
        "REVISE": ({"PROPOSED", "NEEDS_REVIEW", "CONFIRMED", "DISPUTED", "FULFILLED"}, "PROPOSED"),
    }
    if decision not in transitions or current not in transitions[decision][0]:
        raise ValueError("invalid review transition")
    return transitions[decision][1]


def check_parent(child: ReceiptEnvelope, parent: ReceiptEnvelope | None) -> None:
    p = child.payload
    if p.version == 1:
        if parent is not None:
            raise ValueError("genesis cannot have a parent")
        return
    if parent is None:
        raise ValueError("historical receipt unavailable")
    old = parent.payload
    if (
        p.tenant_id != old.tenant_id
        or p.promise_id != old.promise_id
        or p.version != old.version + 1
        or p.previous_receipt_version_id != old.receipt_id
        or p.previous_payload_sha256 != parent.payload_sha256
        or p.receipt_id == old.receipt_id
    ):
        raise ValueError("broken predecessor linkage")
    if p.confirmation is not None and p.confirmation.reviewed_content_hash != content_hash(p):
        raise ValueError("confirmation does not bind reviewed content")
