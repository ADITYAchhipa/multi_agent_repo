from typing import Literal

from app.models.common import SafeInt, StrictModel


class CheckedRange(StrictModel):
    from_sequence: SafeInt
    to_sequence: SafeInt


class AuditCheck(StrictModel):
    sequence: SafeInt
    code: str
    result: Literal["PASS", "FAIL", "UNAVAILABLE"]


class Checkpoint(StrictModel):
    available: bool
    trusted: bool
    sequence: SafeInt | None


class AuditVerifyResponse(StrictModel):
    request_id: str
    checked_range: CheckedRange
    chain_result: Literal["VALID", "INVALID", "INDETERMINATE"]
    checks: list[AuditCheck]
    checkpoint: Checkpoint
    limitations: list[str]
