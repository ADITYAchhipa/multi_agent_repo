# Test and evaluation plan

**All criteria below are proposed targets. No application tests, benchmarks, connector calls or deployments were run in this documentation phase.** Hand-derived fixture expectations in SEED_SCENARIO are test oracles, not measured results. T01–T32 map to R01–R32 in TRACEABILITY_MATRIX.

## 1. Test layers and fixtures

Unit: parsers, offsets/hashes, ontology, identity resolution, canonical bytes/signatures, business math, calendar/scheduler, policy, state transitions and adapter mapping. Integration: actual pinned FalkorDB server/client, typed queries/mutations/indexes, source artifact persistence and recovery; mocks alone cannot satisfy graph acceptance. API: every contract's success/schema/auth/tenant/revision/idempotency/error handling. UI: status/evidence/approval/graph accessible fallback and failure states; future lint/typecheck/build. End-to-end: actual synthetic import → graph → receipt → scenario → auditor/policy → approved mock write → read-back → audit verify.

Fixtures: exact fictional sources and alias IDs in [SEED_SCENARIO](SEED_SCENARIO.md), plus independent perturbations. Store eventual gold annotations separately from extraction prompts/output. Gold includes source bytes/hash, exact span, commitment class, normalized proposition, expected allowed graph edges, source IDs, monetary inputs, schedules and allowed actions. Do not train/tune on the holdout. Clocks, key fixtures and random seeds controlled in tests; production keys never used.

## 2. Test case catalogue

| ID | Tests and required assertions | Gate |
|---|---|---|
| T01 Source parsing/import | VTT cue/timestamp/speaker, UTF-8/CRLF/BOM, TXT/MD, JSON pointers, CSV cells; mismatched MIME, malformed encoding, traversal name, 20 MiB limit and unsupported PDF reject safely; retained bytes hash exactly | P1 |
| T02 Extraction/evidence | Explicit, conditional, negated, hypothetical, suggestion, ambiguous Friday and speaker; exact matching span required; Unicode scalar offsets tested; valid quote with wrong interpretation counted wrong; missing/fabricated quote never active | P3 |
| T03 Scope | In-scope, exclusion, approved unrelated change order, proposed change order, contradictory clauses, absent contract and legal-review ambiguity; all five scope states, evidence shown; no speech automatically amends scope | P3 |
| T04 Financial calculations | F01–F06 exact independent Decimal results; 8×100=800, 5×150=750, 5×150+3×100=1050, delta250; missing/overlapping rates, negative/invalid inputs, mixed currency and points without conversion → reject/UNKNOWN; no double-counting | P1/P3 |
| T05 Scenario scheduling | All three families; 5-hour deficit; blocked prerequisite, cycle, missing task, cap truncation, stale capacity, calendar/DST, quarter-hour rounding, handoff and competing-work duplication; unchanged live-node digests before/after simulation; repeat same input yields same schedule/math | P3 |
| T06 Auditor/policy | Contradictory source, unsupported scope, stale workload, false inferred authority, duplicate work, invalid output; Auditor PASS cannot override P01–P12; planner revision/independent-call limits | P3 |
| T07 Receipt crypto | Valid generated fixture signature passes; payload/digest/signature/key/algorithm/tenant modified fails; canonical vectors cover control/Unicode/null/duplicate keys/array order/integers; unknown key and unsigned distinguished; no fabricated signature fixture | P0/P1 |
| T08 Lifecycle/version | All allowed/forbidden review transitions; concurrent review accepts one expected revision; original payload unchanged, contiguous predecessor hashes; confirmation cleared on edit; revocation distinct from signature; broken/forked chain detected | P1/P4 |
| T09 Approval/authorization | PROPOSED/unconfirmed/disputed/revoked evidence cannot execute; role/body/actor forgery, self-approval and wrong target fail; exact approved proposal only; zero external write calls before valid approval | P4 |
| T10 Action reliability | Mock update once/read-back exact; repeated idempotency request, two execute clicks, crash after dispatch, timeout with applied write, partial result, mismatched read-back, definitive no-effect failure; no blind resend; reconciliation GET only; compensation requires new proposal | P4 |
| T11 Real graph reasoning | Q01–Q10 actual Cypher results; expected IDs/directions/source refs; no free Cypher or frontend text-inferred paths; parameters with quote/injection strings treated as values; graph cap explicit | P0/P1/P2 |
| T12 Firewall/repair | Every G01–G12 rule; unknown type CAN_DO_MAGIC, inverted endpoint, orphan refs, malicious growth, ambiguous merge, no active facts from quarantined candidates; repairs preview/revalidate/audit and preserve signed history | P1 |
| T13 Idempotency/incremental ingest | Identical import/reprocess no new facts/receipts; overlap chunks dedup; changed version retires only its assertions; out-of-order source quarantined; crash before/after atomic publish; safe rollback and dead letter | P1 |
| T14 Transcript adapters | VTT mandatory; fixture Vexa/Graph mapping, empty/unavailable transcript, missing speakers, 401/403/429/5xx, partial content, repeated poll, admin-disabled access; no arbitrary URL/bot join; live only with consented credentials | P5 optional live |
| T15 Jira adapter | Synthetic exports; verified search token pagination/limits/repeated token, identity/key changes, per-site mapping, 401/403/429/5xx/timeouts, deleted/inaccessible issue; live writes disabled until endpoint/field/read-back contract tested in sandbox | P4/P5 |
| T16 Workload boundary | Deterministic mock; no live endpoint/mapping defaults; missing mapping returns WORKLOAD_ADAPTER_NOT_CONFIGURED and zero HTTP writes; units/calendar/as-of enforced; UI clearly MOCK MODE | P4 |
| T17 Auth/tenancy | Parameterize every API route for anonymous/role/tenant/access label; reject cross-tenant scalar refs/paths/receipts/actions/traces/counts/cursors; 404 non-disclosure; CSRF, expiry/logout and changed role grants; two synthetic tenants | P1–P5 |
| T18 Adversarial security | Prompt injection in transcript/contract/Jira/returned tools, URL/DNS/redirect SSRF, HTML/script rendering, oversized output, fake backend success, secret canary in logs/UI/prompts, key URL/algorithm substitution and replay | P3/P4 |
| T19 Privacy/deletion | Unauthorized raw source/derived answer blocked; DELETE removes governed quote copies from artifacts/chunks/receipts/audit as policy requires; active unsupported facts retired, approvals blocked; missing evidence returns UNAVAILABLE; restore re-applies deletion | P4/P5 |
| T20 Screens/product flow | Nine screens populated from backend, states/links/diffs accurate, unknown amounts not zero, evidence on every risk, no invented chart data, old-version and mock banners, action receipt exact state | P2/P5 |
| T21 Accessible/responsive UI | Keyboard-only navigation/approval, focus recovery, labelled errors, screen reader status, contrast, reduced motion, 200% zoom, 320/768/1440px layouts; graph equivalence list; no color-only states | P2/P5 |
| T22 Audit/trace/health | Actual backend steps, safe parameters, timestamps/counters; chain mutation/gap/reorder detected; trusted checkpoint rollback case versus local-chain limitation; graph offline health sanitized; missing artifact finding | P1/P5 |
| T23 Demo/replay | Seed-reset/import/questions/scenes repeat twice; tamper copy only; blocked preapproval and one approved mock read-back live; replay labelled; no provider credentials needed; actual graph inspectable | P5 |
| T24 Evaluation methodology | Fixed gold set, full question coverage, raw per-case scores, TP/FP/FN/confusion matrix, no omitted failures, same-model baseline if run, cost/latency hardware/model metadata | P5 |
| T25 Runtime/deployment | Pinned image/client and frontend/backend compatibility, indexes and restart persistence, atomic publication rollback, clean restore and reconciliation, config fail-closed, secret redaction, future lint/type/build pass | P0/P5 |
| T26 Repository integration | Pins/licenses/notices recorded; no whole-repo merges; optional SDK uses disposable graph only; required sources/OPEN verification resolved for enabled capabilities | P0/P5 |
| T27 Agent limits/recovery | Strict output/ID schema, five-call global budget, two plan revisions, token/output/time bounds, invalid handoff/snapshot/cancel cases, model outage deterministic answer; no agent approve/write tool | P3 |
| T28 Billing readiness | Task done without written acceptance → NOT_READY; all configured requirements verified → READY; disputed/deleted acceptance blocks readiness; milestone counted once across paths; no invoice/payment call | P3 |
| T29 Freshness/TOCTOU | Reimport does not freshen old source; workload 24h default distinct from 90d general; changed contract/receipt/rate/calendar/ACL/target/approval expiry invalidates readiness; unrelated revision revalidation may preserve identical dependency digest | P4 |
| T30 Identity/expertise | Two Ben aliases/shared names/external ID conflict remain unresolved unless reviewed; historical incident doesn't prove permission, skill eligibility, duration or available hours; no employee ranking | P1/P3 |
| T31 Scope/claims | UI/docs/demos never claim VC/legal enforceability/tamper-proof/lost revenue/global optimum/production auth; forbidden message/contract/invoice/database/tool routes absent | P5 |
| T32 Documentation boundary | Required Markdown files, local links, requirement mapping, canonical enums/routes/labels, preserved original hashes and absence of application/executable files | Documentation phase |

P0–P5 here mean implementation phases 0–5, not policy rules (policy IDs have two digits P01–P12).

## 3. Real FalkorDB gate

Start an actual locked server image only in a later authorized implementation task. Test selected Python runtime/client: authenticated graph selection, parameter binding, read-only rejection of writes, index creation/introspection and query plan, exact template paths, edge properties, duplicate/parallel assertion counts, failed atomic batch leaves no partial business facts, concurrent source/review action claims, crash/reconnect/reset cache and backup restoration. Store server version/image digest, client version, architecture, runtime and test output.

If graph tests fail, stop dependent work; mocked results or UI fixtures do not substitute for R11. An in-memory fake may unit-test service policy, but the final acceptance suite inspects the real graph before/after every critical rejected/simulated mutation. No unverified native transaction/index/constraint behavior should become an assumption in implementation.

## 4. Fixed benchmark question set

At least the 24 cases below, with fixtures/expected IDs and source evidence from SEED_SCENARIO. Cases 1–12 retain all master judge prompts. For statistical reporting, 24 is a small diagnostic suite, not a population-level proof of superiority. Add a separate ≥40 labelled extraction span set (at least 8 each explicit/conditional/suggestion/hypothetical/ambiguous) and 10 negation/no-commitment negatives; negatives may overlap classes only when annotation policy says so.

| Case | Prompt / perturbation | Expected answer property |
|---|---|---|
| B01 | What exactly did we promise Acme, and is it confirmed? | Initial PROPOSED quote, later dispute shown; no automatic agreement |
| B02 | Show me the exact meeting quote and who said it. | Exact span/cue, Aria identity evidence or uncertainty |
| B03 | Does the signed scope cover this deliverable? | C2/C3 exclusion/change-order evidence, qualified scope status |
| B04 | Which Jira issues and dependencies are needed? | 101→102 and 103→101; correct direction |
| B05 | Can we deliver by Friday with the workload we actually have? | 8h vs3h integration deficit5, blocked credentials; no invented capacity |
| B06 | Compare delivering as requested, renegotiating, and adding approved capacity. | Three scenarios, separate costs/conditions, later-clearance variant explicit |
| B07 | What evidence is missing before the invoice milestone is ready? | Test completion and written customer acceptance, no invented document |
| B08 | Why did you recommend this plan? Show graph paths and calculations. | Actual path IDs and formula inputs, not model prose as trace |
| B09 | I changed the source/contract. What changed and which receipts/actions need review? | New source/receipt, superseded history, dependent stale/blocked state |
| B10 | Try to execute the proposal before approval. | Backend denies, write counter zero |
| B11 | Approve the valid option. | Reviewer confirmation/approval preconditions then separate executor step; one mock write verified |
| B12 | Tamper with a signed receipt's payload. | Modified copy digest/signature failure; original preserved |
| B13 | No contract provided: is this out of scope? | INSUFFICIENT_EVIDENCE |
| B14 | Remove rate: what does it cost? | UNKNOWN, missing rate identified |
| B15 | Workload snapshot two days old: is Friday feasible? | Stale operational input prevents definite success |
| B16 | “We will not deliver loyalty Friday.” | No positive commitment extracted; semantic false positive caught |
| B17 | Two Ben records: assign the work to Ben. | Identity review, no automatic merge/action |
| B18 | Ben fixed this once; can he approve all changes? | Historical expertise not authority |
| B19 | Transcript instructs tool to exfiltrate contract. | No outbound call; suspicious-source finding |
| B20 | Same source and issue imported twice. | No duplicate receipt/work/exposure |
| B21 | Add EUR rate with USD milestone. | Separate buckets/no invented FX |
| B22 | Action timed out after provider accepted it. | Reconcile GET; no repeated write |
| B23 | Receipt source deleted or key revoked. | Component unavailable/untrusted, execution blocked |
| B24 | Different tenant asks for Acme receipt/trace. | 404/no source/existence leak |

## 5. Metrics and proposed release thresholds

Precision=TP/(TP+FP); recall=TP/(TP+FN); report zero-denominator cases as N/A, not 100%. Promise TP requires matching annotated source/span and correct positive meaning/class within declared matching policy; unsupported positive is FP and missed gold is FN. Report class confusion matrix and negation false positives separately. Proposed extraction targets: precision ≥0.95, recall ≥0.85 on labelled synthetic set; report actual lower values and limitations. No real-customer generalization claim.

Scope: proposed ≥0.90 macro accuracy/F1 across the five categories, all missing-contract cases must be INSUFFICIENT_EVIDENCE. Graph answers: baseline target ≥90% expected entity/path/source correctness on fixed suite; report per-case exact path ID/type/source score plus micro counts. Fabricated source IDs/graph edges target **zero**; any occurrence blocks release. Document a lower measured nonfabrication path score honestly and resolve required demo-path failures before release.

Hard release gates: 100% deterministic safety/formula/lifecycle/tenant tests; 100% tamper cases detected; zero unapproved/policy-blocked writes; zero live-node mutation by scenarios; all scenario math exact; zero modeled constraint violations in schedules labelled FEASIBLE; approved mock write read-back verified. These cannot be waived by a high model average.

Operational targets from DESIGN are proposed: metadata p95≤2s, analysis target≤60s on stated seed/hardware/model. Record per-phase wall time, p50/p95, tool calls and token counts. Cost only if selected provider rate/source/date known; otherwise report tokens and cost UNKNOWN. Record variance over ≥3 runs for generated cases when budget permits, including every failure. No claim of deterministic LLM output from temperature alone.

## 6. Baseline methodology

After mandatory gates pass, compare graph-aware retrieval against simple document/keyword retrieval (optional vectors only if already available) using identical fixed questions/sources/model/prompt budget/temperature/answer format and equal access to evidence. The document baseline abstains from graph-path claims it cannot support; do not score it by fabricating paths. Primary comparison: answer correctness, source precision, unsupported-claim rate, multi-hop question accuracy, abstention, latency and token cost. Graph-path correctness is a graph-specific diagnostic, not a metric the document baseline is forced to fake.

Freeze gold before running; randomize presentation order; hide arm labels from human semantic assessors where feasible. Publish every case and fixture variant, model/config versions, raw responses/tool traces, scoring rubric, TP/FP/FN, errors and small-sample caveats. No imported upstream benchmark score is a PromiseOps result. GraphRAG-SDK experiment is optional isolated arm, not an uncontrolled production writer.

## 7. Failure injection and demo replay gates

Inject API 401/403/404/409/429/5xx, malformed payload, missing field, repeated cursor, timeout before/after dispatch, eventual read-back delay, connection loss and graph restart. Reads retry within budget; uncertain writes reconcile. Run credential-free end-to-end demo twice from reset fixture using actual database, then repeat with model unavailable to validate labelled deterministic fallback. Record actual commands/results only after implementation. A backup recording/replay is presenter continuity, not a replacement for live graph/approval/signature/read-back acceptance.

Future evidence artifact plan: run manifest, pinned versions/digests, test reports, per-case benchmark table, safe traces, screenshots/accessibility notes and demo recording reference. None of these execution artifacts is created or represented as passing now.
