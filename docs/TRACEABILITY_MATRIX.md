# Requirements traceability matrix

Status: documentation coverage, not implementation completion. Each row maps a major baseline requirement to future behavior and evidence. R IDs originate in DESIGN §3; T IDs in TEST_AND_EVALUATION_PLAN; D1–D8 are demo scenes (not decision IDs D01–D18). “Extended” means judge reproduction or engineering acceptance outside the five-minute presentation.

| Req / baseline | Design section / component | Schema entities / relationships | API or tool | Test | Proposed acceptance criterion | Phase / demo |
|---|---|---|---|---|---|---|
| R01 import (§2.1/6) | DESIGN §2.1, ingestion service | SourceRecord/SourceVersion/SourceChunk; HAS_SOURCE_VERSION/HAS_CHUNK | sources/upload, operations poll | T01 | Permitted formats retained/hashable, bad types/paths rejected | 1 / D2 |
| R02 compiler (§2.1) | §2.1, Compiler/evidence verifier | PromiseVersion, SourceChunk; PROPOSES/SPOKEN_BY | upload/reprocess; read_source_chunk | T02 | Exact spans, strict class/date schema; no fabricated quote | 3 / D2 |
| R03 scope (§2.2) | §2.2, Graph Investigator | Contract/Clause/ChangeOrder; POSSIBLY_COVERED_BY/HAS_CLAUSE | chat/Q02 | T03 | Five-state qualified result with clauses; absent contract insufficient | 3 / D3 |
| R04 margin (§2.3/7) | §2.2, Decimal calculator | RateCard/WorkloadSnapshot/Milestone; USES_RATE/AFFECTS | chat/simulations/F01–F06 | T04 | Exact math, units/currency/input provenance, no overlapping total | 1+3 / D4 |
| R05 simulator (§2.4/7) | §2.2, pure overlay/scheduler | Scenario, JiraIssue; DEPENDS_ON | POST/GET simulations; simulate_overlay | T05 | Three scenarios, repeatable math, live node values unchanged | 3 / D4 |
| R06 adversarial audit (§2.5) | §2.2, Auditor/Policy | Conflict/Scenario/ActionProposal | agent handoff/P01–P12 | T06 | Invalid/unsafe critique prevents executable recommendation | 3 / D5 |
| R07 receipt crypto (§2.6) | §2.1, signer/verifier | PromiseVersion/AuditEvent; HAS_VERSION/HAS_EVENT | promises/{id}/verify; receipts/verify | T07 | Canonical bytes and valid/negative signature checks | 0+1 / D6 |
| R08 review/history (§0.13/2.6) | §2.1/2.4, receipt service | Promise/Version; SUPERSEDES | review/revoke | T08 | Authorized versioned transitions, revocation separated, history retained | 1+4 / D6 |
| R09 approvals (§2.7) | §2.3/5, approval/policy | ActionProposal/Approval/Person; HAS_APPROVAL/APPROVED_BY | request-approval/approve/reject/execute | T09 | Zero writes until server-valid bound approval/current receipt | 4 / D7 |
| R10 read-back (§2.7/12.6) | §2.3, executor/ledger | ActionProposal/AuditEvent; HAS_EVENT | execute/reconcile/get action | T10 | One approved mock write matches read-back; uncertain writes never blindly retried | 4 / D7 |
| R11 graph core (§0.7/5) | §2.2/4, GraphRepository/UI | Promise→Version→Issue→Person→Workload; clauses/milestones | Q01–Q10, graph/trace | T11 | Real pinned FalkorDB returns expected IDs/directions/evidence | 0–3 / D3+D8 |
| R12 quality (§6) | §2.1/4, firewall | Conflict/KnowledgeFinding; HAS_FINDING/CONFLICTS_WITH | health/knowledge; conflicts/resolve | T12 | Reject unknown ontology/quotes/refs/growth; reviewed safe repair | 1 / D5+Extended |
| R13 incremental sources (§6.1) | §2.4, source service | SourceVersion/OperationRun; HAS_SOURCE_VERSION | reprocess/operations | T13 | NO_CHANGE duplicates; per-source retirement; crash-safe publish | 1 / D2+Extended |
| R14 transcripts (§4.3–5/9.1) | §3 R14, transcript adapter | Meeting/SourceVersion/Chunk; HAS_SOURCE/SPOKEN_BY | upload; vexa/import; optional Graph adapter | T14 | File path works offline; verified optional mapping/consent only | 5 / D2 |
| R15 Jira (§4.6/9.2) | §3 R15, Jira adapter | JiraIssue/SourceVersion; ASSIGNED_TO/DEPENDS_ON | jira/sync; adapter search/read | T15 | Bounded export/sync and explicit custom fields; live writes gated | 4–5 / D3 |
| R16 workload (§9.3) | §3 R16, mock adapter | WorkloadSnapshot/ActionProposal | normalized adapter methods, execute | T16 | No guessed live endpoint; MOCK visible; unconfigured live fails closed | 4 / D7 |
| R17 auth/tenant (§12.4) | §5, auth/ACL service | tenant_id/access_label on all; scoped edges/refs | session; every read/write route | T17 | Two-tenant and role denial across objects/counts/traces | 1–5 / Extended |
| R18 tool/injection security (§12.1–3) | §6, validation/egress policy | Findings/OperationRun/AuditEvent | all tools/adapters | T18 | No instruction-driven privilege/URL/query expansion; no leaked secrets | 3–4 / D5+Extended |
| R19 privacy (§12.5) | §2.4/6, retention service | SourceRecord/Version/Chunk, receipt/audit tombstones | sources/{id}/retire | T19 | Governed erase retires unsupported facts and blocks reliance | 4–5 / Extended |
| R20 primary screens (§10) | §4, UI/API client | All safe read DTOs | baseline reads + actions/connectors list | T20 | Nine real-data screens with evidence/mode/current status | 2–5 / D1–D8 |
| R21 accessibility (§10) | §6, semantic UI/list fallback | Same authorized path DTOs | graph/detail/approval reads | T21 | Keyboard/mobile/zoom/failure paths usable and labelled | 2–5 / all+Extended |
| R22 trace/audit/health (§8/12/13) | §4/6, trace/audit services | GraphState/OperationRun/AuditEvent | trace/{id}, audit/verify, health | T22 | Actual steps, chain checks, safe logs/counts and limitations | 1–5 / D8 |
| R23 synthetic demo (§11/17) | §7, fixture/demo harness | Seed aliases and PTH1–PTH6 | credential-free core workflow | T23 | Twice reproducible with actual graph and approved mock write | 5 / D1–D8 |
| R24 evaluation (§13) | §7, evaluation harness | Gold source/path IDs and result refs | benchmark chat/verify/action calls | T24 | Actual TP/FP/FN, math/safety scores and failures reported | 5 / D8 |
| R25 config/deploy (§3/15/18) | §6, startup/storage/recovery | GraphState/source manifests/action ledger | health; future bootstrap/restore | T25 | Tested pins/config/persistence/restore; no accidental replay on restore | 0+5 / Extended |
| R26 repo reuse (§4) | §3 R26, adapter/package boundaries | No second writer/database | S01–S09 version/license ledger | T26 | Actual inspected sources, narrow reuse, OPEN gates for enabled integrations | 0+5 / Extended |
| R27 bounded agents (§3.2) | §2.2/6, orchestrator | OperationRun/Scenario/AuditEvent | agent-result-v1 / named tools | T27 | Five graph calls/two revisions, strict handoffs, safe model failure | 3 / D4+D5 |
| R28 billing evidence (§1/2.3/11) | §2.2, readiness calculator | Milestone/AcceptanceRequirement; REQUIRES/SATISFIED_BY | Q05/F07/chat | T28 | Task completion alone never READY; no invoice write | 3 / D5 |
| R29 freshness (§6/7/12.6) | §2.4/6, dependency invalidation | SourceVersion/Scenario/ActionProposal | Q06/approve/execute | T29 | Changed/stale target/evidence invalidates bound approval | 4 / Extended B09 |
| R30 expertise/identity (§2.5/6/11) | §2.1/5, identity and policy | Person/Chunk/Findings; SPOKEN_BY/ASSIGNED_TO | resolve_entity/conflict review | T30 | No first-name merge or expertise-as-authority | 1+3 / D5 |
| R31 limits/claims (§0.12/19) | §3/7, scope governance | No extra DB/unsafe action labels | no unrestricted shell/Cypher/HTTP/payment tools | T31 | Honest receipt/risk/production boundaries and non-goals | 5 / D6+D8 |
| R32 docs-only (current task) | README/decision D01 | Schema is documentation only | No application endpoints implemented | T32 | Required files, preserved inputs, no executable/application edits | Current phase / N/A |

## Coverage of baseline definition of done

Master §18 startup/seed → R25/R23; demo/mock → R16/R20; upload/hash/idempotency → R01/R13; invalid relation/quote health → R02/R12; proposed/confirmed → R08/R09; signature and version chain → R07/R08; scope evidence → R03; actual graph joins → R11; math/isolation → R04/R05; auditor/policy gate → R06/R09; approved mock read-back → R10/R16; connector failure independence → R14–R16/R23; tenant tests → R17; secrets/privacy → R18/R19; actual benchmark → R24; setup/safety/demo documentation → R25/R32.

## Contract cross-check rules

Authoritative route table: API_CONTRACTS. Graph labels/types: FALKORDB_SCHEMA. Business/receipt transitions and canonical profile: PROMISESEAL_PROTOCOL. Action transitions: API_CONTRACTS. Tool/role permissions: AGENT_DESIGN and DESIGN §5. Phase order: IMPLEMENTATION_PLAN. Numbers/IDs/calendar: SEED_SCENARIO. Terminology: GLOSSARY. Every later implementation change must update its owning contract, affected traceability rows and tests before being described as complete.
