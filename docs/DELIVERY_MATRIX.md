# Backend delivery matrix — 2026-10-14

Baseline: `feat/backend`, local HEAD, cached remote and live GitHub branch all
`22b1ebfa26d7380159e600b4c209891154a72bd0`. The existing API_CONTRACTS.md change
(implementation-status clarification) is preserved. No other initial changes/untracked files.
This matrix retains the full requested scope. Estimates are engineering effort ranges,
not promises of same-day production acceptance. External validation is a separate gate.

| Phase / workstream | Dependencies | Effort estimate | Current implementation / delivery status | Required validation | Blockers / limits |
| --- | --- | --- | --- | --- | --- |
| 1 API contract and release baseline | Repository audit | 1–2 hours | Existing partial routes inspected; additive contracts documented before implementation | Existing API tests, schema and error contracts | Published contract contains proposed behavior |
| 2 Source ingestion/version pagination | Existing publication CAS | 2–4 hours | Implemented constrained UTF-8 ingestion; >100-version defect being fixed | Real graph >100 versions, ACL, race, retry | No arbitrary document parser yet |
| 2 Evidence-grounded structured extraction | Retained source/chunks | 4–12 hours | Conservative extraction expansion in progress | Exact quotes, dates, amounts, ambiguity/negation | General semantic extraction needs additional model/evaluation work |
| 2 Receipt review/history/freshness | Signed audit and retained bytes | 3–6 hours | Review and history implemented; freshness/lifecycle hardening pending | Existing 61 graph tests plus source/revocation regressions | PUBLIC_DEMO promise scope |
| 3 Financial/scenario engine | Typed evidence and graph snapshots | 8–16 hours | Typed formulas, assumptions, API/persistence in progress | Decimal edge cases, missing inputs, tenant/replay/CAS | No fabricated calendar/rate/capacity data |
| 3 Action approval/execution/reconciliation | Scenarios, receipt verification, durable audit | 12–24 hours | Implementation starting with explicitly MOCK adapter | State matrix, permissions, replay, crash/reconciliation/read-back | Live workload schema/access unspecified |
| 4 Graph/trace/knowledge/grounded QA | ACL graph reads | 6–12 hours | Pending bounded authorized traversal and evidence answers | Tenant/edge filtering, bounds, abstention, traces | No generated business facts |
| 4 Conflict discovery/resolution | Source assertions, review, audit | 6–12 hours | Pending | Contradictions, authorization, preservation of history | Identity merges need explicit authority |
| 4 Source reprocessing/retirement | Version retention, dependent receipt standing | 4–8 hours | Pending | Replay, current pointer, dependent invalidation, retention | Deletion needs configured retention policy |
| 5 Teams connector | OAuth config, Microsoft Graph access | 8–16 hours + external consent | Actual client/normalization/tests in progress | Representative responses then live discovery/import | App registration, tenant consent/application access policy, organizer/meeting IDs |
| 5 Jira connector | Configured cloud/site credentials/project mapping | 8–16 hours + access | Actual read/search/update/read-back client in progress | Pagination/rate-limit/permissions + sandbox live validation | Site credentials, project and field mappings |
| 5 Workload live adapter | Vendor contract and sandbox | Unknown until supplied | Interface/mock retained; real integration pending | Approved update and verified read-back | Vendor API/auth/data model unspecified |
| 6 Keys/revocation/checkpoints | Signed audit + independent trust store | 8–16 hours + infrastructure | Pending | Retired/compromised trust, rollback, recovery | Independently protected checkpoint infrastructure required |
| 6 Session/operation lifecycle | Durable revocation/operation ledger | 4–8 hours | Pending logout/revocation/safe cancellation | Cross-instance logout, role changes, terminal/in-flight cancel | Production identity remains a separate gate |
| 7 Reliability/deployment/security/E2E | All preceding phases | 12–24 hours | Real FalkorDB available now; baseline running | Full suite, failpoints, restore, API handoff, dependency audit | Production not enabled before acceptance |

## Current verification

Previous read-only turn: 106 offline tests passed; 61 integration cases skipped because
FalkorDB was unavailable then. Current session: Docker 29.5.2 and existing FalkorDB
4.20.4 container are healthy at localhost:16379. New results will be recorded after execution.

## Work allocation

Lead owns shared integration, audited mutations, action/lifecycle/knowledge work and validation.
Parallel agents own core source/extraction, scenario engine, and Teams/Jira clients respectively.
Frontend branch/worktree remains untouched. No commit or push is implied by implementation.
