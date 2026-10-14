import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from falkordb import FalkorDB
from fastapi import HTTPException

from app.auth import Actor
from app.graph.repository import GraphRepository
from app.services.knowledge import KnowledgeService


@pytest.fixture
def knowledge_graph():
    if os.environ.get("RUN_FALKORDB_INTEGRATION") != "1":
        pytest.skip("requires disposable FalkorDB")
    db = FalkorDB(host="127.0.0.1", port=16379)
    graph = db.select_graph("spike_knowledge_" + uuid4().hex)

    class Connection:
        settings = SimpleNamespace(falkordb_query_timeout_ms=2000)

        def graph_for_tenant(self, tenant):
            return graph

    class Artifacts:
        def read(self, tenant, digest, kind):
            if digest == "good":
                return b"We will deliver the rocket tomorrow."
            raise FileNotFoundError

    service = KnowledgeService(GraphRepository(Connection()), Artifacts())
    try:
        yield graph, service
    finally:
        graph.delete()
        db.close()


def test_graph_filters_every_edge_and_node(knowledge_graph):
    graph, service = knowledge_graph
    graph.query("""
        CREATE (p:Promise {id:'p',tenant_id:'t',access_label:'PUBLIC_DEMO'}),
               (v:PromiseVersion {id:'v',tenant_id:'t',access_label:'PUBLIC_DEMO'}),
               (x:PromiseVersion {id:'x',tenant_id:'other',access_label:'PUBLIC_DEMO'}),
               (s:PromiseVersion {id:'s',tenant_id:'t',access_label:'RESTRICTED'}),
               (z:PromiseVersion {id:'z',tenant_id:'t',access_label:'PUBLIC_DEMO'}),
               (p)-[:HAS_VERSION {id:'e',tenant_id:'t',access_label:'PUBLIC_DEMO',
                 status:'ACTIVE'}]->(v),
               (p)-[:HAS_VERSION {id:'x',tenant_id:'t',access_label:'PUBLIC_DEMO',
                 status:'ACTIVE'}]->(x),
               (p)-[:HAS_VERSION {id:'s',tenant_id:'t',access_label:'PUBLIC_DEMO',
                 status:'ACTIVE'}]->(s),
               (p)-[:HAS_VERSION {id:'z',tenant_id:'t',access_label:'RESTRICTED',
                 status:'ACTIVE'}]->(z)
    """)
    actor = Actor("actor", "t", frozenset({"admin"}), 0)
    result = service.graph(actor, "p")
    assert {n["id"] for n in result["nodes"]} == {"p", "v"}
    assert result["edges"] == [{"id": "e", "type": "HAS_VERSION", "source": "p", "target": "v"}]
    with pytest.raises(HTTPException):
        service.graph(actor, "s")


def test_grounded_quotes_require_retained_artifacts_and_trace_owner(knowledge_graph):
    graph, service = knowledge_graph
    graph.query("""
        CREATE (s:SourceRecord {id:'s',tenant_id:'t',access_label:'PUBLIC_DEMO',
                 retention_state:'ACTIVE',current_version_id:'v',parse_status:'PARSED'}),
               (v:SourceVersion {id:'v',tenant_id:'t',access_label:'PUBLIC_DEMO',
                 availability:'AVAILABLE',representation_hash:'good'}),
               (c:SourceChunk {id:'c',source_id:'s',source_version_id:'v',tenant_id:'t',
                 access_label:'PUBLIC_DEMO',text:'We will deliver the rocket tomorrow.',
                 start_offset:0,end_offset:36}),
               (s)-[:HAS_SOURCE_VERSION {tenant_id:'t',access_label:'PUBLIC_DEMO',
                 status:'ACTIVE'}]->(v),
               (v)-[:HAS_CHUNK {tenant_id:'t',access_label:'PUBLIC_DEMO',
                 status:'ACTIVE'}]->(c),
               (:OperationRun {id:'op',tenant_id:'t',request_id:'req',requested_by:'owner',
                 access_label:'PUBLIC_DEMO',kind:'IMPORT',status:'SUCCEEDED',phase:'PUBLISHED'})
    """)
    actor = Actor("owner", "t", frozenset({"viewer"}), 0)
    assert service.ask(actor, "rocket")["evidence"][0]["evidence_ref_id"] == "c"
    assert service.ask(actor, "elephant")["abstained"] is True
    assert service.trace(actor, "req")["operations"][0]["id"] == "op"
    with pytest.raises(HTTPException):
        service.trace(Actor("stranger", "t", frozenset(), 0), "req")
    graph.query("MATCH (v:SourceVersion) SET v.representation_hash='missing'")
    assert service.ask(actor, "rocket")["abstained"] is True
    assert service.health(actor)["sources"][0]["id"] == "s"
