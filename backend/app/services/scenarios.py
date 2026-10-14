"""Pure deterministic aggregate estimates; never a substitute for a feasible schedule."""

from decimal import Decimal, localcontext

from app.models.scenarios import SimulationRequest
from app.promise_seal.canonicalize import digest

CALCULATOR_VERSION = "aggregate-decimal-v1"


def number(value: Decimal) -> str:
    return format(value, "f").rstrip("0").rstrip(".") if "." in format(value, "f") else str(value)


def calculate(body: SimulationRequest, kind: str) -> list[dict]:
    base = body.financials.model_dump() if body.financials else {}
    overlay = next((o.model_dump(exclude_none=True) for o in body.overlays if o.type == kind), {})
    values = {**base, **overlay}
    if kind == "AS_REQUESTED":
        values.update(other_cost="0", delay_days="0", daily_delay_cost="0")
    calculations = []

    def emit(code, fields, formula, unit, explanation):
        missing = [field for field in fields if values.get(field) is None]
        with localcontext() as ctx:
            ctx.prec = 100
            value = None if missing else formula(*(Decimal(values[f]) for f in fields))
        calculations.append(
            {
                "formula_id": code,
                "value": number(value) if value is not None else None,
                "unit": unit,
                "currency": base.get("currency") if unit == "money" else None,
                "status": "UNKNOWN" if value is None else "ESTIMATE",
                "explanation": explanation,
                "inputs": {f: values.get(f) for f in fields},
                "missing_inputs": missing,
            }
        )
        return value

    emit(
        "F01",
        ["required_hours", "hourly_cost"],
        lambda h, r: h * r,
        "money",
        "Estimated labor cost for the stated scope; overlaps aggregate cost, do not add.",
    )
    emit(
        "F04",
        ["required_hours", "available_hours"],
        lambda h, a: max(Decimal(0), h - a),
        "hours",
        "Aggregate capacity deficit; zero does not prove schedule feasibility.",
    )
    cost = emit(
        "SCENARIO_AGGREGATE_COST",
        ["required_hours", "hourly_cost", "other_cost", "delay_days", "daily_delay_cost"],
        lambda h, r, o, d, c: h * r + o + d * c,
        "money",
        "Labor plus explicit overhead and delay cost assumptions, one currency/scope.",
    )
    values["cost"] = number(cost) if cost is not None else None
    emit(
        "F06",
        ["cost", "baseline_cost"],
        lambda c, b: c - b,
        "money",
        "Difference from caller supplied comparable baseline for the same scope.",
    )
    margin = emit(
        "MARGIN_AMOUNT",
        ["revenue", "cost"],
        lambda r, c: r - c,
        "money",
        "Estimated commercial value minus modeled delivery cost, not realized profit.",
    )
    values["margin"] = number(margin) if margin is not None else None
    emit(
        "MARGIN_PERCENT",
        ["margin", "revenue"],
        lambda m, r: 100 * m / r if r else None,
        "percent",
        "Percentage margin; zero revenue is undefined.",
    )
    return calculations


def compute(body: SimulationRequest, receipt: dict, ids: list[str], now: str) -> list[dict]:
    inputs = {
        "request": body.model_dump(mode="json"),
        "receipt": receipt,
        "input_kind": "USER_ASSUMPTION",
    }
    result = []
    for kind, scenario_id in zip(body.scenario_types, ids, strict=True):
        calculations = calculate(body, kind)
        gap = calculations[1]["value"]
        missing = sorted(
            {field for c in calculations for field in c["missing_inputs"]}
            | {"dependency_graph", "resource_calendars", "approved_rate_mapping"}
        )
        result.append(
            {
                "id": scenario_id,
                "type": kind,
                "status": "COMPUTED",
                "base_graph_revision": body.base_graph_revision,
                "input_digest": digest(
                    {"inputs": inputs, "type": kind, "calculator_version": CALCULATOR_VERSION}
                ),
                "inputs": inputs,
                "overlay": next(
                    (o.model_dump(mode="json") for o in body.overlays if o.type == kind), {}
                ),
                "assumptions": [a.model_dump(mode="json") for a in body.assumptions],
                "feasibility": "INFEASIBLE" if gap is not None and Decimal(gap) > 0 else "UNKNOWN",
                "conditional": True,
                "schedule": [],
                "constraint_results": [
                    {
                        "rule_id": "AGGREGATE_CAPACITY",
                        "outcome": "FAIL" if gap is not None and Decimal(gap) > 0 else "UNKNOWN",
                        "reason": "Capacity deficit under supplied assumptions."
                        if gap is not None and Decimal(gap) > 0
                        else "Aggregate capacity is not a schedule proof.",
                        "evidence_ref_ids": [],
                    }
                ],
                "calculations": calculations,
                "affected_entity_ids": [body.promise_id, receipt["receipt_id"]],
                "graph_paths": [],
                "missing_inputs": missing,
                "auditor": None,
                "policy_checks": [],
                "candidate_actions": [],
                "computed_at": now,
                "calculator_version": CALCULATOR_VERSION,
                "parent_scenario_id": body.parent_scenario_id,
            }
        )
    return result
