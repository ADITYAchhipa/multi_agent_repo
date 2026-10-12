from types import SimpleNamespace
from unittest.mock import Mock

from redis.exceptions import ConnectionError

from app.config import Settings
from app.graph.connection import GraphConnection


def test_client_readiness_close_and_no_implicit_graph_creation(monkeypatch):
    client = Mock()
    client.list_graphs.return_value = []
    constructor = Mock(return_value=client)
    monkeypatch.setattr("app.graph.connection.FalkorDB", constructor)
    connection = GraphConnection(Settings())
    assert connection.ready() is False
    client.select_graph.assert_not_called()
    client.list_graphs.return_value = ["company_demo"]
    client.select_graph.return_value.ro_query.return_value = SimpleNamespace(result_set=[[1]])
    assert connection.ready() is True
    client.select_graph.return_value.ro_query.assert_called_once_with(
        "RETURN $probe", params={"probe": 1}, timeout=2000
    )
    assert constructor.call_args.kwargs["socket_connect_timeout"] == 3
    connection.close()
    connection.close()
    client.close.assert_called_once()


def test_offline_does_not_surface_driver_secrets(monkeypatch):
    constructor = Mock(side_effect=ConnectionError("secret-password-canary"))
    monkeypatch.setattr("app.graph.connection.FalkorDB", constructor)
    connection = GraphConnection(Settings())
    assert connection.ready() is False
    connection.close()
