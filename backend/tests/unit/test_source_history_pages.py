from unittest.mock import Mock

import pytest

from app.graph.connection import GraphUnavailable
from app.graph.repository import GraphRepository


def test_source_history_reads_all_pages_with_revision_guard():
    repository = GraphRepository(Mock())
    repository.graph_revision = Mock(return_value=7)
    repository._read = Mock(side_effect=[list(range(100)), list(range(100, 200)), [200]])
    rows = repository.source_detail("tenant-demo", "source-demo")
    assert len(rows) == 201
    assert rows[-1] == 200
    assert [call.args[2]["offset"] for call in repository._read.call_args_list] == [0, 100, 200]
    assert all(call.args[2]["limit"] == 100 for call in repository._read.call_args_list)


def test_source_history_retries_concurrent_change():
    repository = GraphRepository(Mock())
    repository.graph_revision = Mock(side_effect=[1, 2, 2, 2])
    repository._read = Mock(side_effect=[["old"], ["new"]])
    assert repository.source_detail("tenant-demo", "source-demo") == ["new"]


def test_source_history_fails_closed_under_continuous_writes():
    repository = GraphRepository(Mock())
    repository.graph_revision = Mock(side_effect=range(6))
    repository._read = Mock(return_value=[])
    with pytest.raises(GraphUnavailable):
        repository.source_detail("tenant-demo", "source-demo")
