"""Independent ingest instances and malformed traversal tests on real FalkorDB."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest
from falkordb.graph import Graph
from fastapi.testclient import TestClient

from app.auth import Actor
from app.graph.connection import GraphConnection
from app.graph.queries import sources
from app.graph.repository import GraphRepository
from app.services.audit import sign_audit
from app.services.source_ingest import SourceConflict, SourceIngestService

pytestmark = pytest.mark.integration


def upload(service, raw=b"We will deliver the integration.", request_id="request-one"):
    return service.ingest(
        Actor("admin", "tenant-demo", frozenset({"admin"}), 9999999999),
        raw=raw,
        source_type="NOTES",
        title="notes.txt",
        source_key="coordination-source",
        access_label="PUBLIC_DEMO",
        content_type="text/plain",
        idempotency_key="independent-ingest-key",
        request_id=request_id,
    )


@pytest.mark.parametrize("different_body", [False, True])
def test_independent_instances_recover_committed_ledger(
    proposal_system, monkeypatch, different_body
):
    client, graph = proposal_system
    settings = client.app.state.graph.settings
    connections = [GraphConnection(settings), GraphConnection(settings)]
    services = [SourceIngestService(settings, connection) for connection in connections]
    barrier = Barrier(2)
    original = Graph.query

    def simultaneous_publish(self, query, *args, **kwargs):
        if self.name == graph.name and query in {sources.CREATE_SOURCE, sources.UPDATE_SOURCE}:
            barrier.wait(timeout=10)
        return original(self, query, *args, **kwargs)

    monkeypatch.setattr(Graph, "query", simultaneous_publish)

    def run(index):
        try:
            return upload(
                services[index],
                raw=b"We will deliver another item."
                if different_body and index
                else b"We will deliver the integration.",
                request_id=f"request-{index}",
            )
        except SourceConflict:
            return "conflict"

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, range(2)))
        if different_body:
            assert results.count("conflict") == 1, results
        else:
            assert all(result[0] == 202 for result in results), results
            assert results[0][1]["operation_id"] == results[1][1]["operation_id"]
            assert results[0][1]["request_id"] == "request-0"
            assert results[1][1]["request_id"] == "request-1"
            with pytest.raises(SourceConflict):
                upload(services[0], raw=b"Different body")
        for label in [
            "SourceRecord",
            "SourceVersion",
            "OperationRun",
            "AuditEvent",
            "PromiseVersion",
        ]:
            assert graph.ro_query(f"MATCH (n:{label}) RETURN count(n)").result_set == [[1]]
    finally:
        for connection in connections:
            connection.close()


@pytest.mark.parametrize("damage", ["tenant", "inactive", "edge_tenant", "version_acl", "edge_acl"])
def test_source_traversal_rejects_malformed_current_version(proposal_system, damage):
    client, graph = proposal_system
    connection = client.app.state.graph
    service = SourceIngestService(connection.settings, connection)
    _, result = upload(service)
    source = result["source_id"]
    repository = GraphRepository(connection)
    version = repository.source_detail("tenant-demo", source)[0][9]
    query = {
        "tenant": "MATCH (v:SourceVersion) SET v.tenant_id='tenant-other'",
        "inactive": "MATCH ()-[e:HAS_SOURCE_VERSION]->() SET e.status='RETIRED'",
        "edge_tenant": "MATCH ()-[e:HAS_SOURCE_VERSION]->() SET e.tenant_id='tenant-other'",
        "version_acl": "MATCH (v:SourceVersion) SET v.access_label='RESTRICTED'",
        "edge_acl": "MATCH ()-[e:HAS_SOURCE_VERSION]->() SET e.access_label='RESTRICTED'",
    }[damage]
    graph.query(query)
    assert repository.source_detail("tenant-demo", source) == []
    assert repository.source_version("tenant-demo", source, version) is None
    assert repository.source_chunks("tenant-demo", source, version, None, False) == []
    # A fresh key must not treat the inaccessible current version as genesis or NO_CHANGE.
    with pytest.raises(SourceConflict):
        service.ingest(
            Actor("admin", "tenant-demo", frozenset({"admin"}), 9999999999),
            raw=b"We will deliver the integration.",
            source_type="NOTES",
            title="notes.txt",
            source_key="coordination-source",
            access_label="PUBLIC_DEMO",
            content_type="text/plain",
            idempotency_key="fresh-key-invalid-source",
            request_id="new-request",
        )
    assert graph.ro_query("MATCH (v:SourceVersion) RETURN count(v)").result_set == [[1]]


def test_audit_pagination_beyond_1000_allows_publication_and_verification(proposal_system):
    client, graph = proposal_system
    connection = client.app.state.graph
    previous = None
    events = []
    for sequence in range(1, 1002):
        payload = {
            "event_id": f"audit-seed-{sequence}",
            "tenant_id": "tenant-demo",
            "sequence": sequence,
            "prev_event_hash": previous,
            "signing_key_id": "test-key",
            "event_type": "TEST_CHECKPOINT_FREE_HISTORY",
            "payload": {},
        }
        signed = sign_audit(payload, connection.settings.signing_private_key_path)
        events.append(
            {
                "id": payload["event_id"],
                "event_type": payload["event_type"],
                "sequence": sequence,
                "previous": previous,
                "payload": signed.payload_json,
                "hash": signed.event_hash,
                "signature": signed.signature,
            }
        )
        previous = signed.event_hash
    graph.query(
        "UNWIND $events AS event CREATE (:AuditEvent {id:event.id,tenant_id:'tenant-demo',"
        "access_label:'PUBLIC_DEMO',sequence:event.sequence,prev_event_hash:event.previous,"
        "payload_json:event.payload,event_hash:event.hash,signature:event.signature,"
        "key_id:'test-key',event_type:event.event_type})",
        {"events": events},
    )
    graph.query(
        "MATCH (s:GraphState) SET s.audit_sequence=1001,s.audit_head_hash=$head,s.revision=1001",
        {"head": previous},
    )
    result = client.get("/api/audit/verify")
    assert result.status_code == 200, result.text
    assert result.json()["chain_result"] == "VALID"
    assert len(result.json()["checks"]) == 1001
    assert upload(SourceIngestService(connection.settings, connection))[0] == 202
    promise = client.get("/api/promises").json()["items"][0]["id"]
    verified = client.get(f"/api/promises/{promise}/verify")
    assert verified.status_code == 200, verified.text
    assert all(item["result"] == "PASS" for item in verified.json()["verification"]["checks"])
    graph.query("MATCH (a:AuditEvent {sequence:1000}) SET a.signature=$bad", {"bad": "A" * 86})
    assert client.get("/api/audit/verify").json()["chain_result"] == "INVALID"


def _seed_signed_audit_prefix(graph, key_path, count):
    previous = None
    events = []
    for sequence in range(1, count + 1):
        payload = {
            "event_id": f"seed-audit-{sequence}",
            "tenant_id": "tenant-demo",
            "sequence": sequence,
            "prev_event_hash": previous,
            "signing_key_id": "test-key",
            "event_type": "TEST_PREFIX",
            "payload": {},
        }
        signed = sign_audit(payload, key_path)
        events.append(
            {
                "id": payload["event_id"],
                "sequence": sequence,
                "previous": previous,
                "payload": signed.payload_json,
                "hash": signed.event_hash,
                "signature": signed.signature,
            }
        )
        previous = signed.event_hash
    graph.query(
        "UNWIND $events AS event CREATE (:AuditEvent {id:event.id,tenant_id:'tenant-demo',"
        "access_label:'PUBLIC_DEMO',sequence:event.sequence,prev_event_hash:event.previous,"
        "payload_json:event.payload,event_hash:event.hash,signature:event.signature,"
        "key_id:'test-key',event_type:'TEST_PREFIX'})",
        {"events": events},
    )
    graph.query(
        "MATCH (s:GraphState) SET s.audit_sequence=$sequence,s.audit_head_hash=$head,"
        "s.revision=$sequence",
        {"sequence": count, "head": previous},
    )


def test_source_commit_during_paginated_audit_read_retries(proposal_system, monkeypatch):
    client, graph = proposal_system
    _seed_signed_audit_prefix(graph, client.app.state.graph.settings.signing_private_key_path, 100)
    ready = Event()
    release = Event()
    original = GraphRepository._pages
    paused = False

    def pause_after_first_page(self, tenant, query, params):
        nonlocal paused
        for index, row in enumerate(original(self, tenant, query, params), 1):
            if query == sources.AUDIT_EVENTS and index == 100 and not paused:
                paused = True
                ready.set()
                assert release.wait(timeout=10)
            yield row

    monkeypatch.setattr(GraphRepository, "_pages", pause_after_first_page)

    def verify_in_peer():
        peer = TestClient(client.app)
        assert peer.post("/api/session", json={"credential": "admin-credential"}).status_code == 200
        return peer.get("/api/audit/verify")

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="audit_verifier") as pool:
        future = pool.submit(verify_in_peer)
        try:
            assert ready.wait(timeout=10)
            uploaded = client.post(
                "/api/sources/upload",
                data={"source_type": "NOTES", "access_label": "PUBLIC_DEMO"},
                files={
                    "file": ("audit-race.txt", b"We will deliver the integration.", "text/plain")
                },
                headers={"Idempotency-Key": "audit-race-upload-key"},
            )
            assert uploaded.status_code == 202, uploaded.text
        finally:
            release.set()
        verified = future.result(timeout=15)
    assert verified.status_code == 200, verified.text
    body = verified.json()
    assert body["chain_result"] == "VALID"
    assert body["checked_range"]["to_sequence"] == 101
    assert len(body["checks"]) == 101


@pytest.mark.parametrize("damage", ["signature", "chain"])
def test_stable_audit_corruption_remains_invalid(proposal_system, damage):
    client, graph = proposal_system
    for index, raw in enumerate([b"We will deliver the integration.", b"No commitment here."]):
        result = client.post(
            "/api/sources/upload",
            data={"source_type": "NOTES", "access_label": "PUBLIC_DEMO"},
            files={"file": (f"source-{index}.txt", raw, "text/plain")},
            headers={"Idempotency-Key": f"stable-corruption-key-{index}"},
        )
        assert result.status_code == 202, result.text
    if damage == "signature":
        graph.query("MATCH (a:AuditEvent {sequence:2}) SET a.signature=$bad", {"bad": "A" * 86})
    else:
        graph.query(
            "MATCH (a:AuditEvent {sequence:2}) SET a.prev_event_hash=$bad", {"bad": "0" * 64}
        )
    result = client.get("/api/audit/verify")
    assert result.status_code == 200, result.text
    assert result.json()["chain_result"] == "INVALID"
    promise = client.get("/api/promises").json()["items"][0]["id"]
    verification = client.get(f"/api/promises/{promise}/verify")
    assert verification.status_code == 200, verification.text
    checks = verification.json()["verification"]["checks"]
    assert any(check["code"] == "AUDIT_CHAIN" and check["result"] == "FAIL" for check in checks)


def test_continuous_audit_boundaries_return_indeterminate(proposal_system, monkeypatch):
    client, _ = proposal_system
    original = GraphRepository.audit_boundary
    reads = 0

    def moving_boundary(self, tenant):
        nonlocal reads
        reads += 1
        boundary = original(self, tenant)
        return [boundary[0], boundary[1], boundary[2] + reads]

    monkeypatch.setattr(GraphRepository, "audit_boundary", moving_boundary)
    result = client.get("/api/audit/verify")
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["chain_result"] == "INDETERMINATE"
    assert body["checks"] == []
    assert body["checked_range"] == {"from_sequence": 0, "to_sequence": 0}
    assert "changed during audit verification" in body["limitations"][-1]


def test_source_update_can_issue_valid_genesis_receipt(proposal_system):
    client, graph = proposal_system
    for index, raw in enumerate([b"A neutral note.", b"We will deliver the integration."]):
        result = client.post(
            "/api/sources/upload",
            data={
                "source_type": "NOTES",
                "source_key": "semantic-source",
                "access_label": "PUBLIC_DEMO",
            },
            files={"file": ("semantic.txt", raw, "text/plain")},
            headers={"Idempotency-Key": f"semantic-genesis-key-{index}"},
        )
        assert result.status_code == 202, result.text
    assert graph.ro_query("MATCH (a:AuditEvent {sequence:2}) RETURN a.event_type").result_set == [
        ["SOURCE_UPDATED"]
    ]
    promise = client.get("/api/promises").json()["items"][0]["id"]
    verified = client.get(f"/api/promises/{promise}/verify")
    assert verified.status_code == 200, verified.text
    assert all(check["result"] == "PASS" for check in verified.json()["verification"]["checks"])


def test_source_publication_rejects_changed_audit_head(proposal_system, monkeypatch):
    client, graph = proposal_system
    original = Graph.query
    changed = False

    def change_head_before_upload(self, query, *args, **kwargs):
        nonlocal changed
        if self.name == graph.name and query == sources.CREATE_SOURCE and not changed:
            changed = True
            original(self, "MATCH (s:GraphState) SET s.audit_head_hash=$hash", {"hash": "0" * 64})
        return original(self, query, *args, **kwargs)

    monkeypatch.setattr(Graph, "query", change_head_before_upload)
    result = client.post(
        "/api/sources/upload",
        data={"source_type": "NOTES", "access_label": "PUBLIC_DEMO"},
        files={"file": ("head-change.txt", b"We will deliver the integration.", "text/plain")},
        headers={"Idempotency-Key": "head-change-upload-key"},
    )
    assert result.status_code == 409, result.text
    assert changed
    assert graph.ro_query("MATCH (r:SourceRecord) RETURN count(r)").result_set == [[0]]
    assert graph.ro_query("MATCH (a:AuditEvent) RETURN count(a)").result_set == [[0]]
