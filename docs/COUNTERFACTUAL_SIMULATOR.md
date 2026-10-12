# Counterfactual simulator

Status: proposed deterministic engine, not executed. Baseline §§2.4, 7. Scenario assumptions may be proposed by an LLM; scheduling, constraints and all arithmetic are backend computations. No optimality or calibrated loss-probability claim.

## 1. Isolation and reproducibility

Capture immutable input DTOs and evidence refs at a checked GraphState revision, including tasks/dependencies, workload windows, calendars, rate versions, milestone requirements, promise version, authority policy and source freshness. Store them in Scenario.inputs_json with input_digest, calculator_version and policy_version. `graph_snapshot_as_of` is capture time, not a claim of engine snapshot isolation. Read revision before/after capture and retry once if changed; otherwise STALE_SNAPSHOT.

Overlay only contains allowlisted hypothetical changes: supplied additional free-capacity slots, proposed due date, explicit reduced work/estimate with source or user assumption, proposed authorized resource substitution. Store in Scenario.overlay_json. No live JiraIssue, WorkloadSnapshot, Contract, PromiseVersion or milestone properties change. Scenario relationships in UI are DTO-only and prefixed `scenario:`. New assumptions produce new Scenario, parent-linked; old result stays reproducible. A source/policy change marks dependent scenario STALE.

## 2. Input contract and units

Task input: `{issue_id,remaining_hours,estimate_source_ref,assignee_candidates,dependencies[],earliest_start?,due_at?,completion_state,resource_policy:{splittable,parallelizable,handoff_hours}}`. Remaining hours must be supplied; a total estimate without completed-work basis cannot imply remaining effort. Story points without explicit approved conversion → UNKNOWN. Cycles/missing prerequisite IDs invalidate schedule. DONE task consumes zero remaining hours, with supporting updated source.

Capacity input: per-person, timezone-aware free intervals with as_of/window/source; available_hours equals sum of free intervals. committed_hours is explanatory and **already excluded**. Do not subtract committed work twice. Active competing tasks consume capacity only if not already accounted for in snapshot; include counted_task_ids and reject ambiguous coverage. Missing interval/calendar mapping may support aggregate gap calculation but not exact finish time.

Calendar: explicit IANA timezone in config, working intervals, holidays and exceptions. UTC is synthetic fixture choice only. 15-minute slots; supplied effort must be a multiple of 0.25 hours or round **up** to next slot with displayed rounding assumption. Store original and scheduled values. DST transitions use actual instants; nonexistent/ambiguous local times require explicit offset or review. No assumed weekend work/overtime. Workload age >24 hours by proposed default blocks definite scheduling, regardless of 90-day general source-stale default.

Rate input: effective approved cost per resource/role, currency and source. Do not confuse customer billing rate with loaded delivery cost. Multiple overlapping rates require resolution. No supplied rate → cost UNKNOWN even if schedule feasible.

## 3. Deterministic scheduling algorithm v1

1. Resolve all prerequisite tasks and affected milestones via Q03/Q05. If traversal cap is reached, mark incomplete and UNKNOWN; do not drop unseen work.
2. Validate acyclic graph using topological order, then enforce earliest start, prerequisite completion, supplied deadlines and source freshness.
3. Reserve only explicit free 15-minute slots. Order ready tasks by due instant (unknown last), then task ID. Order eligible resources by current assignment preference, then resource ID. Record tie-breaks in result.
4. Default task may use one resource, cannot run in parallel, and may pause between its available slots. Multi-resource handoff is allowed only when task resource_policy explicitly says splittable and specifies handoff hours. No implicit expertise-to-eligibility mapping.
5. For a multi-resource serial task, allocate earliest eligible slots ordered by instant then resource ID; no two resources work on that task simultaneously unless parallelizable=true explicitly. Charge any handoff overhead from input; missing overhead → UNKNOWN when substitution is required.
6. Schedule successors only after full predecessor effort finishes. Compare completion to deadline and aggregate every constraint. Stop at configured horizon (fixture 14 days); unscheduled work becomes INFEASIBLE if known capacity is insufficient over fully provided horizon, UNKNOWN if later calendar is missing.
7. Produce actual allocated slots, finish instants, resource utilization, unmet work, constraints, affected IDs and assumption list. Return conditional=true if feasibility relies on any unapproved assumption. Conditional output never authorizes that assumption as a fact.

Feasibility aggregation: known violated hard constraint → INFEASIBLE; otherwise missing required input → UNKNOWN; otherwise FEASIBLE. Known failure and missing inputs are both reported. The scheduling heuristic finding no schedule does not prove no possible schedule under every ordering; label reason `HEURISTIC_NO_SCHEDULE` where applicable. Simple aggregate insufficiency/cycle/deadline facts can be definitive under modeled constraints.

## 4. Formulas and exposure semantics

Decimal arithmetic only; retain full calculation precision, round presentation to currency minor unit with ROUND_HALF_UP and label rounding. No financial Cypher/LLM arithmetic.

| Formula ID | Definition | Status / guard |
|---|---|---|
| F01 UNPRICED_WORK_COST | estimated_unapproved_hours × loaded_hourly_cost | ESTIMATE; hours/rate/currency/source required |
| F02 MILESTONE_AT_RISK | configured milestone amount when named required condition is unmet by target | AT_RISK, not loss; once per distinct milestone, not per graph path |
| F03 RECOVERY_COST | extra_hours × approved_hourly_cost + explicit other costs | ESTIMATE until actuals; no unknown cost replaced with zero |
| F04 CAPACITY_GAP | max(0, required remaining hours − eligible free hours before deadline) | Hours; aggregate diagnostic, not a sufficient schedule proof |
| F05 SCENARIO_WORK_COST | sum(allocated hours × matching approved resource rate) + explicit overhead costs | ESTIMATE per currency; identify priced/unpriced scope |
| F06 COST_DELTA | scenario work cost − stated comparable baseline work cost | ESTIMATE; same scope/currency/horizon only; otherwise UNKNOWN |
| F07 MILESTONE_READINESS | all required tasks DONE AND all required acceptance records VERIFIED | READY/NOT_READY/UNKNOWN; technical completion alone insufficient |

Each result includes formula ID/version, input values/units/evidence, currency, computed_at and unknown inputs. Renewal value USD 180,000 in the seed is contextual, separately labelled; no automatic probability or summation. USD 800 unpriced integration cost and USD 750 extra-capacity spend overlap; never headline USD 1,550. USD 40,000 milestone at risk is also a different category. Cross-currency totals absent without explicitly approved FX rate/source/as-of and method (not MVP).

## 5. Scenario families and objective

| Family | Overlay | Comparison intent |
|---|---|---|
| AS_REQUESTED | Existing scope, date, workload and unresolved prerequisites | Identify deficit/blocker under observed inputs |
| RENEGOTIATE_DATE_OR_SCOPE | Proposed explicit later date or reduced scope | Show feasible alternative conditional on customer/commercial agreement; draft only |
| CHANGE_ORDER_OR_EXTRA_CAPACITY | Supplied extra capacity/rate plus proposed change order when relevant | Quantify scheduling/cost benefit conditional on authorization; no contract change |

Default ranking is lexicographic and disclosed: exclude policy-blocked candidates from executable recommendation; prefer fewer unmet hard constraints; then fewer unsupported assumptions; then earlier completion; then lower comparable incremental cost. Unknowns never sort as zero. User can select a different objective, captured in Scenario, but cannot override hard policy gates. Auditor reviews the preferred candidate; selection is advisory, not automatic optimization of profit.

## 6. Graph impact and limits

Impact set is union of original and overlay task dependencies, resource competing assignments, linked PromiseVersions/projects/customers and milestone requirements. Deduplicate IDs, preserve path evidence, mark discovered impacts without supported monetary value UNKNOWN. Do not infer new causal AFFECTS edges merely from an LLM explanation; publish any new business assertion only through ingestion/review firewall.

Limitations: estimates may be wrong; free slots may change; transcript may be misattributed; critical paths may be incomplete; handoff cost/skill eligibility need explicit data; external acceptance cannot be simulated as received; meeting promise confirmation does not amend scope. No probabilistic risk scoring, employee ranking, global optimality, invoice automation or graph clone in MVP.

Acceptance: T04/T05/T28/T29 plus the exact independent expectations in [SEED_SCENARIO](SEED_SCENARIO.md). Input replay with same calculator/calendar versions must reproduce schedules, input digests and unrounded costs. No results were computed by implemented application code in this phase.
