from typing import Literal

from pydantic import Field, model_validator

from app.models.common import Digest, Id, Quantity, SafeInt, StrictModel, Timestamp


class Slot(StrictModel):
    start: Timestamp
    end: Timestamp

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("slot must have positive duration")
        return self


class CostCeiling(StrictModel):
    amount: Quantity
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class WorkloadChange(StrictModel):
    resource_id: Id
    task_id: Id
    allocation_slots: list[Slot] = Field(min_length=1, max_length=32)
    cost_ceiling: CostCeiling

    @model_validator(mode="after")
    def no_overlap(self):
        ordered = sorted(self.allocation_slots, key=lambda item: item.start)
        if any(a.end > b.start for a, b in zip(ordered, ordered[1:])):
            raise ValueError("overlapping slots")
        return self


class ProposeAction(StrictModel):
    expected_scenario_digest: Digest
    target_id: Id
    requested_changes: WorkloadChange


class ActionGuard(StrictModel):
    expected_revision: SafeInt
    proposal_hash: Digest


class ApproveAction(ActionGuard):
    reason: str = Field(min_length=1, max_length=2000)


class ReasonGuard(StrictModel):
    expected_revision: SafeInt
    reason: str = Field(min_length=1, max_length=2000)


ActionStatus = Literal[
    "PROPOSED", "NEEDS_APPROVAL", "APPROVED", "EXECUTING", "SUCCEEDED", "FAILED",
    "NEEDS_RECONCILIATION", "CANCELLED", "BLOCKED"
]
