# Synthetic seed scenario and expected oracle

**All people, companies, quotes, projects, rates, amounts and events below are fictional design fixtures.** They are illustrative source content and hand-derived expected values, not a real transcript, legal agreement, executed calculation or measured benchmark. No seed files exist yet.

## 1. Time and identities

Company Northstar Systems; tenant alias `tenant-demo`, graph `company_demo`; customer `customer-acme` Acme Retail; project `project-acme-pos`. `DEMO_ANCHOR_DATE=2026-10-12` (Monday), `DEMO_TIMEZONE=UTC`, fixed initial evaluation time anchor+4 days at 09:00. Friday deadline is anchor+4 at 19:00, explicitly supplied by fixture policy; a separate ambiguous-Friday test omits this policy and must leave deadline unresolved. All source timestamps are generated from anchor offsets. Real current time must not age a replayed fixture unpredictably.

Three resolved people: `person-aria` Aria Chen (delivery lead), `person-ben` Ben Ortiz (integration specialist), `person-casey` Casey Rao (test lead and operations executor). Demo reviewer actor `actor-reviewer` is bound to Aria; executor `actor-executor` to Casey; `actor-admin` is a separate authenticated system persona with admin and reviewer capabilities, not a fourth employee record. Viewer has no write capabilities. Actor bindings are configuration, not derived from transcripts.

Ambiguous duplicate-like pair uses the existing resolved Ben and a candidate Person `person-ben-candidate` labelled “B. Ortiz” with no external ID. This is an extra **unresolved candidate**, not a fourth resolved employee/capacity source. It stays quarantined or explicitly flagged, never merged by name.

## 2. Source inventory and exact fictional excerpts

IDs below identify logical sources; initial versions append `-v1`. Hashes/offsets are computed from actual future fixture bytes and are intentionally not fabricated here.

| Source | Type / time / exact relevant content |
|---|---|
| `src-contract` | CONTRACT, signed before anchor: five clauses C1–C5 below |
| `src-meeting-1` | TRANSCRIPT, anchor+0 09:00, Aria at 00:00:12–00:00:18: “We can deliver the loyalty integration by Friday at no extra charge.” |
| `src-meeting-2` | TRANSCRIPT, anchor+1 10:00, Aria: “My Friday statement was a proposal. Loyalty integration needs a change order; I did not approve free work.” Casey: “Credentials are still blocked and written customer acceptance is missing.” |
| `src-jira` | JIRA_EXPORT, anchor+4 08:45; five issues in §3, explicit links to promise/project |
| `src-workload` | WORKLOAD_EXPORT, anchor+4 08:45; base free slots in §4 |
| `src-rate` | RATE_CARD, effective anchor−7 through anchor+30; approved Aria USD 100/hour, Ben USD 150/hour, Casey USD 100/hour |
| `src-milestones` | CONFIG/contract-derived import; milestone records below and source refs to clauses |
| `src-co-approved` | CHANGE_ORDER: CO-0 is APPROVED for reporting configuration, USD 2,000, unrelated to loyalty; includes authorized approval record |
| `src-co-proposed` | CHANGE_ORDER: CO-1 loyalty integration proposal, USD 1,500, status PROPOSED; no customer approval |
| `src-incident` | INCIDENT, anchor−100 days: “Ben helped resolve a similar adapter issue last year.” Stale; no current authority, capacity or guaranteed estimate |
| `src-capacity-option` | CONFIG, anchor+4 08:45: Ben has an optional five-hour Friday 09:00–14:00 block at USD 150/hour, subject to internal reservation approval; supplied as scenario input, not current workload |
| `src-internal-policy` | CONFIG, effective anchor−7: “The delivery reviewer may approve internal capacity reservations up to USD 750. Reservation approval does not authorize customer delivery, free work or contract changes.” |
| `src-credential-clearance` | NOTES, imported during remediation, effective anchor+4 09:00: “ACME-102 credentials were verified at 09:00; the dependency is complete.” |

Fictional contract `contract-acme` clause text (not a legal template):

- C1 (`clause-c1`): “Base scope includes the point-of-sale rollout and two hours of acceptance testing.”
- C2 (`clause-c2`): “Loyalty integration is excluded from base scope.”
- C3 (`clause-c3`): “Additional integrations require an approved change order before customer delivery.”
- C4 (`clause-c4`): “The delivery milestone requires completed acceptance testing and written customer acceptance.”
- C5 (`clause-c5`): “The delivery milestone amount is USD 40,000. The kickoff milestone amount is USD 10,000.”

Separate synthetic account source context in `src-milestones`: “Renewal opportunity is USD 180,000; no renewal-loss probability is assigned.” Never sum that value into cost or overdue invoice exposure.

Promise alias `promise-loyalty`, receipt aliases `receipt-loyalty-v1...` (real future IDs may be deterministic fixture UUIDs with this alias table). Candidate from meeting 1 PROPOSED; meeting 2 creates material interpretation/scope conflict `conflict-loyalty`. C2/C3 support POSSIBLE_OUT_OF_SCOPE for the unconditional integration, not a legal conclusion. Related Jira task can exist even though commercial approval is missing.

## 3. Tasks and billing requirements

| ID / key | Remaining work and owner | Dependency/status |
|---|---|---|
| `jira-acme-101` / ACME-101 | Loyalty integration, 8 hours, Aria; explicit eligible alternate Ben | Depends on ACME-102; TODO; splittable sequentially across Aria/Ben, parallelizable=false, handoff_hours=0 explicitly for fixture |
| `jira-acme-102` / ACME-102 | Credentials prerequisite, 0 effort after external clearance | BLOCKED until authoritative clearance; zero effort does **not** mean complete |
| `jira-acme-103` / ACME-103 | Acceptance testing, 2 hours, Casey | Depends on ACME-101; TODO; required by delivery milestone |
| `jira-acme-104` / ACME-104 | Existing support work, 5 hours, Aria | Already reserved outside free slots; not part of integration estimate |
| `jira-acme-105` / ACME-105 | Existing maintenance, 3 hours, Ben | Already reserved outside optional capacity slot |

`milestone-delivery`: USD 40,000, target Friday19:00, REQUIRES ACME-103 and `acceptance-written`. AcceptanceRequirement `acceptance-written` is MISSING with no SATISFIED_BY edge. Scheduling test completion is not evidence that it happened. `milestone-kickoff`: USD 10,000, READY from separately supplied verified kickoff acceptance; counted independently, not at risk in this scenario.

An orphan test candidate `jira-orphan` refers to nonexistent project ID and no supporting source pointer. Firewall quarantines it; it must not appear as valid task work. Malformed relationship candidate `CAN_DO_MAGIC` is rejected, retained only in KnowledgeFinding.

## 4. Free-capacity inputs and hand-derived schedule

Workload snapshots are as of Friday08:45 (15 minutes old at initial evaluation). Aria: Friday14:00–17:00 (3 free hours) and Monday09:00–14:00 (5 free hours). Casey: Friday17:00–19:00 (2 free hours) and Monday14:00–16:00 (2 free hours). Ben: zero base free integration capacity; optional Friday09:00–14:00 (5 hours) exists only in the supplied scenario option. Existing commitments are already excluded. Fixture snapshot window covers Friday through Monday; committed_hours documented separately, not subtracted again.

| Stage/scenario | Expected schedule and feasibility | Expected arithmetic / caveat |
|---|---|---|
| Initial AS_REQUESTED | INFEASIBLE on known 5-hour integration deficit; credentials additionally unresolved | F04: 8−3=5 hours; no definite finish |
| Initial RENEGOTIATE_DATE_OR_SCOPE | UNKNOWN if credentials completion is not supplied; conditional plan for Monday | Do not claim changing date clears credentials |
| Initial CHANGE_ORDER_OR_EXTRA_CAPACITY | UNKNOWN while credentials blocked; conditional supplied five-hour option | No live workload mutation or customer approval |
| After credentials-clearance source, AS_REQUESTED | INFEASIBLE by Friday; only 3 of 8 integration hours fit | Known 5-hour gap |
| After clearance, renegotiate to Monday16:00 | FEASIBLE, conditional on date/scope agreement: Aria 3h Friday +5h Monday, Casey 2h Monday14–16 | Integration cost 8×100=USD 800; acceptance test 2×100=USD 200 shown separately as priced scope |
| After clearance, add supplied capacity | FEASIBLE, conditional on internal reservation: Ben Fri09–14 (5h), Aria Fri14–17 (3h), Casey Fri17–19 (2h) | F03 extra spend 5×150=USD 750; F05 integration cost 5×150+3×100=USD 1,050; F06 versus USD 800 integration baseline =USD 250 |

F01 unpriced integration estimate is USD 800 using baseline 8 hours×Aria USD 100/hour; status ESTIMATE. Milestone USD 40,000 remains AT_RISK and NOT_READY until actual test completion and written acceptance are imported/reviewed. No integration/customer-delivery action is allowed while CO-1 is unapproved. The valid demo action reserves **internal** optional capacity only; it neither delivers excluded work nor approves a change order. Internal capacity policy explicitly permits reservation up to USD 750 by demo reviewer and distinguishes reservation from commencing customer delivery.

## 5. Remediation and valid action

Initial Auditor must identify conflict, blocked credentials and missing written acceptance. Reviewer resolves the interpretation by issuing REVISE then CONFIRM on the exact clarified operational statement: “Reserve an internal five-hour option for Ben on Friday at a maximum cost of USD 750; customer delivery remains conditional on an approved change order.” This is a **revised commitment**, not confirmation of the original free-work claim. Attach original/clarifying transcript plus `src-capacity-option` and `src-internal-policy`; the reviewer-authored interpretation is labelled as such, never presented as a meeting quote. Initial promise history remains visible; original “no extra charge” version becomes SUPERSEDED, not rewritten.

Import `src-credential-clearance`, record reviewer resolution of `conflict-loyalty`, recalculate scenario and rerun Auditor. Material requirements for the reservation action can now pass; missing customer acceptance remains a displayed milestone risk outside the reservation's execution prerequisites. Policy P11 forbids interpreting this approval as contract amendment or customer delivery authorization.

Action alias `action-reserve-ben` targets WORKLOAD_MOCK only. Before state: option unreserved. Requested normalized change: reserve Ben's Friday09:00–14:00 slot for ACME-101, 5 hours, cost ceiling USD 750. Synthetic mock expected state after approved execution: reserved allocation exists once; same attempt/idempotency key does not add another. Read-back reports exact resource/task/start/end match. Actor-reviewer approves; actor-executor executes. The fixed demo clock stays at Friday09:00 for this planning fixture; no claim about real elapsed execution time.

## 6. Expected graph proof paths

- PTH1: `promise-loyalty —HAS_VERSION→ receipt-loyalty-v1 ←PROPOSES— chunk-meeting-1 ←HAS_CHUNK— src-meeting-1-v1 ←HAS_SOURCE_VERSION— src-meeting-1`.
- PTH2: `receipt-loyalty-v1 —POSSIBLY_COVERED_BY→ clause-c2 ←HAS_CLAUSE— contract-acme ←HAS_CONTRACT— customer-acme`. Scope-status qualifier says POSSIBLE_OUT_OF_SCOPE; relation name alone is not coverage proof.
- PTH3: `receipt-loyalty-v1 —IMPLEMENTED_BY→ jira-acme-101 —DEPENDS_ON→ jira-acme-102`.
- PTH4: `jira-acme-101 —ASSIGNED_TO→ person-aria —HAS_WORKLOAD→ workload-aria-v1`; Aria→USES_RATE→rate-aria.
- PTH5: `jira-acme-103 ←REQUIRES— milestone-delivery —REQUIRES→ acceptance-written`; no satisfaction edge initially.
- PTH6: `scenario-extra —HAS_ACTION→ action-reserve-ben —HAS_APPROVAL→ approval-reserve-ben`, with HAS_EVENT audit chain and EVIDENCED_BY current confirmed receipt.

These are expected fixture paths, not actual query results. A later implementation must seed supported edges and prove them through backend query traces; never draw them in UI from this prose.

## 7. Perturbations for tests and demo

Keep separate resettable variants: changed contract exclusion; missing rate; no date-resolution policy; stale workload; duplicate issue alias; swapped tenant ID; Unicode/malformed quote; forged approver; revoked key; altered receipt copy; delayed read-back; provider timeout after accepted write; source deletion; graph restart mid-publication; repeated same import; unsupported relation. Each variant changes one factor so false positives/negatives can be attributed. Do not corrupt the live original receipt for the tamper scene; verify a modified copy through the nonpersisting endpoint.
