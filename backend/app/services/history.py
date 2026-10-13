"""Verify complete receipt histories with paginated reads and one retained predecessor."""

from app.models.audit import GENESIS_RECEIPT_EVENT_TYPES, SUCCESSOR_RECEIPT_EVENT_TYPE
from app.promise_seal.canonicalize import strict_json
from app.promise_seal.crypto import verify_bytes
from app.promise_seal.lifecycle import check_parent, next_state
from app.promise_seal.models import ReceiptEnvelope, ReceiptPayload
from app.services.audit import SNAPSHOT_ATTEMPTS, verify_audit_chain


def validate_receipt_event(receipt, parent, event, event_id, projected_type):
    """Bind the signed event's meaning to the receipt's place in its lifecycle."""
    payload = receipt.payload
    event_type = event["event_type"]
    if event_type != projected_type:
        raise ValueError("audit event type projection mismatch")
    data = event["payload"]
    if parent is None:
        # Both source event types can issue v1 proposals: a changed source can
        # introduce a new assertion for the first time.
        if event_type not in GENESIS_RECEIPT_EVENT_TYPES:
            raise ValueError("genesis receipt requires a source publication event")
        if not all(
            ref.source_id == data["source_id"]
            and ref.source_version_id == data["source_version_id"]
            and ref.source_hash == data["content_hash"]
            for ref in payload.source_refs
        ):
            raise ValueError("genesis source does not match signed audit event")
        return
    if event_type != SUCCESSOR_RECEIPT_EVENT_TYPE:
        raise ValueError("successor receipt requires a review event")
    if data["promise_id"] != payload.promise_id or data["receipt_id"] != payload.receipt_id:
        raise ValueError("review event targets a different receipt")
    decision = data["decision"]
    if parent.payload.status_at_issuance == "DISPUTED" and decision == "CONFIRM":
        raise ValueError("disputed confirmation requires conflict resolution")
    if next_state(parent.payload.status_at_issuance, decision) != payload.status_at_issuance:
        raise ValueError("review decision does not produce receipt state")
    if payload.review_event_id != event_id:
        raise ValueError("receipt review event mismatch")
    confirmation = payload.confirmation
    if confirmation is not None and (
        confirmation.confirmed_by != event["actor_id"]
        or confirmation.confirmation_event_id != event_id
    ):
        raise ValueError("receipt confirmation event mismatch")


def verify_history(settings, repository, registry, tenant_id, selected):
    promise_id = selected.payload.promise_id
    for _ in range(SNAPSHOT_ATTEMPTS):
        boundary = repository.audit_boundary(tenant_id)
        pointer = repository.history_state(tenant_id, promise_id)
        try:
            result = _verify_once(settings, repository, registry, tenant_id, selected, pointer)
        except ValueError, TypeError, KeyError:
            result = "FAIL", "Receipt history validation failed."
        if boundary == repository.audit_boundary(tenant_id) and pointer == repository.history_state(
            tenant_id, promise_id
        ):
            return result
    return "UNAVAILABLE", "Graph changed during history verification; retry when writes settle."


def _verify_once(settings, repository, registry, tenant_id, selected, pointer):
    promise_id = selected.payload.promise_id
    if pointer is None:
        return "UNAVAILABLE", "Receipt history is missing."
    state, events = repository.audit_chain(tenant_id)
    result, _, _ = verify_audit_chain(settings, tenant_id, state, events, collect_checks=False)
    if result != "VALID":
        return (
            "FAIL" if result == "INVALID" else "UNAVAILABLE",
            "Tenant audit chain cannot establish receipt history.",
        )
    parent = None
    found = False
    previous_event_sequence = 0
    for index, row in enumerate(repository.promise_versions(tenant_id, promise_id), 1):
        receipt = ReceiptEnvelope(
            payload=ReceiptPayload.model_validate(strict_json(row[4].encode())),
            payload_sha256=row[5],
            signature_base64url=row[6],
        )
        payload = receipt.payload
        if (
            row[1] != index
            or payload.version != index
            or row[0] != payload.receipt_id
            or payload.promise_id != promise_id
            or row[7] != promise_id
            or row[2] != payload.status_at_issuance
            or row[3] != ("ACTIVE" if index == pointer[1] else "SUPERSEDED")
        ):
            raise ValueError("receipt history projection mismatch")
        check_parent(receipt, parent)
        if verify_bytes(receipt, registry, tenant_id=tenant_id).integrity != "VALID":
            raise ValueError("invalid historical signature")
        links = repository.history_links(tenant_id, promise_id, payload.receipt_id)
        event_links = [link for link in links if link[1] == "HAS_EVENT"]
        parents = [link[2] for link in links if link[1] == "SUPERSEDES"]
        if len(event_links) != 1 or parents != (
            [payload.previous_receipt_version_id] if parent else []
        ):
            raise ValueError("missing or duplicate history linkage")
        link = event_links[0]
        event = strict_json(link[3].encode())
        if (
            event["event_id"] != link[2]
            or event["tenant_id"] != tenant_id
            or not previous_event_sequence < event["sequence"] <= state[0]
        ):
            raise ValueError("invalid receipt audit event")
        validate_receipt_event(receipt, parent, event, link[2], link[5])
        manifest = event["payload"].get("receipts", [])
        if "receipt_id" in event["payload"]:
            manifest = [*manifest, event["payload"]]
        if not any(
            item["receipt_id"] == payload.receipt_id
            and item["payload_sha256"] == receipt.payload_sha256
            for item in manifest
        ):
            raise ValueError("receipt digest does not match signed audit manifest")
        if payload.receipt_id == selected.payload.receipt_id:
            if receipt != selected:
                raise ValueError("selected receipt differs from history")
            found = True
        previous_event_sequence = event["sequence"]
        parent = receipt
    if (
        parent is None
        or not found
        or pointer
        != [parent.payload.receipt_id, parent.payload.version, parent.payload.status_at_issuance]
    ):
        raise ValueError("inconsistent history head or selected receipt")
    return "PASS", None
