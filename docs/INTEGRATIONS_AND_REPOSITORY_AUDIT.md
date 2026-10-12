# Integrations and repository audit

**Verification date for every entry: 2026-10-12. Scope: public repository pages, README/license files, visible release information, official documentation and selected issue discussions.** No repository was cloned, installed, executed, vulnerability-scanned or exhaustively reviewed. No external API credentials were used. Browsing may serve cached snapshots; dates/tags below are observed values, not guaranteed latest releases or compatibility pins. No source code is copied into this workspace.

Fact labels: VERIFIED-DOC = inspected source supports the claim; RECOMMENDATION = architectural judgment; OPEN = unverified contract/version/operational behavior. All go decisions are provisional until the relevant phase-0 spike passes. License identification is file inspection, not a legal conclusion about a particular distribution/service arrangement.

## 1. Integration decision matrix

| Critical boundary | Recommended option | Fallback | Why / cut line |
|---|---|---|---|
| Knowledge/state database | Official FalkorDB image, version+digest locked after S01 | Another tested supported FalkorDB release or approved managed FalkorDB | Fixed product requirement; no replacement database and no fake graph fallback |
| Python graph access | Official falkordb-py, one chosen async or sync/threadpool style | Tested earlier client/server pair; sync threadpool if async behavior fails | Small controlled repository layer; no SDK second writer |
| Meeting evidence | FileTranscriptProvider with synthetic VTT | Optional Microsoft Graph if tenant configured; Vexa if provider approved | Fixture works without credentials; both live options behind one normalization boundary |
| Jira evidence | Synthetic export then official REST v3 read-only adapter | Reimport approved exports; remote Atlassian MCP only in later evaluated environment | Deterministic mapping/pagination/read-back; do not embed another application |
| Workload | Deterministic MockWorkloadAdapter | Manual approved export for read-only analysis | Real API unknown; no live-write fallback until contract supplied |
| Graph UI | @xyflow/react with backend graph DTO | Accessible relationship/path table using same DTO | Never sacrifice evidence correctness for visualization |
| Cryptographic attestation | cryptography Ed25519 + explicit canonical profile | Tested prior supported package; otherwise unsigned PROPOSED receipts with execution blocked | Never substitute home-grown crypto or treat unsigned as signed |
| Generated analysis | Configured model adapter with validated outputs | Deterministic graph/calculation answer; labelled prerecorded extraction for replay only | Model availability cannot bypass evidence or policy |
| Source artifacts | Local generated-ID files for demo | Backup/restore of same artifacts; production approved object storage | No extra application database; original bytes retained |

## 2. Repository candidates

Each record includes exact repository, README, license, release/activity and limitation evidence. Language/framework is scoped to what was observed; transitive compatibility remains OPEN.

### A01 — FalkorDB server: GO, mandatory, pin after S01

VERIFIED-DOC: [official FalkorDB repository](https://github.com/FalkorDB/FalkorDB), [README](https://github.com/FalkorDB/FalkorDB/blob/main/README.md), [LICENSE](https://raw.githubusercontent.com/FalkorDB/FalkorDB/main/LICENSE) identify the graph server and SSPL v1. Main README describes the Rust implementation; release notes distinguish 6.x Rust and older 4.x C engines. [Releases](https://github.com/FalkorDB/FalkorDB/releases) displayed v6.0.2 and describe replication/packaging differences across major versions. This is an active release surface, not a compatibility result.

RECOMMENDATION: consume official image, zero upstream files copied; use graph properties/traversals and typed Cypher writes. Do not compile/fork server or assume every documented newer index exists in selected image. Dependencies: Redis-module runtime, image architecture, persistence/storage and official client. Review server licensing for actual deployment/distribution before commercialization. S01 must test parameterized queries, atomic publication, constraints/indexes, persistence/restore and image digest. Do not mix incompatible major versions in a replication plan. [Official command reference](https://docs.falkordb.com/commands/graph.ro-query), [index documentation](https://docs.falkordb.com/cypher/indexing).

### A02 — FalkorDB Python client: GO, mandatory, pin after S01

VERIFIED-DOC: [official repository](https://github.com/FalkorDB/falkordb-py), [README](https://raw.githubusercontent.com/FalkorDB/falkordb-py/main/README.md), [MIT license](https://raw.githubusercontent.com/FalkorDB/falkordb-py/main/LICENSE). Python client README demonstrates synchronous and asynchronous usage, select_graph, query and ro_query. [Releases](https://github.com/FalkorDB/falkordb-py/releases) displayed v1.7.1. [Issue #243](https://github.com/FalkorDB/falkordb-py/issues/243) reports schema-cache behavior after graph deletion/recreation; not reproduced here and not assumed to affect the selected pair.

RECOMMENDATION: one package behind GraphRepository; zero copied files. Start with async if tested, otherwise sync in bounded threadpool. Dependencies include redis client/runtime compatibility; exact constraints/pool/thread safety are OPEN until S01. Include graph reset/reconnect/cache invalidation in tests. Do not expose graph deletion/copy/query methods as model tools. [Issue index reviewed](https://github.com/FalkorDB/falkordb-py/issues).

### A03 — GraphRAG-SDK: NO-GO on MVP critical path; optional isolated experiment

VERIFIED-DOC: [FalkorDB-owned repository](https://github.com/FalkorDB/GraphRAG-SDK), [README](https://raw.githubusercontent.com/FalkorDB/GraphRAG-SDK/main/README.md), [Apache-2.0 license](https://raw.githubusercontent.com/FalkorDB/GraphRAG-SDK/main/LICENSE). README presents Python GraphRAG ingestion/retrieval, custom schema and incremental updates. [Releases](https://github.com/FalkorDB/GraphRAG-SDK/releases) displayed v1.4.0. [#285](https://github.com/FalkorDB/GraphRAG-SDK/issues/285), [#284](https://github.com/FalkorDB/GraphRAG-SDK/issues/284), [#283](https://github.com/FalkorDB/GraphRAG-SDK/issues/283) were inspected for relationship vocabulary, concurrent update and bulk-write concerns respectively; no issue was reproduced.

RECOMMENDATION: reuse ideas for grounding/schema and optional benchmark methodology only, zero critical-path imports/copied files. Dependencies include FalkorDB, model/embedding providers and SDK pipeline packages; complete dependency review OPEN. Two graph writers would undermine controlled provenance and receipts. Any later experiment uses a disposable tenant-isolated graph, pinned version, ontology validation and graph diff. Do not attribute these SDK discussions to an active core database defect. Baseline repository paths [getting-started](https://github.com/FalkorDB/GraphRAG-SDK/blob/main/docs/getting-started.md) and [API reference](https://github.com/FalkorDB/GraphRAG-SDK/blob/main/docs/api-reference.md) failed retrieval; OPEN. README links newer hosted docs; verify those before an experiment.

### A04 — Vexa: CONDITIONAL GO as transcript API, not embedded stack

VERIFIED-DOC: [Vexa-ai repository](https://github.com/Vexa-ai/vexa), [README](https://raw.githubusercontent.com/Vexa-ai/vexa/main/README.md), [Apache-2.0 license](https://raw.githubusercontent.com/Vexa-ai/vexa/main/LICENSE). It is the provider's project, not a Microsoft official connector. README describes hosted/self-hosted meeting capture, transcript API and a separate agent plane. [Release view](https://github.com/Vexa-ai/vexa/releases) displayed v0.12.28 with transcript-related fixes. [Issues index](https://github.com/Vexa-ai/vexa/issues) was inspected; no individual Teams limitation was validated in a running deployment.

RECOMMENDATION: call documented transcript retrieval through adapter; zero source copied; no bot creation in MVP. API boundary is language-independent; repository is multi-service, and complete language/framework/dependency inventory remains OPEN (Python/JavaScript-family service details must be confirmed at pinned commit). Self-host prerequisites/operational services add workload irrelevant to PromiseOps core. Exact auth/response schema/platform availability, consent and data-processing terms need S04. Do not import Vexa's agent orchestration or business state store. Fallback synthetic VTT.

### A05 — Atlassian MCP: DEFER; direct Jira REST primary

VERIFIED-DOC: [official Atlassian repository](https://github.com/atlassian/atlassian-mcp-server), [README](https://raw.githubusercontent.com/atlassian/atlassian-mcp-server/main/README.md), [Apache-2.0 license](https://raw.githubusercontent.com/atlassian/atlassian-mcp-server/main/LICENSE). README describes cloud-hosted MCP with OAuth 2.1/API-token options and recommends a v2 transport endpoint. [Releases view](https://github.com/atlassian/atlassian-mcp-server/releases) showed no packaged releases. [Issue index](https://github.com/atlassian/atlassian-mcp-server/issues) reviewed; no transport/tool contract executed.

RECOMMENDATION: remote protocol integration only if a later environment already needs it. Repository license covers repository material, not automatic rights/availability of the hosted service. Hosted implementation language is not established here; local files are integration/configuration/docs, not a self-hostable Jira application to merge. Dependencies: Atlassian account permissions, auth flow, MCP client/tool schemas, service limits. Pin observed tool schemas/capabilities and enforce PromiseOps policy outside MCP. Zero copied source files. Fallback direct REST or synthetic import; do not assume old SSE endpoints remain supported.

### A06 — xyflow / React Flow: GO for graph UI after S03

VERIFIED-DOC: [maintainer repository](https://github.com/xyflow/xyflow), [README](https://raw.githubusercontent.com/xyflow/xyflow/main/README.md), [MIT license](https://raw.githubusercontent.com/xyflow/xyflow/main/LICENSE). React/Svelte libraries share a monorepo; PromiseOps selects only React `@xyflow/react`. [Releases](https://github.com/xyflow/xyflow/releases) displayed React 12.12.0. [SSR documentation](https://reactflow.dev/learn/advanced-use/ssr-ssg-configuration) and [CSS transform/zoom issue #6023](https://github.com/xyflow/xyflow/issues/6023) were reviewed; issue report is not a reproduced blocker.

RECOMMENDATION: package dependency, TypeScript/React consumer, zero copied upstream application files. UI receives real backend paths; disable free graph editing as a fact-creation mechanism. Dependencies: compatible React/Next runtime, CSS/layout sizing, browser interactions; verify package peer ranges and accessible keyboard/list fallback in S03. Prefer client-rendered bounded graph initially; avoid ancestor scaling until zoom/handle tests pass. Pro examples/services have separate terms if considered; none selected. [Issue index](https://github.com/xyflow/xyflow/issues).

### A07 — msteams-mcp: NO-GO for default product path

VERIFIED-DOC: [third-party repository](https://github.com/m0nkmaster/msteams-mcp), [README](https://raw.githubusercontent.com/m0nkmaster/msteams-mcp/main/README.md), [MIT license](https://raw.githubusercontent.com/m0nkmaster/msteams-mcp/main/LICENSE). README describes Node/browser sign-in and direct Teams internal-service/session use (Substrate, chatsvc, CSA). It is not Microsoft official Graph API. [Releases](https://github.com/m0nkmaster/msteams-mcp/releases) and [issues](https://github.com/m0nkmaster/msteams-mcp/issues) inspected; no version selected or runtime compatibility established.

RECOMMENDATION: zero runtime dependency/copied files. Internal service/session coupling and broad message capabilities increase maintenance/governance exposure. Language boundary is Node/JavaScript-family; exact TypeScript build/peer versions remain OPEN because it is not selected. If separately evaluated, isolate behind TranscriptProvider with explicit governance review; fallback official Graph or file import. No need to merge a whole personal assistant connector to import a transcript.

### A08 — FalkorDB Browser: OPTIONAL local developer tool

VERIFIED-DOC: [official repository](https://github.com/FalkorDB/falkordb-browser), [README](https://raw.githubusercontent.com/FalkorDB/falkordb-browser/main/README.md), [actual LICENSE.txt](https://raw.githubusercontent.com/FalkorDB/falkordb-browser/main/LICENSE.txt) identifies SSPL v1. The attempted `/LICENSE` URL returned 404; correct file was subsequently verified. [Releases](https://github.com/FalkorDB/falkordb-browser/releases) and [issue index](https://github.com/FalkorDB/falkordb-browser/issues) inspected; no specific version pinned. Repository contains TypeScript/web UI artifacts; full runtime/dependency compatibility OPEN.

RECOMMENDATION: optional official local container compatible with selected server; zero files copied and no user-facing PromiseOps dependency. It can manipulate the database; restrict to loopback/presenter, with no public credentials or production access. Use bounded backend trace display as fallback for judges. Check server/browser image pairing, auth and licensing before deployment. Browser is not a second business database.

### A09 — pyca/cryptography: GO for signing after S02

VERIFIED-DOC: [maintainer repository](https://github.com/pyca/cryptography), [README](https://raw.githubusercontent.com/pyca/cryptography/main/README.rst), [license selector](https://raw.githubusercontent.com/pyca/cryptography/main/LICENSE), [Apache license](https://raw.githubusercontent.com/pyca/cryptography/main/LICENSE.APACHE), [BSD license](https://raw.githubusercontent.com/pyca/cryptography/main/LICENSE.BSD). The project permits either Apache-2.0 or BSD terms. Python API with native dependencies; [stable changelog](https://cryptography.io/en/stable/changelog/) showed 50.0.2, while latest API docs identified a development version. [Issue index](https://github.com/pyca/cryptography/issues) inspected; no relevant Ed25519 defect established.

RECOMMENDATION: stable supported binary package, zero copied source. Use documented [Ed25519 sign/verify](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/) and key serialization behind a narrow service. Verify Python, wheel platform and crypto backend support in S02; do not pin a dev version from latest documentation. Private-key custody is application responsibility. No ad hoc alternative signature algorithm if unavailable.

## 3. Official API and standards sources

### A10 — Microsoft Graph / Teams

VERIFIED-DOC: Microsoft-owned [list transcripts](https://learn.microsoft.com/en-us/graph/api/onlinemeeting-list-transcripts?view=graph-rest-1.0) and [get/content](https://learn.microsoft.com/en-us/graph/api/calltranscript-get?view=graph-rest-1.0) references were inspected. They document specific account/permission/meeting/tenant settings. Personal Microsoft account support must not be assumed; speaker attribution can be disabled independently of transcript access. No public repository or source-code license is needed for consuming the REST API; service permissions/terms still apply.

For the proposed application-permission route, docs identify `OnlineMeetingTranscript.Read.All` and scenario-limited `OnlineMeetingTranscript.Read.Chat`; the latter uses resource-specific consent for scheduled private chat meetings, not a universal substitute for tenant-wide permission. Application access involves administrator configuration/access policy. Tenant transcript-access and speaker-attribution controls can independently affect retrieval. These documented prerequisites are not evidence that the user's tenant has granted them; S04 must check the exact selected meeting/auth scenario.

RECOMMENDATION: optional HTTP adapter; Python/httpx is application stack, not required vendor SDK. Minimal metadata and content fields verified in API_CONTRACTS; all other fields and tenant setup OPEN S04. Dependency: approved app/tenant consent and available meeting transcript. Fallback VTT. Do not work around admin-disabled transcript access using internal session APIs. No live auth test performed.

### A11 — Jira Cloud REST v3

VERIFIED-DOC: Atlassian [issue search reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/) confirms enhanced JQL search and token pagination fields. [Issue read/create/edit reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/) failed retrieval twice, including a specific operation anchor. Those contracts are OPEN, not asserted verified. This is an official hosted API; no application repo merging or source license adoption.

RECOMMENDATION: thin HTTP adapter, configured project/field allowlists, minimal read-only sync first. S05 must verify issue identity, field metadata, permissions, pagination/read-after-write behavior, approved write shape and sandbox tests. No assumed generic idempotency header or If-Match support. Fallback import or separately evaluated official MCP transport. Exact auth scheme is owner choice; no credentials stored in prompts/UI/graph.

### A12 — Receipt design references

Inspected: [RFC 8785/JCS](https://www.rfc-editor.org/rfc/rfc8785), [dated W3C VC Data Model 2.0](https://www.w3.org/TR/2025/REC-vc-data-model-2.0-20250515/), [VC Data Integrity](https://www.w3.org/TR/vc-data-integrity/). These are official standards references, not packages or implemented compliance. PromiseSeal uses custom canonical profile and explicit issuer/claim separation only. No VC credential/presentation interoperability is implemented. No JCS library has been selected/audited; a future adoption needs vectors and version migration. This package paraphrases design relevance; it does not copy standards prose or license an implementation by implication.

## 4. Unverified technology and compatibility ledger

The fixed baseline names Next.js, React, TypeScript, Tailwind, shadcn/ui, FastAPI, Pydantic 2, httpx, pytest and a provider SDK. This research did not audit every framework repository, release, license, transitive dependency or security advisory. These remain **baseline stack choices with OPEN version/license checks S03/S07/S09**, not independently verified repository recommendations. shadcn/ui is optional; do not add it unless its component-copying license/attribution and accessibility justify it. No LLM provider/model/version/pricing is chosen here. Workload vendor/API/repository remains UNSPECIFIED, not missing research to be guessed.

| OPEN item | Required future evidence | Gate |
|---|---|---|
| Tested server/client pair and image digest | Real query/index/constraint/atomicity/restore tests, runtime versions and changelog review | S01 mandatory |
| Stable crypto runtime and canonical vectors | Sign/verify and negative vectors on target platform | S02 mandatory |
| Frontend/backend package compatibility/licenses | Resolved manifests/lockfiles and notices, lint/type/build | S03/S09 mandatory |
| Vexa response/auth/platform exact contract; Graph tenant setup | Pinned provider docs and consented sandbox response fixtures | S04 optional-live gate |
| Jira issue endpoint/contracts and per-site mappings | Official docs accessible plus sandbox validation | S05 live gate |
| Workload API | Owner-supplied actual contract and sandbox | S06 live gate |
| Model structured output/privacy/cost limits | Selected provider docs, schema stress tests and owner budget | S07 generated-analysis gate |
| SDK moved docs and isolated experiment | Resolve hosted docs, selected version and independent graph diff | Post-MVP only |
| Browser language/runtime/dependencies and image pairing | Selected artifact and local-only test | Optional tooling |

No “all issues reviewed,” “secure,” “latest compatible,” or “license-compliant deployment” conclusion is warranted by this document. Each recommendation minimizes copied code and isolates the uncertainty behind a small adapter or package boundary.
