import pytest
from pydantic import ValidationError

from app.models.scenarios import SimulationRequest
from app.services.scenarios import calculate


def request(**kwargs):
    return SimulationRequest.model_validate(
        {
            "promise_id": "p",
            "base_graph_revision": 1,
            "question": "Compare costs",
            "scenario_types": ["AS_REQUESTED"],
            **kwargs,
        }
    )


def test_baseline_exact_and_negative_margin():
    body = request(
        financials={
            "scope_id": "s",
            "currency": "USD",
            "required_hours": "8",
            "available_hours": "3",
            "hourly_cost": "100",
            "revenue": "750",
            "baseline_cost": "800",
        }
    )
    values = {c["formula_id"]: c["value"] for c in calculate(body, "AS_REQUESTED")}
    assert values["F01"] == "800"
    assert values["F04"] == "5"
    assert values["F06"] == "0"
    assert values["MARGIN_AMOUNT"] == "-50"


def test_missing_is_not_zero():
    assert all(c["value"] is None for c in calculate(request(), "AS_REQUESTED"))


def test_zero_revenue_unknown_percentage():
    body = request(
        financials={
            "scope_id": "s",
            "currency": "USD",
            "required_hours": "0",
            "hourly_cost": "0",
            "revenue": "0",
        }
    )
    assert calculate(body, "AS_REQUESTED")[-1]["status"] == "UNKNOWN"


def test_alternative_delay_cost_and_unchanged_baseline():
    body = request(
        scenario_types=["AS_REQUESTED", "RENEGOTIATE_DATE_OR_SCOPE"],
        financials={
            "scope_id": "s",
            "currency": "USD",
            "required_hours": "8",
            "hourly_cost": "100",
            "baseline_cost": "800",
        },
        overlays=[
            {
                "type": "RENEGOTIATE_DATE_OR_SCOPE",
                "other_cost": "0",
                "delay_days": "2",
                "daily_delay_cost": "25",
                "hourly_cost": "125",
            }
        ],
    )
    assert calculate(body, "AS_REQUESTED")[2]["value"] == "800"
    assert calculate(body, "RENEGOTIATE_DATE_OR_SCOPE")[2]["value"] == "1050"
    assert calculate(body, "RENEGOTIATE_DATE_OR_SCOPE")[3]["value"] == "250"


@pytest.mark.parametrize("value", ["-1", "NaN", "Infinity", "1e6", "1.00", 1, True])
def test_bad_numbers(value):
    with pytest.raises(ValidationError):
        request(financials={"scope_id": "s", "currency": "USD", "required_hours": value})


def test_observed_client_claim_rejected():
    with pytest.raises(ValidationError):
        request(assumptions=[{"id": "a", "description": "claim", "kind": "OBSERVED"}])


def test_duplicate_types_rejected():
    with pytest.raises(ValidationError):
        request(scenario_types=["AS_REQUESTED", "AS_REQUESTED"])
