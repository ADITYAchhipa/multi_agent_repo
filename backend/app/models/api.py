from typing import Literal, Self

from pydantic import Field, model_validator

from app.models.common import Digest, Id, SafeInt, StrictModel, Timestamp


class EvidenceRef(StrictModel):
    evidence_ref_id: Id
    source_id: Id
    source_version_id: Id
    source_hash: Digest
    representation_hash: Digest
    origin_reference: str = Field(min_length=1, max_length=512)
    quote: str | None = Field(max_length=20000)
    start_offset: SafeInt | None
    end_offset: SafeInt | None
    start_ms: SafeInt | None
    end_ms: SafeInt | None
    structured_pointer: str | None = Field(max_length=1024)
    source_updated_at: Timestamp | None
    observed_at: Timestamp
    verification: Literal["VERIFIED", "REJECTED", "UNAVAILABLE"]
    access_label: Literal["PUBLIC_DEMO", "INTERNAL", "RESTRICTED"]

    @model_validator(mode="after")
    def locator(self) -> Self:
        if self.quote is not None:
            if not self.quote or self.start_offset is None or self.end_offset is None:
                raise ValueError("quote requires nonempty text and both offsets")
            if self.end_offset <= self.start_offset:
                raise ValueError("invalid quote range")
        elif self.structured_pointer is None:
            raise ValueError("quote or structured pointer required")
        elif self.start_offset is not None or self.end_offset is not None:
            raise ValueError("offsets require a quote")
        if (self.start_ms is None) != (self.end_ms is None):
            raise ValueError("both cue timestamps required")
        if self.start_ms is not None and self.end_ms <= self.start_ms:
            raise ValueError("invalid cue interval")
        if self.structured_pointer is not None and self.structured_pointer != "":
            if not self.structured_pointer.startswith("/"):
                raise ValueError("invalid JSON pointer")
        # Provider URL publication requires a future configured host allowlist.
        if not self.origin_reference.startswith("source:"):
            raise ValueError("only safe logical source references are enabled")
        return self


class Services(StrictModel):
    api: Literal["OK"]
    graph: Literal["OK", "UNAVAILABLE"]


class HealthResponse(StrictModel):
    request_id: str = Field(min_length=1, max_length=64)
    status: Literal["OK", "DEGRADED"]
    services: Services
    checked_at: Timestamp


class ErrorDetail(StrictModel):
    field: str
    reason: str


class ErrorBody(StrictModel):
    code: str
    message: str
    request_id: str
    details: list[ErrorDetail] = []


class ErrorResponse(StrictModel):
    error: ErrorBody
