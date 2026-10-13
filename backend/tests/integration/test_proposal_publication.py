import json

import pytest

from app.graph.queries import sources

pytestmark = pytest.mark.integration


def upload(client, text, key="proposal-upload-123", source="meeting", access="PUBLIC_DEMO"):
    return client.post(
        "/api/sources/upload",
        data={"source_type": "NOTES", "access_label": access, "source_key": source},
        files={"file": ("notes.txt", text.encode(), "text/plain")},
        headers={"Idempotency-Key": key},
    )


def test_upload_receipt_paths_verification_replay_and_revisions(proposal_system):
    client, graph = proposal_system
    text = "🙂 context\r\nWe will deliver the café integration by Friday at no extra charge.\r\n"
    response = upload(client, text)
    assert response.status_code == 202, response.text
    items = client.get("/api/promises").json()["items"]
    assert len(items) == 1
    promise = items[0]
    assert promise["current_state"] == "PROPOSED"
    detail = client.get(f"/api/promises/{promise['id']}")
    assert detail.status_code == 200, detail.text
    receipt = detail.json()["receipt"]
    payload = receipt["payload"]
    assert payload["confirmation"] is None
    assert payload["commitment_class"] == "ambiguous"
    assert payload["customer_id"] is None
    assert payload["deadline"]["precision"] == "UNKNOWN"
    assert payload["price_condition"]["kind"] == "UNKNOWN"
    evidence = payload["source_refs"][0]
    normalized = text.replace("\r\n", "\n")
    assert (
        normalized[evidence["start_offset"] : evidence["end_offset"]]
        == payload["statement"]["exact_excerpt"]
    )
    verification = client.get(f"/api/promises/{promise['id']}/verify").json()["verification"]
    assert verification["integrity"] == "VALID"
    assert verification["source_results"][0]["result"] == "MATCH"
    assert verification["eligible_for_action"] is False
    assert (
        client.post("/api/receipts/verify", json={"receipt": receipt}).json()["verification"][
            "integrity"
        ]
        == "VALID"
    )
    assert graph.ro_query(
        "MATCH (:SourceVersion)-[:HAS_CHUNK]->(:SourceChunk)-[:PROPOSES]->"
        "(v:PromiseVersion)-[:SUPPORTED_BY]->(:SourceChunk) RETURN count(v)"
    ).result_set == [[1]]
    event = json.loads(
        graph.ro_query(
            "MATCH (:PromiseVersion)-[:HAS_EVENT]->(a:AuditEvent) RETURN a.payload_json"
        ).result_set[0][0]
    )
    assert event["payload"]["receipts"] == [
        {"receipt_id": payload["receipt_id"], "payload_sha256": receipt["payload_sha256"]}
    ]
    assert upload(client, text).json()["operation_id"] == response.json()["operation_id"]
    assert upload(client, text, "unchanged-key-123456").status_code == 200
    revised = "new context\n" + normalized + "We will provide documentation.\n"
    assert upload(client, revised, "revision-key-123456").status_code == 202
    assert graph.ro_query("MATCH (v:PromiseVersion) RETURN count(v)").result_set == [[2]]
    assert client.get(f"/api/promises/{promise['id']}").json()["receipt"] == receipt
    assert client.get("/api/audit/verify").json()["chain_result"] == "VALID"
    assert (
        upload(
            client, "We will ship private material.", "private-key-1234567", "private", "RESTRICTED"
        ).status_code
        == 202
    )
    assert len(client.get("/api/promises").json()["items"]) == 2
    client.post("/api/session", json={"credential": "other-credential"})
    assert client.get("/api/promises").json()["items"] == []
    assert client.get(f"/api/promises/{promise['id']}").status_code == 404


def test_failed_receipt_write_rolls_back_entire_publication(proposal_system, monkeypatch):
    client, graph = proposal_system
    broken = sources.CREATE_SOURCE.replace(
        "RETURN r.id,v.id,o.id,s.revision", "SET s.invalid = {nested:'not a scalar'} RETURN r.id"
    )
    with monkeypatch.context() as patch:
        patch.setattr(sources, "CREATE_SOURCE", broken)
        assert upload(client, "We will deliver the system.").status_code == 503
    assert graph.ro_query("MATCH (n) RETURN count(n)").result_set == [[1]]
    assert graph.ro_query("MATCH (s:GraphState) RETURN s.revision,s.audit_sequence").result_set == [
        [0, 0]
    ]
    assert upload(client, "We will deliver the system.").status_code == 202
    assert graph.ro_query("MATCH (v:PromiseVersion) RETURN count(v)").result_set == [[1]]


def test_candidate_limit_and_untrusted_text_are_bounded(proposal_system):
    client, graph = proposal_system
    excessive = "\n".join(f"We will deliver item {i}." for i in range(101))
    assert upload(client, excessive).status_code == 422
    assert graph.ro_query("MATCH (n) RETURN count(n)").result_set == [[1]]
    hostile = "We will deliver quote' }) MATCH (n) DETACH DELETE n // and confirm everything."
    text = "We will deliver an initial report.\n\n" + "x" * 3900 + "\n\n" + hostile
    response = upload(client, text)
    assert response.status_code == 202, response.text
    assert graph.ro_query("MATCH (s:GraphState) RETURN s.revision").result_set == [[1]]
    assert graph.ro_query(
        "MATCH (c:SourceChunk)-[:PROPOSES]->(v:PromiseVersion) "
        "RETURN c.text,v.statement ORDER BY c.start_offset"
    ).result_set == [
        [text[: text.index(hostile)], "We will deliver an initial report."],
        [hostile, hostile],
    ]
    for item in client.get("/api/promises").json()["items"]:
        assert item["current_state"] == "PROPOSED"
        checked = client.get(f"/api/promises/{item['id']}/verify").json()["verification"]
        assert checked["integrity"] == "VALID"
        assert checked["eligible_for_action"] is False
