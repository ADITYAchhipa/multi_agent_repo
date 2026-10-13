"""HTTP review workflows against a real, disposable FalkorDB graph."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest
from falkordb.graph import Graph
from fastapi.testclient import TestClient

from app.graph.queries import promises
from app.graph.repository import GraphRepository
from app.promise_seal.canonicalize import strict_json
from app.promise_seal.crypto import TrustedKey, load_private_key, verify_bytes
from app.promise_seal.models import ReceiptEnvelope
from app.services.audit import sign_audit

pytestmark = pytest.mark.integration


def login(client, credential="reviewer-credential"):
    assert client.post("/api/session", json={"credential": credential}).status_code == 200


def detail(client, promise, version=None):
    response = client.get(
        f"/api/promises/{promise}", params={"version_id": version} if version else {}
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def reviewed_source(proposal_system):
    client, graph = proposal_system
    response = client.post(
        "/api/sources/upload",
        data={"source_type": "NOTES", "access_label": "PUBLIC_DEMO"},
        files={"file": ("review.txt", b"We will deliver the integration.", "text/plain")},
        headers={"Idempotency-Key": "review-source-key-1234"},
    )
    assert response.status_code == 202, response.text
    promise = client.get("/api/promises").json()["items"][0]["id"]
    original = detail(client, promise)
    login(client)
    body = {
        "expected_version_id": original["receipt"]["payload"]["receipt_id"],
        "expected_revision": 1,
        "decision": "CONFIRM",
        "reason": "Reviewed exact evidence",
        "evidence_ref_ids": [ref["evidence_ref_id"] for ref in original["evidence"]],
    }
    return client, graph, promise, original, body


def review(client, promise, body, key="review-request-key-1234"):
    return client.post(
        f"/api/promises/{promise}/review", json=body, headers={"Idempotency-Key": key}
    )


def checked(client, promise, version=None):
    response = client.get(
        f"/api/promises/{promise}/verify", params={"version_id": version} if version else {}
    )
    assert response.status_code == 200, response.text
    return response.json()["verification"]


def assert_valid(result):
    assert result["integrity"] == "VALID"
    assert all(check["result"] == "PASS" for check in result["checks"]), result
    assert result["eligible_for_action"] is False


def test_signed_successor_replay_and_historical_reads(reviewed_source, tmp_path):
    client, graph, promise, original, body = reviewed_source
    first = review(client, promise, body)
    assert first.status_code == 200, first.text
    receipt = first.json()["receipt"]
    private = load_private_key(tmp_path / "key.pem")
    trusted = TrustedKey("tenant-demo", "demo", "test-key", private.public_key())
    assert (
        verify_bytes(
            ReceiptEnvelope.model_validate(receipt),
            {("tenant-demo", "demo", "test-key"): trusted},
            tenant_id="tenant-demo",
        ).integrity
        == "VALID"
    )
    assert receipt["payload"]["version"] == 2
    assert receipt["payload"]["previous_payload_sha256"] == original["receipt"]["payload_sha256"]
    assert receipt["payload"]["confirmation"]["confirmed_by"] == "reviewer"
    assert detail(client, promise)["receipt"] == receipt
    assert_valid(checked(client, promise))
    old_id = body["expected_version_id"]
    assert detail(client, promise, old_id)["receipt"] == original["receipt"]
    assert (
        detail(client, promise, old_id)["promise"]["current_version_id"]
        == receipt["payload"]["receipt_id"]
    )
    old = checked(client, promise, old_id)
    assert_valid(old)
    assert old["standing"] == "SUPERSEDED"
    copied = client.post("/api/receipts/verify", json={"receipt": original["receipt"]})
    assert copied.status_code == 200, copied.text
    assert_valid(copied.json()["verification"])
    replay = review(client, promise, body)
    assert replay.status_code == 200, replay.text
    assert replay.json()["receipt"] == receipt
    assert replay.json()["request_id"] == replay.headers["X-Request-ID"]
    assert replay.json()["audit_event_id"] == first.json()["audit_event_id"]
    assert graph.ro_query("MATCH (v:PromiseVersion) RETURN count(v)").result_set == [[2]]
    assert graph.ro_query("MATCH (a:AuditEvent) RETURN count(a)").result_set == [[2]]
    assert review(client, promise, {**body, "reason": "Different request"}).status_code == 409
    assert review(client, promise, body, "new-key-stale-review-123").status_code == 409


@pytest.mark.parametrize(
    "damage",
    [
        "signature",
        "audit_missing",
        "audit_signature",
        "version",
        "standing",
        "pointer",
        "supersedes",
        "event_edge",
    ],
)
def test_corrupt_history_fails_safely(reviewed_source, damage):
    client, graph, promise, _, body = reviewed_source
    response = review(client, promise, body)
    assert response.status_code == 200, response.text
    version = response.json()["receipt"]["payload"]["receipt_id"]
    queries = {
        "signature": "MATCH (v:PromiseVersion {version:1}) SET v.signature=$bad",
        "audit_missing": "MATCH (a:AuditEvent {sequence:1}) DETACH DELETE a",
        "audit_signature": "MATCH (a:AuditEvent {sequence:2}) SET a.signature=$bad",
        "version": "MATCH (v:PromiseVersion {version:2}) SET v.version=3",
        "standing": "MATCH (v:PromiseVersion {version:1}) SET v.receipt_standing='ACTIVE'",
        "pointer": "MATCH (p:Promise) SET p.current_version_id=$old",
        "supersedes": "MATCH ()-[e:SUPERSEDES]->() DELETE e",
        "event_edge": "MATCH (v:PromiseVersion {version:2})-[e:HAS_EVENT]->() DELETE e",
    }
    graph.query(queries[damage], {"bad": "A" * 86, "old": body["expected_version_id"]})
    result = checked(client, promise, version)
    assert any(c["result"] == "FAIL" for c in result["checks"]), result
    assert result["eligible_for_action"] is False


@pytest.mark.parametrize("damage", ["digest", "actor", "decision", "receipt_id", "promise_id"])
def test_valid_audit_signature_cannot_hide_receipt_mismatch(reviewed_source, tmp_path, damage):
    client, graph, promise, _, body = reviewed_source
    assert review(client, promise, body).status_code == 200
    raw = graph.ro_query("MATCH (a:AuditEvent {sequence:2}) RETURN a.payload_json").result_set[0][0]
    event = strict_json(raw.encode())
    if damage == "digest":
        event["payload"]["payload_sha256"] = "0" * 64
    elif damage == "actor":
        event["actor_id"] = "different-reviewer"
    elif damage in {"receipt_id", "promise_id"}:
        event["payload"][damage] = "different-" + damage
    else:
        event["payload"]["decision"] = "REJECT"
    signed = sign_audit(event, tmp_path / "key.pem")
    graph.query(
        "MATCH (a:AuditEvent {sequence:2}), (s:GraphState) "
        "SET a.payload_json=$payload,a.event_hash=$hash,a.signature=$signature,"
        "s.audit_head_hash=$hash",
        {"payload": signed.payload_json, "hash": signed.event_hash, "signature": signed.signature},
    )
    login(client, "admin-credential")
    audit = client.get("/api/audit/verify")
    assert audit.status_code == 200, audit.text
    assert audit.json()["chain_result"] == "VALID", audit.text
    result = checked(client, promise)
    assert any(
        c["code"] == "RECEIPT_HISTORY" and c["result"] == "FAIL" for c in result["checks"]
    ), result
    assert result["eligible_for_action"] is False


def test_redirected_supersedes_edge_fails_history_verification(reviewed_source):
    client, graph, promise, _, body = reviewed_source
    response = review(client, promise, body)
    assert response.status_code == 200, response.text
    successor_id = response.json()["receipt"]["payload"]["receipt_id"]

    login(client, "admin-credential")
    other = client.post(
        "/api/sources/upload",
        data={"source_type": "NOTES", "access_label": "PUBLIC_DEMO"},
        files={"file": ("other.txt", b"We will deliver the separate report.", "text/plain")},
        headers={"Idempotency-Key": "other-source-key-1234"},
    )
    assert other.status_code == 202, other.text
    promises = client.get("/api/promises").json()["items"]
    other_promise = next(item["id"] for item in promises if item["id"] != promise)
    unrelated_id = detail(client, other_promise)["receipt"]["payload"]["receipt_id"]

    graph.query(
        "MATCH (v:PromiseVersion {id:$successor})-[e:SUPERSEDES]->(:PromiseVersion), "
        "(wrong:PromiseVersion {id:$unrelated}) "
        "DELETE e "
        "CREATE (v)-[:SUPERSEDES {id:'redirected-supersedes',tenant_id:'tenant-demo',"
        "status:'ACTIVE',access_label:'PUBLIC_DEMO'}]->(wrong)",
        {"successor": successor_id, "unrelated": unrelated_id},
    )
    audit = client.get("/api/audit/verify")
    assert audit.status_code == 200, audit.text
    assert audit.json()["chain_result"] == "VALID", audit.text
    login(client)
    result = checked(client, promise)
    assert any(c["code"] == "RECEIPT_HISTORY" and c["result"] == "FAIL" for c in result["checks"])
    assert result["eligible_for_action"] is False


def test_repeated_reviews_and_replay_after_later_version(reviewed_source):
    client, graph, promise, original, body = reviewed_source
    first = review(client, promise, body)
    assert first.status_code == 200, first.text
    second_body = {
        **body,
        "expected_version_id": first.json()["receipt"]["payload"]["receipt_id"],
        "expected_revision": 2,
        "decision": "DISPUTE",
        "reason": "New disagreement about the interpretation",
    }
    second = review(client, promise, second_body, "second-review-key-1234")
    assert second.status_code == 200, second.text
    assert second.json()["receipt"]["payload"]["version"] == 3
    for receipt in [original["receipt"], first.json()["receipt"], second.json()["receipt"]]:
        version = receipt["payload"]["receipt_id"]
        assert detail(client, promise, version)["receipt"] == receipt
        assert_valid(checked(client, promise, version))
    replay = review(client, promise, body)
    assert replay.status_code == 200, replay.text
    assert replay.json()["receipt"] == first.json()["receipt"]
    assert detail(client, promise)["receipt"] == second.json()["receipt"]
    assert graph.ro_query("MATCH (v:PromiseVersion) RETURN count(v)").result_set == [[3]]
    assert graph.ro_query("MATCH (a:AuditEvent) RETURN count(a)").result_set == [[3]]


def test_revised_content_survives_readback_and_preserves_history(reviewed_source):
    client, _, promise, original, body = reviewed_source
    deadline = {
        "original_text": "2026-12-01",
        "precision": "DATE",
        "local_date": "2026-12-01",
        "instant": None,
        "timezone": None,
        "resolution_basis": "Reviewer interpretation",
    }
    response = review(
        client,
        promise,
        {
            **body,
            "decision": "REVISE",
            "revised_content": {"deliverable": "Reviewed deliverable", "deadline": deadline},
        },
    )
    assert response.status_code == 200, response.text
    for summary in [
        detail(client, promise)["promise"],
        client.get("/api/promises").json()["items"][0],
    ]:
        assert summary["deadline"] == "2026-12-01"
        assert summary["deliverable"] == "Reviewed deliverable"
    old = detail(client, promise, body["expected_version_id"])
    assert old["promise"]["deadline"] == original["promise"]["deadline"]
    assert old["receipt"] == original["receipt"]
    assert_valid(checked(client, promise))


@pytest.mark.parametrize("damage", ["signature", "audit_missing", "audit_signature"])
@pytest.mark.parametrize("decision", ["CONFIRM", "REVISE", "REJECT"])
def test_review_cannot_extend_invalid_history(reviewed_source, damage, decision):
    client, graph, promise, _, body = reviewed_source
    query = {
        "signature": "MATCH (v:PromiseVersion) SET v.signature=$bad",
        "audit_missing": "MATCH (a:AuditEvent) DETACH DELETE a",
        "audit_signature": "MATCH (a:AuditEvent) SET a.signature=$bad",
    }[damage]
    graph.query(query, {"bad": "A" * 86})
    request = {**body, "decision": decision}
    if decision == "REVISE":
        request["revised_content"] = {"deliverable": "Revised interpretation"}
    assert review(client, promise, request).status_code == 409
    assert graph.ro_query("MATCH (v:PromiseVersion) RETURN count(v)").result_set == [[1]]


def test_tenant_role_and_replay_acl(reviewed_source):
    client, graph, promise, original, body = reviewed_source
    login(client, "admin-credential")
    assert review(client, promise, body).status_code == 403
    login(client)
    assert review(client, promise, body).status_code == 200
    login(client, "other-reviewer-credential")
    for suffix in ["", "/verify"]:
        assert (
            client.get(
                f"/api/promises/{promise}{suffix}",
                params={"version_id": original["receipt"]["payload"]["receipt_id"]},
            ).status_code
            == 404
        )
    assert (
        client.post("/api/receipts/verify", json={"receipt": original["receipt"]}).status_code
        == 404
    )
    assert review(client, promise, body).status_code == 404
    login(client)
    graph.query("MATCH (s:SourceRecord) SET s.access_label='RESTRICTED'")
    assert review(client, promise, body).status_code == 404


@pytest.mark.parametrize("same_key", [True, False])
def test_concurrent_reviews_preserve_one_successor(reviewed_source, monkeypatch, same_key):
    client, graph, promise, _, body = reviewed_source
    barrier = Barrier(4)
    original_read = GraphRepository.review_state

    def synchronized_read(self, *args):
        result = original_read(self, *args)
        barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(GraphRepository, "review_state", synchronized_read)

    def submit(index):
        peer = TestClient(client.app)
        login(peer)
        return review(
            peer,
            promise,
            body,
            "concurrent-key-123456" if same_key else f"concurrent-key-{index}-123456",
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        replies = list(pool.map(submit, range(4)))
    statuses = sorted(reply.status_code for reply in replies)
    assert statuses == ([200] * 4 if same_key else [200, 409, 409, 409]), [r.text for r in replies]
    assert graph.ro_query("MATCH (v:PromiseVersion) RETURN count(v)").result_set == [[2]]
    assert graph.ro_query("MATCH (a:AuditEvent) RETURN count(a)").result_set == [[2]]
    assert_valid(checked(client, promise))


def test_failed_review_write_rolls_back_then_retries(reviewed_source, monkeypatch):
    client, graph, promise, _, body = reviewed_source
    with monkeypatch.context() as patch:
        patch.setattr(
            promises,
            "PUBLISH_REVIEW",
            promises.PUBLISH_REVIEW.replace(
                "RETURN p.id,new.id,p.revision,p.current_state,a.id",
                "SET s.invalid={nested:'invalid property'} RETURN p.id",
            ),
        )
        assert review(client, promise, body).status_code == 503
    assert graph.ro_query("MATCH (v:PromiseVersion) RETURN count(v)").result_set == [[1]]
    assert graph.ro_query("MATCH (s:GraphState) RETURN s.revision,s.audit_sequence").result_set == [
        [1, 1]
    ]
    assert review(client, promise, body).status_code == 200
    assert_valid(checked(client, promise))


def test_history_crosses_99_100_101_and_remains_reviewable(reviewed_source):
    client, graph, promise, original, body = reviewed_source
    current = original["receipt"]
    for version in range(2, 103):
        response = review(
            client,
            promise,
            {
                **body,
                "expected_version_id": current["payload"]["receipt_id"],
                "expected_revision": version - 1,
                "decision": "REVISE",
                "revised_content": {"deliverable": f"Reviewed interpretation {version}"},
            },
            f"long-history-key-{version:04}",
        )
        assert response.status_code == 200, (version, response.text)
        current = response.json()["receipt"]
        if version in {99, 100, 101, 102}:
            assert_valid(checked(client, promise))
            old = detail(client, promise, body["expected_version_id"])
            assert old["receipt"] == original["receipt"]
            assert old["promise"]["current_version_id"] == current["payload"]["receipt_id"]
            assert len(old["versions"]) == version
            assert_valid(checked(client, promise, body["expected_version_id"]))
    assert graph.ro_query("MATCH (v:PromiseVersion) RETURN count(v)").result_set == [[102]]
    # A bad predecessor in an earlier page must still invalidate the complete history.
    graph.query("MATCH (v:PromiseVersion {version:2}) SET v.signature=$bad", {"bad": "A" * 86})
    assert any(check["result"] == "FAIL" for check in checked(client, promise)["checks"])


def test_signed_audit_suffix_rollback_is_not_detected_without_checkpoint(reviewed_source):
    client, graph, promise, _, body = reviewed_source
    assert review(client, promise, body).status_code == 200
    login(client, "admin-credential")
    assert client.get("/api/audit/verify").json()["chain_result"] == "VALID"
    graph.query("MATCH (a:AuditEvent {sequence:2}) DETACH DELETE a")
    assert client.get("/api/audit/verify").json()["chain_result"] == "INVALID"
    graph.query(
        "MATCH (s:GraphState),(a:AuditEvent {sequence:1}) "
        "SET s.audit_sequence=1,s.audit_head_hash=a.event_hash"
    )
    result = client.get("/api/audit/verify")
    assert result.status_code == 200, result.text
    assert result.json()["chain_result"] == "VALID"
    assert result.json()["checkpoint"]["available"] is False
    assert "No independently trusted external checkpoint" in result.json()["limitations"][0]


@pytest.mark.parametrize("version", [1, 2])
def test_wrong_signed_event_type_fails_receipt_history(reviewed_source, tmp_path, version):
    client, graph, promise, _, body = reviewed_source
    if version == 2:
        assert review(client, promise, body).status_code == 200
    raw = graph.ro_query(
        "MATCH (a:AuditEvent {sequence:$sequence}) RETURN a.payload_json",
        {"sequence": version},
    ).result_set[0][0]
    event = strict_json(raw.encode())
    wrong_type = "PROMISE_REVIEW" if version == 1 else "SOURCE_IMPORTED"
    event["event_type"] = wrong_type
    signed = sign_audit(event, tmp_path / "key.pem")
    graph.query(
        "MATCH (a:AuditEvent {sequence:$sequence}), (s:GraphState) "
        "SET a.payload_json=$payload,a.event_hash=$hash,a.signature=$signature,"
        "a.event_type=$event_type,s.audit_head_hash=$hash",
        {
            "sequence": version,
            "payload": signed.payload_json,
            "hash": signed.event_hash,
            "signature": signed.signature,
            "event_type": wrong_type,
        },
    )
    login(client, "admin-credential")
    audit = client.get("/api/audit/verify")
    assert audit.status_code == 200, audit.text
    assert audit.json()["chain_result"] == "VALID", audit.text
    verification = checked(client, promise)
    assert any(check["result"] == "FAIL" for check in verification["checks"])


def test_review_commit_during_history_verification_retries(reviewed_source, monkeypatch):
    client, graph, promise, _, body = reviewed_source
    ready = Event()
    release = Event()
    original = GraphRepository.audit_chain
    paused = False

    def pause_once(self, tenant):
        nonlocal paused
        if not paused:
            paused = True
            ready.set()
            assert release.wait(timeout=10)
        return original(self, tenant)

    monkeypatch.setattr(GraphRepository, "audit_chain", pause_once)

    def verify_in_peer():
        peer = TestClient(client.app)
        login(peer)
        return peer.get(f"/api/promises/{promise}/verify")

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="history_verifier") as pool:
        future = pool.submit(verify_in_peer)
        try:
            assert ready.wait(timeout=10)
            committed = review(client, promise, body)
            assert committed.status_code == 200, committed.text
        finally:
            release.set()
        result = future.result(timeout=15)
    assert result.status_code == 200, result.text
    verification = result.json()["verification"]
    assert all(check["result"] == "PASS" for check in verification["checks"]), verification
    assert graph.ro_query("MATCH (v:PromiseVersion) RETURN count(v)").result_set == [[2]]


def test_unstable_receipt_boundaries_return_unavailable(reviewed_source, monkeypatch):
    client, _, promise, _, _ = reviewed_source
    original = GraphRepository.audit_boundary
    reads = 0

    def moving_boundary(self, tenant):
        nonlocal reads
        reads += 1
        boundary = original(self, tenant)
        return [boundary[0], boundary[1], boundary[2] + reads]

    monkeypatch.setattr(GraphRepository, "audit_boundary", moving_boundary)
    verification = checked(client, promise)
    history = [check for check in verification["checks"] if check["code"] == "RECEIPT_HISTORY"]
    assert history[0]["result"] == "UNAVAILABLE"
    assert "changed during history verification" in history[0]["reason"]


def test_review_publication_rejects_changed_audit_head(reviewed_source, monkeypatch):
    client, graph, promise, _, body = reviewed_source
    original = Graph.query
    changed = False

    def change_head_before_review(self, query, *args, **kwargs):
        nonlocal changed
        if self.name == graph.name and query == promises.PUBLISH_REVIEW and not changed:
            changed = True
            original(self, "MATCH (s:GraphState) SET s.audit_head_hash=$hash", {"hash": "0" * 64})
        return original(self, query, *args, **kwargs)

    monkeypatch.setattr(Graph, "query", change_head_before_review)
    assert review(client, promise, body).status_code == 409
    assert changed
    assert graph.ro_query("MATCH (v:PromiseVersion) RETURN count(v)").result_set == [[1]]
    assert graph.ro_query("MATCH (a:AuditEvent) RETURN count(a)").result_set == [[1]]
