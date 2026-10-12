# Product design

Status: proposed specification, not an implemented product. Baseline §§1–2, 10–12. Requirement IDs R01–R32 are stable and map to [TRACEABILITY_MATRIX](TRACEABILITY_MATRIX.md).

## 1. Users and outcome

| Persona | Job and starting context | Successful outcome |
|---|---|---|
| Delivery director / owner | Must reconcile commercial intent, deadlines and staffing | Understand evidence and tradeoffs; approve an affordable, defensible response |
| Project manager | Tracks Jira dependencies and acceptance work | Find blocked work, stale estimates and missing acceptance evidence |
| Account manager / reviewer | Understands customer scope and commercial authority | Confirm or dispute a precise interpretation without implying contract amendment |
| Operations executor | May change approved scheduling fields | Apply exactly one approved change and see verified read-back |
| Administrator | Configures access and source mappings | Control ingestion, resolve graph-quality issues and inspect audit integrity |
| Read-only stakeholder | Needs an evidence-backed answer | See only authorized sources, uncertainty and current status |

Core outcome: an authorized user can follow source → commitment → scope → task dependencies → available capacity → separate financial exposures → alternatives → challenge → approval → verified result. All arrows representing business relationships come from FalkorDB results. The interface explains unknowns rather than inventing missing facts.

## 2. Journeys

### 2.1 Discover and review

Admin imports a synthetic VTT and contract excerpt. The import reports parsed/rejected counts and opens Knowledge Health if necessary. Promise Compiler produces a PROPOSED candidate. Inbox shows the exact quote, source timestamp, unresolved speaker/deadline identities and a scope classification. Reviewer opens full accessible evidence and selects confirm, dispute or reject with reason. A successful review creates a new receipt version; a concurrent edit returns a conflict requiring refresh.

Confirmation text: “I confirm this recorded interpretation for internal operational use.” Show any external customer agreement as separate evidence. Do not use “sign contract,” “legally verified” or “customer approved” without the corresponding source and separate process.

### 2.2 Investigate and compare

User asks the main business question. Graph Investigator retrieves bounded paths; Margin Investigator computes costs; Planner compares AS_REQUESTED, RENEGOTIATE_DATE_OR_SCOPE and CHANGE_ORDER_OR_EXTRA_CAPACITY. Clicking a number opens formula/input sources. Clicking a path opens source-backed edges. The selected scenario is challenged by an independent Auditor. User can edit assumptions by creating a new scenario; source records are unchanged.

### 2.3 Approve and verify

An eligible scenario generates a draft ActionProposal. Approval Queue shows current target state, requested changes, supporting confirmed receipt versions, dependency freshness, required role, expiry and auditor output. Reviewer approves this exact proposal. Executor initiates it; backend repeats policy and before-state checks, dispatches once, reads back, and records an Action Receipt. An uncertain result shows NEEDS_RECONCILIATION and disables repeat execution.

### 2.4 Changed or removed evidence

Source refresh creates a new SourceVersion, retires only that source's old assertions, and marks dependent scenarios/actions stale. A changed commitment gets a new PROPOSED/NEEDS_REVIEW version, not inherited confirmation. Detail shows old/new quotes and hashes. Source retirement removes it from future reasoning; prior receipt may remain cryptographically valid but its source check becomes UNAVAILABLE after deletion.

## 3. Functional requirements

| ID | Required behavior | MVP boundary |
|---|---|---|
| R01 | Import VTT/TXT/MD/JSON/CSV with size/type validation and exact stored hashes | Synthetic file import mandatory; no PDF/DOCX |
| R02 | Extract strict candidates with verbatim evidence, class, nullable deadline, speaker and triage confidence | Unsupported quote never publishes a fact |
| R03 | Compare signed scope and approved changes, show clauses and five-state classification | No binding legal interpretation; missing data → INSUFFICIENT_EVIDENCE |
| R04 | Deterministic unpriced cost, recovery cost and milestone exposure with units, currencies and formulas | Unknown inputs stay UNKNOWN; no combined misleading total |
| R05 | Generate 2–3 isolated, reproducible scenarios with dependency/capacity checks | Three fixed scenario families; bounded heuristic |
| R06 | Independent adversarial review and deterministic final policy | Invalid auditor output blocks action readiness |
| R07 | Versioned PromiseSeal payload, hash, service signature and fresh verification | Custom protocol, no VC claim |
| R08 | Authorized review, disputes, supersession, fulfillment and receipt revocation | New events/versions; historical evidence preserved subject to deletion policy |
| R09 | Typed proposals, server approvals, freshness and least-privilege execution | One mock workload update mandatory |
| R10 | Idempotent execution ledger, read-back and uncertain-write reconciliation | No blind write retry or guessed rollback |
| R11 | Actual FalkorDB joins/traversals and traceable UI paths | No frontend-invented edges |
| R12 | Controlled ontology, entity resolution, quote, duplicate, orphan, conflict and growth checks | Quarantine/review UI required |
| R13 | Versioned, idempotent ingestion, retirement, rollback and dead-letter handling | Reprocess is admin-only |
| R14 | Transcript adapter boundary and optional documented live import | VTT primary; Graph/Vexa conditional |
| R15 | Jira export import plus bounded optional REST synchronization | Read-only first; live writes stretch |
| R16 | Workload mock and explicitly unmapped live boundary | Real endpoint/field contract remains OPEN |
| R17 | Authentication, roles, tenant and source access isolation | Simplified local session, not enterprise IAM |
| R18 | Prompt-injection, tool, SSRF, secret, replay and exfiltration controls | Backend enforcement, not prompts alone |
| R19 | Source privacy, consent, retention and deletion impacts | Synthetic-only seed; private-data policy pending |
| R20 | Overview, Inbox, Detail, Lab, Queue, Receipt, Graph, Health, Settings | Focus on the connected workflow |
| R21 | Accessible, responsive UI and meaningful failure/empty states | Relationship list on narrow screens |
| R22 | Durable trace, graph health, audit chain and operational observability | Safe metadata only in ordinary logs |
| R23 | Fixed synthetic scenario, actual-query demo and honest replay | No third-party credentials required |
| R24 | Real FalkorDB integration tests and labelled extraction/evaluation suite | Proposed thresholds until run |
| R25 | Compatible-version pins, startup configuration, backup/restore and deployment plan | Future three-service local topology |
| R26 | Repository/license audit with narrow reuse and fallback boundaries | No full application merges |
| R27 | Bounded agents with typed model-independent handoffs and failure recovery | Max five graph tools / two planner revisions |
| R28 | Milestone readiness requires acceptance evidence, separate from task completion | No invoice/payment writes |
| R29 | Business freshness, source changes and approval invalidation | No reimport-to-refresh trick |
| R30 | Safe handling of historical expertise and ambiguous people | Expertise is not authorization; no first-name merge |
| R31 | Explicit non-goals and honest claims | No legal, immutable, loss-prevention or optimum claims |
| R32 | Documentation-only phase, preserved master, consistent contracts and traceability | No application or executable files now |

## 4. Primary screens and interaction contracts

All pages retain a visible tenant/demo/mock banner, global request status and source access context. Navy/neutral surfaces and restrained blue accent are a design recommendation; status uses text/icon in addition to color. No invented metrics when empty.

| Screen / proposed frontend path | Primary data and actions | Required states |
|---|---|---|
| Overview `/` | Counts of high-risk/unconfirmed promises, open conflicts, at-risk milestones, recent events; drill into evidence | Empty → import guidance; incomplete amounts shown as unknown; graph offline banner |
| Promise Inbox `/promises` | Sort/filter by business state, customer, deadline, risk; pagination | PROPOSED and DISPUTED explicit; unknown deadline sorts last; unauthorized results omitted |
| Promise Detail `/promises/{id}` | Quote/cue, speaker status, scope clauses, Jira dependencies, workload, milestones, version timeline, verify/review controls | Old version banner; revoked receipt; invalid signature; inaccessible source; stale evidence; 409 refresh |
| Simulation Lab `/simulations/{id}` | Side-by-side assumptions, deadlines, costs, constraints, affected paths; choose/edit and create proposal | Unknown ≠ feasible; hypothetical edges dashed and labelled; stale result cannot execute |
| Approval Queue `/actions` | Exact before/after diff, approver capability, policy/auditor reasons, expiry | Blocked controls explain remediation; actor cannot self-approve an agent action |
| Action Receipt `/actions/{id}` | Attempts, safe external reference, expected/actual read-back, approval and audit verification | EXECUTING disables repeat; reconciliation allows authorized read-only reconciliation; no fake success |
| Graph Explorer `/graph/{id}` | Real node/edge filters, highlighted path, accessible side panel; default ≤60 nodes | Truncated indicator and bounded expand; no-path state; hypothetical overlay legend |
| Knowledge Health `/knowledge` | Rejected quotes/types, identity ambiguity, stale sources, logical orphans and conflicts; review/repair actions | Quarantine separate from active facts; admin-only mutation controls |
| Settings `/settings` | Connector health/mode, configured project scopes and limits | Configured/unconfigured only for secrets; no token entry sent to an LLM |

Frontend paths are proposed UI routes, not backend API aliases. Backend routes are defined only in [API_CONTRACTS](API_CONTRACTS.md). The Approval Queue uses the additional action-list endpoint there.

## 5. Permissions

Capabilities are explicit server grants; admin does not automatically inherit reviewer/executor. Every authenticated actor also needs tenant and object/source ACL authorization. Local demo credentials map to a named actor, never a client-supplied role.

| Operation | viewer | reviewer | executor | admin |
|---|---|---|---|---|
| Authorized reads/chat/simulation | Yes | Yes | Yes | Yes |
| Upload/sync/reprocess/configure | No | No | No | Yes |
| Confirm/dispute/reject/fulfill | No | Yes | No | Only with reviewer grant |
| Approve/reject an action | No | Yes, within commercial limits | No | Only with reviewer grant |
| Execute approved action / read-only reconcile | No | No | Yes, within connector scope | Only with executor grant |
| Revoke receipt / retire source / propose graph repair | No | No | No | Yes with reason; business conflict resolution also requires reviewer |

No LLM role has human capabilities. Proposed demo separation requires approver actor ≠ executor actor; creator can be the system. Commercial ceilings and real access groups are Q04. Source access and execution authorization are rechecked on the server regardless of UI visibility.

## 6. Non-functional requirements and failure states

These are **proposed targets**, not measured service promises.

- Correctness: every factual answer item has accessible evidence or is explicitly a hypothesis; deterministic math agrees exactly with independent fixtures. No unapproved external writes.
- Responsiveness: local metadata reads p95 ≤2 seconds on the fixed seed; graph queries ≤2-second timeout; async operations acknowledge within 2 seconds. End-to-end generated analysis target ≤60 seconds; otherwise show phase/progress/cancel. Record hardware/model for any measurements.
- Boundedness: 20 MiB upload, 200 chunks/run, 5 graph tools/question, 60 initial graph nodes, depth ≤3, 10 connector pages/run, 2 planner revisions. Limits in configuration; fail explicitly on truncation.
- Accessibility target: keyboard operation, visible focus, labelled controls, semantic tables, descriptive validation, announced async status, reduced motion, 200% zoom, contrast testing and no color-only distinction. Graph has equivalent relationship list and evidence detail. No conformance claim before manual assessment.
- Responsive layouts: desktop ≥1024 px, stacked comparison/tablet 768–1023 px, card/list mobile <768 px. Preserve evidence and approval diffs at 320 px; no mandatory pan/drag to read a fact.
- Reliability: durable job/action records precede external calls. Restart recovers queued work and reconciles uncertain writes. Graph outage blocks writes and new factual answers; a cached replay, if shown, is timestamped REPLAY.
- LLM outage: return deterministic findings and a no-generated-analysis notice. Never silently substitute canned text as a live model answer.
- API failures: 401 prompts authentication; 403 explains capability; 404 avoids cross-tenant disclosure; 409 refreshes stale version; 413/415/422 explain import/schema correction; 429 shows bounded retry; 503 preserves draft and disables execution.
- Privacy: read-time ACL applied to node, edge, snippets, counts, paths, receipts, runs and traces. A hidden source must not leak through answer summaries or aggregate counts.

## 7. Success criteria

The later MVP passes only when the R01–R31 acceptance rows and T01–T32 tests are evidenced, the five-minute synthetic demo is reproducible, all mandatory deterministic safety gates pass, and measured extraction/path performance is reported honestly. A full implementation may still have OPEN production choices. R32 is the deliverable criterion for this documentation phase only.
