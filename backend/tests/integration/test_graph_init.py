import os
from uuid import uuid4

import pytest
from falkordb import FalkorDB

from app.config import Settings
from app.scripts.init_graph import initialize

pytestmark = pytest.mark.integration


def test_explicit_graph_initialization_refuses_existing_graph():
    if os.environ.get("RUN_FALKORDB_INTEGRATION") != "1":
        pytest.skip("set RUN_FALKORDB_INTEGRATION=1 with a real disposable FalkorDB server")
    name = "spike_" + uuid4().hex
    client = FalkorDB(host="127.0.0.1", port=16379)
    try:
        settings = Settings(
            falkordb_port=16379,
            falkordb_graph=name,
            tenant_graphs={"tenant-demo": name},
        )
        assert initialize(settings, "tenant-demo") == name
        graph = client.select_graph(name)
        assert graph.ro_query(
            "MATCH (s:GraphState {tenant_id:'tenant-demo'}) "
            "RETURN s.revision,s.ontology_version,s.policy_version"
        ).result_set == [[0, "v1", "v1"]]
        with pytest.raises(ValueError, match="already exists"):
            initialize(settings, "tenant-demo")
        assert graph.ro_query("MATCH (s:GraphState) RETURN count(s)").result_set == [[1]]
    finally:
        if name in client.list_graphs():
            client.select_graph(name).delete()
        client.close()
