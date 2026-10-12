from typing import Literal

from pydantic import Field

from app.models.api import EvidenceRef
from app.models.common import Id, SafeInt, StrictModel, Timestamp
from app.promise_seal.models import ReceiptEnvelope


class Freshness(StrictModel):
    level: Literal["FRESH", "AGING", "STALE", "UNKNOWN"]
    as_of: Timestamp | None
    evaluated_at: Timestamp
    threshold_seconds: SafeInt
    source_version_ids: list[Id]


class PromiseSummary(StrictModel):
    id: Id
    current_version_id: Id
    revision: SafeInt
    current_state: Literal[
        "PROPOSED", "NEEDS_REVIEW", "CONFIRMED", "DISPUTED", "SUPERSEDED", "FULFILLED", "REJECTED"
    ]
    receipt_standing: Literal["ACTIVE", "SUPERSEDED", "REVOKED"]
    customer_id: Id | None
    project_id: Id | None
    deliverable: str = Field(min_length=1, max_length=2000)
    deadline: str | None
    scope_status: str
    risk_flags: list[str]
    freshness: Freshness
    open_conflict_ids: list[Id]


class PromiseCollection(StrictModel):
    request_id: str
    items: list[PromiseSummary]
    next_cursor: str | None


class VersionSummary(StrictModel):
    receipt_id: Id
    version: SafeInt
    status_at_issuance: str
    standing: Literal["ACTIVE", "SUPERSEDED", "REVOKED"]


class ScopeAssessment(StrictModel):
    status: str
    claim: str
    clause_ids: list[Id]
    evidence_refs: list[EvidenceRef]
    conflict_ids: list[Id]
    missing_evidence: list[str]
    assessment_kind: Literal["LLM_REVIEWED", "DETERMINISTIC_RULE"]
    reviewed_by: Id | None


class GraphPath(StrictModel):
    path_id: Id
    template_id: Id
    node_ids: list[Id]
    edge_ids: list[Id]
    graph_revision: SafeInt
    evidence_ref_ids: list[Id]


class PromiseDetail(StrictModel):
    request_id: str
    promise: PromiseSummary
    receipt: ReceiptEnvelope
    versions: list[VersionSummary]
    evidence: list[EvidenceRef]
    scope_assessment: ScopeAssessment
    calculations: list[dict]
    related_issue_ids: list[Id]
    milestone_ids: list[Id]
    conflicts: list[dict]
    graph_paths: list[GraphPath]


class VerificationCheck(StrictModel):
    code: str
    result: Literal["PASS", "FAIL", "UNAVAILABLE"]
    field: str | None = None
    reason: str | None = None


class SourceVerification(StrictModel):
    evidence_ref_id: Id
    result: Literal["MATCH", "MISMATCH", "UNAVAILABLE"]
    reason: str


class Verification(StrictModel):
    integrity: Literal["VALID", "INVALID", "UNSIGNED", "INDETERMINATE"]
    standing: Literal["ACTIVE", "SUPERSEDED", "REVOKED"]
    checked_at: Timestamp
    checks: list[VerificationCheck]
    source_results: list[SourceVerification]
    key_trust: Literal["TRUSTED", "RETIRED", "COMPROMISED", "UNKNOWN"]
    eligible_for_action: bool


class VerifyResponse(StrictModel):
    request_id: str
    receipt_id: Id
    verification: Verification
