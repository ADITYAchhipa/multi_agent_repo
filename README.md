# PromiseOps + PromiseSeal specification package

PromiseOps helps a B2B implementation company or managed IT service provider connect a customer commitment to signed scope, delivery work, capacity, and billing prerequisites. PromiseSeal is its versioned, verifiable commitment receipt. FalkorDB is the relationship reasoning and application state layer.

**Backend implementation has begun; the complete product is not implemented.** The phase-0
foundation includes health/readiness, strict receipt models, canonical signing, provenance checks,
and tests. See [backend setup](backend/README.md), [actual results and blockers](docs/IMPLEMENTATION_NOTES.md),
and [frontend coordination](docs/BACKEND_COORDINATION.md). Real FalkorDB compatibility is blocked
because Docker is unavailable in the implementation environment; graph writes and action routes
remain unimplemented. The rest of this index describes the preserved specification package.

## Authority and reading order

The preserved [master build specification](PROMISEOPS_PROMISESEAL_CODEX_BUILD_SPEC.md) is the product baseline.
The current backend implementation brief authorizes code. The earlier
[documentation-only task](CODEX_DOCS_ONLY_PROMPT.md) and [CODEX_START_PROMPT.md](CODEX_START_PROMPT.md)
remain historical inputs; their documentation-only restrictions do not govern the newly authorized build.

Read this index, the decision log, design, schema, protocol, API contracts, and test plan before a later implementation task. Follow phases 0–5 only when implementation is separately authorized. Resolve a discrepancy using [DECISIONS_AND_OPEN_QUESTIONS.md](docs/DECISIONS_AND_OPEN_QUESTIONS.md); do not silently override the master. Draft contracts in this package are proposed implementation requirements, not deployed endpoints.

Evidence labels throughout:

- **BASELINE:** specified in the master; not evidence that software exists.
- **VERIFIED-DOC:** observed in a linked public source on 2026-10-12; not executed or compatibility-tested. Browsing results can be cached.
- **DECISION:** a blueprint choice resolving an implementation detail; recorded in the decision log.
- **ASSUMPTION / TARGET:** synthetic input or proposed acceptance threshold, not measured fact.
- **OPEN:** requires owner input, source verification, or an implementation spike. Optional connectors do not block the fixture workflow.

## Product and scope

Delivery directors, project managers, account managers, and operations leads need to answer: “What did we promise, is it in scope, can we deliver, what money is at risk, and what can we safely do next?” Today the evidence sits in separate transcripts, contracts, Jira tickets, workload systems, and acceptance documents.

The MVP imports synthetic sources, extracts reviewable commitments, traverses a real FalkorDB graph, calculates exposure, compares three scenarios, challenges assumptions, issues signed receipts, and performs one approved mock workload action with read-back. Live Microsoft Graph, Vexa, and Jira integrations are optional. The real workload API is **unspecified** until its owner supplies the contract. Application-owned normalized fields in these documents are not claims about that API.

Excluded: legal advice or legal enforceability claims, autonomous customer communication, payments, contract amendment, employee scoring, blockchain, W3C VC conformance, additional application databases, unrestricted agent tools, and framework proliferation. PDF/DOCX, vector search, and live writes beyond the mock workflow are stretch scope.

## Document index

| Document | Purpose |
|---|---|
| [DESIGN](docs/DESIGN.md) | Personas, requirements, journeys, screens, permissions, failure and accessible UI states |
| [IMPLEMENTATION_PLAN](docs/IMPLEMENTATION_PLAN.md) | Future phases, dependencies, compatibility spikes, milestones, work split and gates |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | Components, trust boundaries, sequence, graph publication and recovery |
| [FALKORDB_SCHEMA](docs/FALKORDB_SCHEMA.md) | Authoritative labels, edges, invariants, provenance, temporal model and query catalogue |
| [PROMISESEAL_PROTOCOL](docs/PROMISESEAL_PROTOCOL.md) | Authoritative receipt payload, canonicalization, lifecycle and verification |
| [AGENT_DESIGN](docs/AGENT_DESIGN.md) | Bounded roles, structured proposals, tools, policy and stop conditions |
| [GRAPH_QUALITY_FIREWALL](docs/GRAPH_QUALITY_FIREWALL.md) | Validation, quarantine, conflict review and safe repairs |
| [COUNTERFACTUAL_SIMULATOR](docs/COUNTERFACTUAL_SIMULATOR.md) | Deterministic scheduling, costs, isolation, uncertainty and comparison |
| [INTEGRATIONS_AND_REPOSITORY_AUDIT](docs/INTEGRATIONS_AND_REPOSITORY_AUDIT.md) | Sources actually inspected, licenses, reuse boundaries, primary/fallback matrix and OPEN checks |
| [API_CONTRACTS](docs/API_CONTRACTS.md) | Authoritative application routes, DTOs, errors, adapter boundaries and concurrency rules |
| [SECURITY_AND_THREAT_MODEL](docs/SECURITY_AND_THREAT_MODEL.md) | Assets, threats, access policy, secrets, privacy and control coverage |
| [DATA_INGESTION_AND_PROVENANCE](docs/DATA_INGESTION_AND_PROVENANCE.md) | Source versions, parsing, evidence, incremental updates and deletion |
| [TEST_AND_EVALUATION_PLAN](docs/TEST_AND_EVALUATION_PLAN.md) | Test IDs, adversarial suite, real database gates and proposed metrics |
| [DEMO_SCRIPT](docs/DEMO_SCRIPT.md) | Five-minute scene plan and judge reproduction |
| [CONFIGURATION_AND_DEPLOYMENT_PLAN](docs/CONFIGURATION_AND_DEPLOYMENT_PLAN.md) | Future environment catalogue, topology, backups, health and operations |
| [DECISIONS_AND_OPEN_QUESTIONS](docs/DECISIONS_AND_OPEN_QUESTIONS.md) | Baseline conflicts, decisions, assumptions and owner questions |
| [TRACEABILITY_MATRIX](docs/TRACEABILITY_MATRIX.md) | Requirement → design → graph → API → test → acceptance → demo |
| [GLOSSARY](docs/GLOSSARY.md) | Canonical terminology and state namespaces |
| [CHANGELOG](docs/CHANGELOG.md) | Document inventory, verification limits and documentation checks |
| [SEED_SCENARIO](docs/SEED_SCENARIO.md) | Additional fictional source text, IDs, schedules, expected arithmetic and graph paths |

## Key concepts and glossary

A **promise / commitment** is a candidate business undertaking; extraction alone does not confirm it. **Evidence** is a retained source version plus a validated quote or structured field pointer. A **receipt** is a signed or unsigned immutable payload version. **Confirmation** records an authorized application user's review; it is not customer acceptance or a legal signature. A **scope gap** is a supported possible mismatch with contract scope. **Exposure** separates estimated cost, milestone value at risk, and renewal context. A **scenario** is an isolated set of hypothetical changes. A **verified action** has server approval, an execution record, and matching external read-back. **Graph provenance** explains the origin and validation of a relationship. See the [full glossary](docs/GLOSSARY.md).

## How a future developer should proceed

1. **Review the decision log and complete phase-0 compatibility spikes.** Preserve the original inputs, review D01–D18/Q01–Q09, and record tested versions, image digests and compatibility evidence.
2. **Freeze contracts and implement the no-LLM graph/receipt core.** Freeze API, ontology, receipt and fixture contracts; build and verify the deterministic source → graph → receipt path.
3. **Add the UI, bounded agents, and approved mock action.** Follow phases 2–4, including server-enforced approval, safe execution and verified read-back.
4. **Run the real-FalkorDB tests and reproducible demo before enabling live integrations.** Pass the mandatory gates and repeat the credential-free demo twice; activate each optional live connector only after its own contract, permission and consent checks also pass.

The [implementation checklist](docs/IMPLEMENTATION_PLAN.md#implementation-checklist) maps these four steps to detailed tasks, dependencies and exit gates. Phase 0 is in progress; no full milestone gate is yet complete. The original plan's status labels describe its documentation phase; current results are in implementation notes. Keep demo/live states unmistakable; never guess workload endpoints, fabricate graph paths or interpret a signature as proof of agreement.

Tested backend setup and offline test commands are in [backend/README.md](backend/README.md).
Its graph commands are explicitly unverified follow-up commands, not completed deployment claims.
