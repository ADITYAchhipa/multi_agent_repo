"""Closed ontology v1 from docs/FALKORDB_SCHEMA.md; no database writes here."""

ONTOLOGY_VERSION = "1"

RELATION_ENDPOINTS = {
    "HAS_CONTRACT": ({"Customer"}, {"Contract"}),
    "HAS_CLAUSE": ({"Contract"}, {"ContractClause"}),
    "FOR_CUSTOMER": ({"Project"}, {"Customer"}),
    "PARTICIPATED_IN": ({"Person"}, {"Meeting"}),
    "HAS_SOURCE": (
        {"Meeting", "Contract", "Project", "JiraIssue", "PromiseVersion", "ChangeOrder"},
        {"SourceRecord"},
    ),
    "HAS_SOURCE_VERSION": ({"SourceRecord"}, {"SourceVersion"}),
    "HAS_CHUNK": ({"SourceVersion"}, {"SourceChunk"}),
    "MENTIONED_IN": (
        {"Customer", "Person", "Project", "JiraIssue", "Contract", "PromiseVersion"},
        {"SourceChunk"},
    ),
    "SPOKEN_BY": ({"SourceChunk"}, {"Person"}),
    "PROPOSES": ({"SourceChunk"}, {"PromiseVersion"}),
    "HAS_VERSION": ({"Promise"}, {"PromiseVersion"}),
    "SUPERSEDES": ({"PromiseVersion"}, {"PromiseVersion"}),
    "ASSERTED_BY": ({"PromiseVersion"}, {"SourceRecord"}),
    "ABOUT_CUSTOMER": ({"PromiseVersion"}, {"Customer"}),
    "ABOUT_PROJECT": ({"PromiseVersion"}, {"Project"}),
    "SUPPORTED_BY": ({"PromiseVersion"}, {"SourceChunk", "ContractClause", "SourceVersion"}),
    "POSSIBLY_COVERED_BY": ({"PromiseVersion"}, {"ContractClause"}),
    "CONFLICTS_WITH": (
        {"PromiseVersion", "ContractClause"},
        {"PromiseVersion", "ContractClause", "SourceChunk"},
    ),
    "TRACKED_BY": ({"PromiseVersion"}, {"JiraIssue"}),
    "IMPLEMENTED_BY": ({"PromiseVersion"}, {"JiraIssue"}),
    "ASSIGNED_TO": ({"JiraIssue"}, {"Person"}),
    "DEPENDS_ON": ({"JiraIssue"}, {"JiraIssue"}),
    "HAS_WORKLOAD": ({"Person"}, {"WorkloadSnapshot"}),
    "USES_RATE": ({"Person"}, {"RateCard"}),
    "HAS_MILESTONE": ({"Contract", "Project"}, {"InvoiceMilestone"}),
    "REQUIRES": ({"InvoiceMilestone"}, {"JiraIssue", "AcceptanceRequirement"}),
    "SATISFIED_BY": ({"AcceptanceRequirement"}, {"SourceVersion"}),
    "AFFECTS": ({"JiraIssue", "PromiseVersion"}, {"InvoiceMilestone", "Project", "Customer"}),
    "HAS_CHANGE_ORDER": ({"Contract"}, {"ChangeOrder"}),
    "APPROVED_BY": ({"ChangeOrder", "ActionProposal"}, {"Person"}),
    "HAS_ACTION": ({"Scenario"}, {"ActionProposal"}),
    "EVIDENCED_BY": (
        {"ActionProposal"},
        {"SourceChunk", "SourceVersion", "PromiseVersion", "JiraIssue", "ContractClause"},
    ),
    "HAS_APPROVAL": ({"ActionProposal"}, {"Approval"}),
    "HAS_EVENT": (
        {
            "Promise",
            "PromiseVersion",
            "ActionProposal",
            "Conflict",
            "SourceRecord",
            "OperationRun",
            "GraphState",
        },
        {"AuditEvent"},
    ),
    "HAS_FINDING": (
        {
            "SourceRecord",
            "SourceVersion",
            "SourceChunk",
            "Person",
            "Customer",
            "Project",
            "JiraIssue",
            "Contract",
            "ContractClause",
            "Promise",
            "PromiseVersion",
            "Scenario",
            "ActionProposal",
            "InvoiceMilestone",
            "AcceptanceRequirement",
            "OperationRun",
        },
        {"KnowledgeFinding"},
    ),
}
NODE_LABELS = frozenset(
    {"Team"} | {label for pair in RELATION_ENDPOINTS.values() for end in pair for label in end}
)


def validate_relationship(relation: str, source_label: str, target_label: str) -> None:
    endpoints = RELATION_ENDPOINTS.get(relation)
    if endpoints is None or source_label not in endpoints[0] or target_label not in endpoints[1]:
        raise ValueError("relationship or endpoint labels violate ontology v1")


def normalize_relation(relation: str) -> tuple[str, bool]:
    """Return canonical relation and whether caller must reverse candidate endpoints."""
    if relation in RELATION_ENDPOINTS:
        return relation, False
    aliases = {
        "assigned to": ("ASSIGNED_TO", False),
        "assignee": ("ASSIGNED_TO", False),
        "requires task": ("DEPENDS_ON", False),
        "depends on": ("DEPENDS_ON", False),
        "blocks": ("DEPENDS_ON", True),
        "mentioned": ("MENTIONED_IN", False),
    }
    if relation not in aliases:
        raise ValueError("unknown relationship candidate requires review")
    return aliases[relation]
