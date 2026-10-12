from typing import Literal

from app.models.api import EvidenceRef
from app.models.common import Digest, Id, SafeInt, StrictModel, Timestamp


class UploadAccepted(StrictModel):
    request_id: str
    operation_id: Id
    source_id: Id
    status_url: str


class UploadNoChange(StrictModel):
    request_id: str
    source_id: Id
    source_version_id: Id
    outcome: Literal["NO_CHANGE"]


class SourceSummary(StrictModel):
    id: Id
    source_type: str
    title: str
    current_version_id: Id
    source_updated_at: Timestamp | None
    ingested_at: Timestamp
    content_hash: Digest
    retention_state: str
    parse_status: str
    mode: Literal["IMPORT", "MOCK", "LIVE"]


class SourceVersionResponse(StrictModel):
    id: Id
    source_hash: Digest
    representation_hash: Digest
    availability: Literal["AVAILABLE", "DELETED", "MISSING"]


class SourceVersionSummary(StrictModel):
    id: Id
    version: SafeInt
    source_updated_at: Timestamp | None
    availability: Literal["AVAILABLE", "DELETED", "MISSING"]


class SourceDetail(StrictModel):
    request_id: str
    source: SourceSummary
    version: SourceVersionResponse
    snippets: list[EvidenceRef]
    versions: list[SourceVersionSummary]


class OperationProgress(StrictModel):
    completed: SafeInt
    total: SafeInt | None


class Operation(StrictModel):
    id: Id
    kind: str
    status: str
    phase: str
    created_at: Timestamp
    started_at: Timestamp | None
    finished_at: Timestamp | None
    result: dict | None
    errors: list[dict]
    progress: OperationProgress


class OperationResponse(StrictModel):
    request_id: str
    operation: Operation
