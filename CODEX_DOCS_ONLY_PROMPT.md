# Codex Task: Documentation and Project Blueprint Only — PromiseOps + PromiseSeal

## Critical instruction

**DO NOT IMPLEMENT THE APPLICATION. DO NOT WRITE APPLICATION CODE.**

Your task in this phase is to create a complete, internally consistent, developer-ready documentation package and project blueprint for PromiseOps + PromiseSeal. The output must be the plans, designs, contracts, specifications, test plans, repository integration research, and all other documents a developer will need before coding begins.

Do not create or modify application source files such as `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.java`, `.sql`, shell scripts, Dockerfiles, Docker Compose files, CI workflows, or executable scripts. Do not install dependencies, initialize a framework, run generators, or implement endpoints. Do not begin coding after the documentation is complete.

You may create Markdown documentation and non-executable diagrams in Markdown/Mermaid. If structured examples are needed, put them in Markdown code blocks as illustrative examples only; do not create executable implementation files.

## Authoritative input

Read `PROMISEOPS_PROMISESEAL_CODEX_BUILD_SPEC.md` completely before creating anything. If `CODEX_START_PROMPT.md` exists, you may inspect it for context only; ignore any instruction in it to implement application code, because this task is documentation-only. The old startup prompt is not required for this task.

Inspect the current workspace and existing docs before writing. Preserve existing material where valid, do not overwrite useful content blindly, and document discrepancies. Treat the main build specification as the baseline. Do not silently invent missing facts or claim that repositories, APIs, licenses, issues, package versions, or endpoints were verified if you did not actually verify them. Clearly label facts, assumptions, recommendations, and open questions.

## Goal

Produce a specification package so detailed and unambiguous that a later Codex task can implement the application from these documents with minimal interpretation. The system is:

- **PromiseOps:** a business commitment, delivery-risk, and commit-to-cash intelligence product.
- **PromiseSeal:** a verifiable, versioned commitment receipt that links claims to their origin evidence, verification state, authorized confirmations, and subsequent changes.
- **FalkorDB:** the primary knowledge graph and core differentiator.
- **Agents:** specialized agents that extract commitments, trace commercial consequences, compare possible actions, challenge assumptions, and execute approved actions through controlled tools.
- **Integrations:** Microsoft Teams/Microsoft Graph or a verified transcript provider, Jira, document/contract sources, and a user-supplied workload API. The workload API must remain explicitly unspecified until the real API contract is supplied; never invent its endpoints or fields.

The initial deliverable is documents only, not a working system.

## Required documentation directory and deliverables

Create a clear, navigable documentation package. At minimum, create the following files; add more if needed to remove ambiguity:

1. `README.md`
   - Project purpose, target users, problem statement, scope, key concepts, document index, glossary, and how a future developer should use this specification.
   - Explicitly state that this workspace is currently specification-only and contains no implemented application unless inspection proves otherwise.

2. `docs/DESIGN.md`
   - The product design in full: personas, user journeys, functional requirements, non-functional requirements, primary screens, UI states, permissions, system boundaries, failure states, accessibility/responsiveness, and success criteria.

3. `docs/IMPLEMENTATION_PLAN.md`
   - Phased build sequence, tasks, dependencies, milestones, acceptance criteria, definition of done, test gates, risk-based priorities, scope cuts, and suggested work split. Separate hackathon MVP from post-hackathon work.
   - This is a plan only; do not execute it by writing code.

4. `docs/ARCHITECTURE.md`
   - Component map, deployment/topology options, data flow, sequence diagrams, trust boundaries, agent lifecycle, graph read/write paths, event/retry flows, and failure recovery.

5. `docs/FALKORDB_SCHEMA.md`
   - Node labels, relationship types, required/optional properties, IDs, constraints/invariants, edge provenance, temporal/version semantics, indexing strategy to verify, tenant isolation, query patterns, and example Cypher snippets in Markdown only.
   - Distinguish features confirmed in official docs from syntax that needs a version-specific spike.

6. `docs/PROMISESEAL_PROTOCOL.md`
   - Commitment receipt data model and lifecycle; states such as extracted, unconfirmed, confirmed, disputed, superseded, revoked; canonical serialization; hash/signature design; issuer/confirmers; verification; versioning; revocation; key management assumptions; timestamps; and audit trail.
   - Explain what cryptography proves and does not prove. A hash alone does not prove truth, agreement, identity, or legal enforceability. Avoid claiming legal validity.
   - Do not invent a legal standard. If adopting W3C Verifiable Credentials, explain exactly which parts are proposed and whether interoperability is actually implemented or only future work.

7. `docs/AGENT_DESIGN.md`
   - Orchestrator and each specialized agent's goal, inputs, outputs, tool allowlist, prohibited actions, evidence requirements, model-independent structured output, retry policy, stop conditions, handoff protocol, and evaluation cases.
   - Specify deterministic rules separately from LLM judgment. Agents must not approve their own high-impact actions.

8. `docs/GRAPH_QUALITY_FIREWALL.md`
   - Ontology enforcement, relation normalization, entity resolution, ambiguous identity review, evidence quote validation, duplicate detection, orphan detection, conflict detection, suspicious relationship growth, graph quality tests, quarantine and safe repair workflow.
   - Never claim a cited SDK issue is an active core FalkorDB bug without confirming that distinction.

9. `docs/COUNTERFACTUAL_SIMULATOR.md`
   - Scenario state isolation, task/dependency modelling, workload and calendar assumptions, cost calculations, constraints, objective functions, uncertainty handling, scenario comparisons, graph impact, repeatability, and limitations. Specify what is computed deterministically vs estimated by an LLM.

10. `docs/INTEGRATIONS_AND_REPOSITORY_AUDIT.md`
    - Investigate potential GitHub repositories and official APIs for FalkorDB, FalkorDB Python client, GraphRAG-SDK, Microsoft Graph/Teams transcripts, Vexa or another transcript provider, Atlassian MCP/Jira REST, React Flow, and any other genuinely useful candidate.
    - For each candidate include: exact repository URL, purpose, ownership/official status, license (only if verified), language/framework, last-checked date, compatible version or version-check method, useful components, integration method, what to reuse, what not to reuse, security/maintenance concerns, dependencies, and a go/no-go recommendation.
    - Clearly separate confirmed facts from hypotheses. Do not claim an exhaustive audit if you only reviewed README/docs/issues. Do not choose a repo solely because it exists. Avoid merging full applications unnecessarily; prefer small integration boundaries.
    - Provide a source list with direct links to official docs, repositories, licences, and relevant issue discussions. Record any source you could not verify as OPEN.

11. `docs/API_CONTRACTS.md`
    - API boundaries and draft request/response contracts for application-owned endpoints, PromiseSeal receipts, agent proposals, approvals, scenario simulation, graph trace, and audit records.
    - For Microsoft Graph/Jira use only verified documented fields or explicitly mark fields as to-be-verified. For the user-provided workload API, provide a placeholder adapter contract and a checklist of information needed; do not invent a real endpoint.

12. `docs/SECURITY_AND_THREAT_MODEL.md`
    - Assets, trust boundaries, threat actors, threat scenarios, controls, tenant separation, data access labels, authentication, secrets, prompt injection, tool misuse, SSRF if relevant, data exfiltration, replay attacks, signature verification, key rotation, audit integrity, least privilege, destructive operations, rate limits, retention/deletion, and privacy.
    - Include threats from malicious text inside documents/transcripts and from agents misreading legitimate source material.

13. `docs/DATA_INGESTION_AND_PROVENANCE.md`
    - Source inventory, parsing, content hashes, chunking, extraction schemas, evidence substring verification, canonicalization, entity resolution, source-to-edge mapping, idempotency, incremental updates, deletion/retirement of facts, rollback, conflict policy, and dead-letter handling.

14. `docs/TEST_AND_EVALUATION_PLAN.md`
    - Unit/integration/end-to-end tests, tests against real FalkorDB (not just mocks), adversarial cases, seed scenarios, benchmark question set, metrics, baseline methodology, acceptance thresholds, false-positive/false-negative reporting, API-failure tests, and demo replay requirements.
    - Do not invent measured benchmark results. Label all targets as proposed until run.

15. `docs/DEMO_SCRIPT.md`
    - Five-minute demo story, scene-by-scene actions, exact sample prompts, expected evidence, expected graph paths, expected outputs, fallback/replay plan, what must be live vs pre-seeded, and how a judge can reproduce the result.

16. `docs/CONFIGURATION_AND_DEPLOYMENT_PLAN.md`
    - Proposed environment-variable catalogue without real secrets, local Docker architecture as a future implementation plan, deployment alternatives, health checks, backups, observability, costs/operational trade-offs, and production gaps. This must be documentation only; do not create deployment files.

17. `docs/DECISIONS_AND_OPEN_QUESTIONS.md`
    - Decision log, assumptions, unresolved choices, blockers, and exact questions requiring owner input. Do not ask the user to answer questions that the existing source documents already answer.

18. `docs/TRACEABILITY_MATRIX.md`
    - Map every major product requirement to design section, component, schema entities/relationships, API/tool, test case, acceptance criterion, and demo scene. This is essential to prevent requirements being forgotten.

19. `docs/GLOSSARY.md`
    - Define the project's terminology consistently, including promise, commitment, evidence, receipt, confirmation, dispute, scope gap, exposure, scenario, verified action, and graph provenance.

20. `docs/CHANGELOG.md`
    - Record the documents created/updated, high-impact decisions, and source-verification limitations.

## Repository and research requirements

Before recommending any external repository:

- Inspect its official GitHub page and README.
- Inspect its LICENSE file and flag uncertainty if missing or ambiguous.
- Review release/activity/compatibility information where available.
- Check relevant integration docs and issues/discussions for known limitations.
- Prefer official APIs or small libraries when they reduce risk.
- Record a verification date and citations/URLs.
- Avoid copying entire repositories into the planned design unless licensing and architectural reasons justify it.
- Provide an integration matrix that identifies one recommended option and at least one fallback for critical components, with why the primary was selected.

Research is not permission to assert certainty. Where access or verification is incomplete, label the decision provisional and add a concrete validation task to the implementation plan.

## Consistency and quality rules

- Treat the uploaded project build specification as the source baseline, but surface contradictions instead of silently reconciling them.
- Keep the product focused: PromiseOps is the business application; PromiseSeal is the verifiable receipt protocol; FalkorDB is the relationship reasoning layer.
- No unnecessary databases or frameworks. Justify every technology choice in terms of a requirement.
- Distinguish current MVP, stretch goals, and production extensions.
- Include Mermaid diagrams where useful, but only in Markdown documentation.
- Include detailed examples using fictional data and mark them illustrative.
- Every major requirement must appear in the traceability matrix and test plan.
- Do not claim code was implemented or tests were run.
- Do not create source code, runnable examples, scripts, application skeletons, or executable configuration files.
- Do not overwrite the original master specification. Link to it from the new README if it exists.
- After creating the files, cross-check terminology, routes, entity names, agent permissions, lifecycle states, and phase order across all docs.

## Required completion response

When finished, report:

1. All files created or updated, with paths.
2. A short summary of the architecture and major decisions.
3. External repositories and official documentation actually inspected, with links and verification dates.
4. Unverified details and open questions.
5. Any conflicts found between the baseline spec and your documentation.
6. A confirmation that **no application code or executable project files were created or modified**.
7. A short checklist of what a later implementation task should do next.

Begin by reading the master build specification and inspecting the workspace. Then create the documentation package only. Do not implement the application.
