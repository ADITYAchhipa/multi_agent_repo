"""Destructive only to generated spike_* graphs on an explicitly opted-in test server."""

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from falkordb import FalkorDB
from redis.exceptions import ResponseError

pytestmark = pytest.mark.integration


@pytest.fixture
def db():
    if os.environ.get("RUN_FALKORDB_INTEGRATION") != "1":
        pytest.skip("set RUN_FALKORDB_INTEGRATION=1 with a real disposable FalkorDB server")
    client = FalkorDB(
        host=os.environ.get("FALKORDB_TEST_HOST", "127.0.0.1"),
        port=int(os.environ.get("FALKORDB_TEST_PORT", "16379")),
        socket_timeout=3,
        socket_connect_timeout=3,
    )
    yield client
    client.close()


@pytest.fixture
def graph(db):
    graph = db.select_graph("spike_" + uuid4().hex)
    graph.query("CREATE (:GraphState {id:'graph-state', revision:0})")
    yield graph
    graph.delete()


def test_binding_readonly_and_graph_selection(graph, db):
    hostile = "quote' }) MATCH (n) DETACH DELETE n //"
    assert graph.ro_query("RETURN $value", {"value": hostile}, timeout=2000).result_set == [
        [hostile]
    ]
    with pytest.raises(ResponseError):
        graph.ro_query("CREATE (:Promise {id:'forbidden'})", timeout=2000)
    assert graph.ro_query("MATCH (p:Promise) RETURN count(p)").result_set == [[0]]
    assert graph.name in db.list_graphs()


def test_index_and_tenant_scoped_path(graph):
    graph.query("CREATE INDEX FOR (p:Promise) ON (p.id)")
    graph.query(
        "CREATE (p:Promise {id:$id, tenant_id:$tenant})"
        "-[:HAS_VERSION {id:'edge-1',tenant_id:$tenant}]->"
        "(:PromiseVersion {id:'receipt-1',tenant_id:$tenant})",
        {"id": "promise-1", "tenant": "tenant-a"},
    )
    query = (
        "MATCH (p:Promise {id:$id, tenant_id:$tenant})-[e:HAS_VERSION]->(v:PromiseVersion) "
        "WHERE e.tenant_id=$tenant AND v.tenant_id=$tenant "
        "RETURN p.id,e.id,v.id LIMIT 60"
    )
    assert graph.ro_query(query, {"id": "promise-1", "tenant": "tenant-a"}).result_set == [
        ["promise-1", "edge-1", "receipt-1"]
    ]
    assert graph.ro_query(query, {"id": "promise-1", "tenant": "tenant-b"}).result_set == []


def test_conditional_publication_has_one_winner(graph):
    query = (
        "MATCH (s:GraphState {id:'graph-state'}) WHERE s.revision=$expected "
        "SET s.revision=s.revision+1 CREATE (:Promise {id:$id}) RETURN s.revision"
    )

    def claim(i):
        return graph.query(query, {"expected": 0, "id": f"candidate-{i}"}).result_set

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(claim, range(4)))
    assert sum(bool(r) for r in results) == 1
    assert graph.ro_query("MATCH (p:Promise) RETURN count(p)").result_set == [[1]]


def test_failed_statement_does_not_publish_partial_nodes(graph):
    # Runtime type error after a write: S01 must establish all-or-nothing behavior.
    with pytest.raises(ResponseError):
        graph.query(
            "CREATE (p:Promise {id:'rollback'}) SET p.invalid = $bad",
            {"bad": {"nested": "map-property-not-supported"}},
        )
    assert graph.ro_query("MATCH (p:Promise {id:'rollback'}) RETURN count(p)").result_set == [[0]]
