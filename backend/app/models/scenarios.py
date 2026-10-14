from typing import Literal, Self

from pydantic import Field, model_validator

from app.models.common import Id, Quantity, SafeInt, StrictModel, Text

ScenarioType = Literal[
    "AS_REQUESTED", "RENEGOTIATE_DATE_OR_SCOPE", "CHANGE_ORDER_OR_EXTRA_CAPACITY"
]


class Assumption(StrictModel):
    id: Id
    description: Text
    value: str | None = Field(default=None, max_length=128)
    unit: str | None = Field(default=None, max_length=64)
    evidence_ref_ids: list[Id] = Field(default_factory=list, max_length=100)
    kind: Literal["USER_ASSUMPTION"]


class Financials(StrictModel):
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    scope_id: Id
    revenue: Quantity | None = Field(default=None, max_length=24)
    baseline_cost: Quantity | None = Field(default=None, max_length=24)
    required_hours: Quantity | None = Field(default=None, max_length=24)
    available_hours: Quantity | None = Field(default=None, max_length=24)
    hourly_cost: Quantity | None = Field(default=None, max_length=24)


class Overlay(StrictModel):
    type: ScenarioType
    required_hours: Quantity | None = Field(default=None, max_length=24)
    available_hours: Quantity | None = Field(default=None, max_length=24)
    hourly_cost: Quantity | None = Field(default=None, max_length=24)
    revenue: Quantity | None = Field(default=None, max_length=24)
    other_cost: Quantity | None = Field(default=None, max_length=24)
    delay_days: Quantity | None = Field(default=None, max_length=24)
    daily_delay_cost: Quantity | None = Field(default=None, max_length=24)


class SimulationRequest(StrictModel):
    promise_id: Id
    base_graph_revision: SafeInt
    question: Text
    scenario_types: list[ScenarioType] = Field(min_length=1, max_length=3)
    assumptions: list[Assumption] = Field(default_factory=list, max_length=100)
    parent_scenario_id: Id | None = None
    financials: Financials | None = None
    overlays: list[Overlay] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def unique(self) -> Self:
        if len(set(self.scenario_types)) != len(self.scenario_types):
            raise ValueError("duplicate scenario type")
        kinds = [item.type for item in self.overlays]
        if len(set(kinds)) != len(kinds) or not set(kinds).issubset(self.scenario_types):
            raise ValueError("duplicate or unrequested overlay")
        if "AS_REQUESTED" in kinds:
            raise ValueError("baseline cannot be overlaid")
        if len({item.id for item in self.assumptions}) != len(self.assumptions):
            raise ValueError("duplicate assumption")
        return self


class Calculation(StrictModel):
    formula_id: str
    value: str | None
    unit: Literal["money", "hours", "percent"]
    currency: str | None
    status: Literal["ESTIMATE", "UNKNOWN"]
    explanation: str
    inputs: dict[str, str | None]
    missing_inputs: list[str]


class ConstraintResult(StrictModel):
    rule_id: str
    outcome: Literal["FAIL", "UNKNOWN"]
    reason: str
    evidence_ref_ids: list[Id]


class ScenarioResult(StrictModel):
    id: Id
    type: ScenarioType
    status: Literal["COMPUTED", "STALE"]
    base_graph_revision: SafeInt
    input_digest: str
    inputs: dict
    overlay: dict
    assumptions: list[Assumption]
    feasibility: Literal["INFEASIBLE", "UNKNOWN"]
    conditional: bool
    schedule: list[dict]
    constraint_results: list[ConstraintResult]
    calculations: list[Calculation]
    affected_entity_ids: list[Id]
    graph_paths: list[dict]
    missing_inputs: list[str]
    auditor: dict | None
    policy_checks: list[dict]
    candidate_actions: list[dict]
    computed_at: str
    calculator_version: str
    parent_scenario_id: Id | None


class SimulationResponse(StrictModel):
    request_id: str
    scenario_ids: list[Id]
    results: list[ScenarioResult]


class SimulationDetail(StrictModel):
    request_id: str
    scenario: ScenarioResult
