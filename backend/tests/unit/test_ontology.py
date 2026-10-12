from pathlib import Path

import pytest

from app.graph.ontology import (
    NODE_LABELS,
    RELATION_ENDPOINTS,
    normalize_relation,
    validate_relationship,
)


def test_matrix_matches_frozen_document():
    spec = (Path(__file__).resolve().parents[3] / "docs/FALKORDB_SCHEMA.md").read_text()
    section = spec.split("## 3. Closed relationship endpoint matrix")[1].split("## 4.")[0]
    expected = {}
    for line in section.splitlines():
        if line.startswith("| ") and " → " in line and not line.startswith("| Type |"):
            cells = line.split("|")
            relation = cells[1].strip()
            source, target = cells[2].strip().split(" → ")
            expected[relation] = (set(source.split(", ")), set(target.split(", ")))
    assert RELATION_ENDPOINTS == expected
    assert "Task" not in NODE_LABELS and "Team" in NODE_LABELS


@pytest.mark.parametrize(
    "relation,source,target",
    [
        ("CAN_DO_MAGIC", "Person", "JiraIssue"),
        ("BLOCKS", "JiraIssue", "JiraIssue"),
        ("DEPENDS_ON", "Project", "Task"),
        ("HAS_CHUNK", "SourceRecord", "SourceChunk"),
        ("ASSIGNED_TO", "Person", "JiraIssue"),
        ("ASSERTED_BY", "PromiseVersion", "Person"),
    ],
)
def test_unknown_and_invalid_endpoints_rejected(relation, source, target):
    with pytest.raises(ValueError):
        validate_relationship(relation, source, target)


def test_normalization_is_explicit_and_directional():
    assert normalize_relation("blocks") == ("DEPENDS_ON", True)
    assert normalize_relation("assignee") == ("ASSIGNED_TO", False)
    with pytest.raises(ValueError):
        normalize_relation("related to")
