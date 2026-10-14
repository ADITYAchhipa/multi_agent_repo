import pytest

pytestmark = pytest.mark.integration


def setup(client, graph):
    # Also exercise the router before the composition-root integration lands.
    if "/api/simulations" not in client.app.openapi()["paths"]:
        from app.api.scenarios import router
        from app.graph.repository import GraphRepository

        connection = client.app.state.graph
        client.app.include_router(router(connection.settings, GraphRepository(connection)))
    response = client.post(
        "/api/sources/upload",
        data={"source_type": "NOTES", "access_label": "PUBLIC_DEMO"},
        files={"file": ("scenario.txt", b"We will deliver the dashboard.", "text/plain")},
        headers={"Idempotency-Key": "scenario-upload-0001"},
    )
    assert response.status_code == 202, response.text
    promise = client.get("/api/promises").json()["items"][0]["id"]
    revision = graph.ro_query("MATCH (s:GraphState) RETURN s.revision").result_set[0][0]
    return {
        "promise_id": promise,
        "base_graph_revision": revision,
        "question": "Compare baseline",
        "scenario_types": ["AS_REQUESTED"],
        "financials": {
            "scope_id": "dashboard",
            "currency": "USD",
            "required_hours": "8",
            "available_hours": "3",
            "hourly_cost": "100",
        },
    }


def test_scenario_atomic_replay_read_isolation_and_audit(proposal_system):
    client, graph = proposal_system
    body = setup(client, graph)
    headers = {"Idempotency-Key": "scenario-create-0001"}
    response = client.post("/api/simulations", json=body, headers=headers)
    assert response.status_code == 201, response.text
    result = response.json()["results"][0]
    assert result["feasibility"] == "INFEASIBLE"
    assert result["calculations"][1]["value"] == "5"
    sid = result["id"]
    read = client.get(f"/api/simulations/{sid}")
    assert read.status_code == 200, read.text
    assert read.json()["scenario"] == result
    replay = client.post("/api/simulations", json=body, headers=headers)
    assert replay.status_code == 201, replay.text
    assert replay.json()["results"] == response.json()["results"]
    assert graph.ro_query("MATCH (n:Scenario) RETURN count(n)").result_set == [[1]]
    conflict = client.post(
        "/api/simulations", json={**body, "question": "changed"}, headers=headers
    )
    assert conflict.status_code == 409
    stale = client.post(
        "/api/simulations", json=body, headers={"Idempotency-Key": "scenario-create-0002"}
    )
    assert stale.status_code == 409
    assert client.get("/api/audit/verify").json()["chain_result"] == "VALID"
    client.post("/api/session", json={"credential": "other-credential"})
    assert client.get(f"/api/simulations/{sid}").status_code == 404


def test_multiple_scenarios_and_parent(proposal_system):
    client, graph = proposal_system
    body = setup(client, graph)
    body["scenario_types"] = ["AS_REQUESTED", "CHANGE_ORDER_OR_EXTRA_CAPACITY"]
    response = client.post(
        "/api/simulations", json=body, headers={"Idempotency-Key": "scenario-multiple-01"}
    )
    assert response.status_code == 201, response.text
    assert len(response.json()["scenario_ids"]) == 2
    body["parent_scenario_id"] = response.json()["scenario_ids"][0]
    body["base_graph_revision"] += 1
    child = client.post(
        "/api/simulations", json=body, headers={"Idempotency-Key": "scenario-multiple-02"}
    )
    assert child.status_code == 201, child.text
    assert client.get("/api/audit/verify").json()["chain_result"] == "VALID"
    assert (
        client.get("/api/simulations/" + body["parent_scenario_id"]).json()["scenario"]["status"]
        == "STALE"
    )


def test_concurrent_scenario_replay_publishes_once(proposal_system):
    from concurrent.futures import ThreadPoolExecutor

    client, graph = proposal_system
    body = setup(client, graph)

    def create(_):
        return client.post(
            "/api/simulations", json=body, headers={"Idempotency-Key": "scenario-concurrent-1"}
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(create, range(2)))
    assert [r.status_code for r in responses] == [201, 201]
    assert responses[0].json()["results"] == responses[1].json()["results"]
    assert graph.ro_query("MATCH (n:Scenario) RETURN count(n)").result_set == [[1]]
    assert client.get("/api/audit/verify").json()["chain_result"] == "VALID"


def test_source_access_change_blocks_scenario_replay(proposal_system):
    client, graph = proposal_system
    body = setup(client, graph)
    headers = {"Idempotency-Key": "scenario-retention-1"}
    response = client.post("/api/simulations", json=body, headers=headers)
    assert response.status_code == 201
    sid = response.json()["scenario_ids"][0]
    graph.query("MATCH (s:SourceRecord) SET s.access_label='RESTRICTED'")
    assert client.get("/api/simulations/" + sid).status_code == 404
    assert client.post("/api/simulations", json=body, headers=headers).status_code == 404
