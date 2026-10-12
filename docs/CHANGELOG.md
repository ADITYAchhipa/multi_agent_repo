# Documentation changelog

## 2026-10-12 — Explicit four-step implementation checklist

Updated `README.md` and `docs/IMPLEMENTATION_PLAN.md` to include the four requested next steps explicitly: decision review/phase-0 spikes; contract freeze/no-LLM core; UI/bounded agents/approved mock action; real-FalkorDB tests/reproducible demo before live integration activation. Each checklist item now identifies its detailed phases, outputs and milestone gates. All four are marked NOT STARTED.

Clarified that optional live application integrations stay disabled until the credential-free M5 acceptance gate passes, in addition to each connector's contract/consent/permission checks. Earlier explicitly authorized isolated sandbox compatibility checks remain distinct from application activation. This entry records documentation changes only; no compatibility spike, application implementation, application test or external API call was executed.

## 2026-10-12 — Specification package v1

Created a documentation-only project blueprint from the completely read 1,077-line PROMISEOPS_PROMISESEAL_CODEX_BUILD_SPEC.md and inspected CODEX_DOCS_ONLY_PROMPT.md. Workspace inspection found only three Markdown inputs, no application implementation and no Git repository. CODEX_START_PROMPT.md was preserved; its contents were not needed for this task. No original input was edited.

### Files created

1. `README.md` — purpose, scope, authority, index, glossary summary and developer reading order.
2. `docs/DESIGN.md` — personas, journeys, R01–R32, screens, permissions and non-functional targets.
3. `docs/IMPLEMENTATION_PLAN.md` — future phases 0–5, S01–S09 spikes, gates, cuts and production sequence.
4. `docs/ARCHITECTURE.md` — topology, trust boundaries, sequences, publication and recovery.
5. `docs/FALKORDB_SCHEMA.md` — label/property/edge catalogue, temporal provenance, invariants and query templates.
6. `docs/PROMISESEAL_PROTOCOL.md` — payload, canonical bytes, signing, review, revocation and verification.
7. `docs/AGENT_DESIGN.md` — typed role handoffs, tools, policy rules, limits and evaluation cases.
8. `docs/GRAPH_QUALITY_FIREWALL.md` — validation, quarantine, identity/conflicts/growth and repair.
9. `docs/COUNTERFACTUAL_SIMULATOR.md` — scheduling, formulas, isolation, objectives and limitations.
10. `docs/INTEGRATIONS_AND_REPOSITORY_AUDIT.md` — inspected source links, licenses, release observations, decisions/fallbacks and OPEN gates.
11. `docs/API_CONTRACTS.md` — baseline routes, justified extensions, shared DTOs, transitions and adapter placeholders.
12. `docs/SECURITY_AND_THREAT_MODEL.md` — threats/controls, ACL, auth, keys, privacy and gaps.
13. `docs/DATA_INGESTION_AND_PROVENANCE.md` — parsing, immutable versions, evidence, updates, deletion and recovery.
14. `docs/TEST_AND_EVALUATION_PLAN.md` — T01–T32, B01–B24, real database and proposed metric gates.
15. `docs/DEMO_SCRIPT.md` — D1–D8, judge reproduction and honest fallback/replay.
16. `docs/CONFIGURATION_AND_DEPLOYMENT_PLAN.md` — proposed env catalogue, local/production topology, backup and operations.
17. `docs/DECISIONS_AND_OPEN_QUESTIONS.md` — D01–D18, assumptions, contradictions and Q01–Q09.
18. `docs/TRACEABILITY_MATRIX.md` — complete R01–R32 crosswalk and baseline definition-of-done coverage.
19. `docs/GLOSSARY.md` — canonical terms and distinct state namespaces.
20. `docs/CHANGELOG.md` — this record.
21. `docs/SEED_SCENARIO.md` — additional fictional source excerpts, IDs, schedules and hand-derived expected results.

### High-impact choices

Preserved the baseline stack, central FalkorDB, typed bounded orchestrator, package/API consumption, file-first sources and mock-first workload action. Added immutable SourceVersion, explicit acceptance requirement/run/revision state; finalized relationship endpoints; separated business confirmation, receipt integrity/standing and approval; added NEEDS_RECONCILIATION; defined canonical bytes; made source deletion's verification impact explicit; bound approval to target/evidence versions; specified synthetic hours/calendar/costs. All are explained in decisions D01–D18.

### Research limitations and corrections

Public sources checked 2026-10-12 through available web retrieval, sometimes cached. Repository pages, README/licenses, release views, official API/crypto/standard docs and selected issue discussions were inspected; no exhaustive source/dependency/security audit or runtime compatibility test. FalkorDB 6.x transition requires a pinned compatibility/restore spike. SDK #284 is concurrent-update discussion; bulk relationship writes are #283, correcting the master citation description. These reports are not established active core database defects.

Jira issue read/create/edit reference retrieval failed twice; exact contracts remain OPEN. Baseline GraphRAG-SDK repository docs paths also failed retrieval. FalkorDB Browser's attempted LICENSE path returned 404; LICENSE.txt was then found and verified. Model/provider choice, real workload API and live credentials are not supplied. The repository audit records all narrow reuse decisions and remaining checks. No package versions are declared tested/compatible.

### Input preservation manifest

SHA-256 values recorded before documentation writes; final documentation check must compare these unchanged inputs:

| Original file | SHA-256 |
|---|---|
| PROMISEOPS_PROMISESEAL_CODEX_BUILD_SPEC.md | `edb4fb32466e2dcf86fdf7965be5835909e0681d8862058bc648659e4a40b3a7` |
| CODEX_DOCS_ONLY_PROMPT.md | `d4ad9fd10c9946b1f9d693675d3735486fee232285b71893b9b7cb71cf8f097e` |
| CODEX_START_PROMPT.md | `f20daef85ac56da6282df8ad9741cb94320a96b87ee6311a3dd921680952499e` |

### Documentation validation status

Read-only documentation checks completed: 21 new Markdown documents, 24 total workspace files, 40 valid local document links, 46 structurally consistent Markdown tables, balanced fenced blocks, all 32 requirements and 32 test groups present, and all 22 baseline API routes represented. Three original SHA-256 values match the preservation manifest. Recursive inventory found no non-Markdown files. Enum pipes inside table code spans were escaped for correct Markdown rendering.

Cross-document review checked terminology, seven user-visible promise labels versus receipt standing, action reconciliation, graph labels/endpoints, adapter permissions, phases 0–5, workload nonconfiguration and fictional amounts/calendar. Follow-up clarifications froze proposal/content hash field sets, receipt-to-graph field mappings, receipt-evidence eligibility versus action authorization, and internal reservation approval versus independent customer change-order conditions. These are documentation checks only, not application test results. No application source, executable configuration, dependencies, framework, endpoints, datasets, runtime scripts or deployment files were created or modified.
