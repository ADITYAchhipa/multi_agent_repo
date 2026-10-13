# Next Codex Session Handoff

> **Continuation update, 2026-10-12:** The main body below records the previous baseline at
> commit `b55540a`. It is historical where superseded. Verified new progress is appended at
> the end and in `docs/IMPLEMENTATION_NOTES.md`; do not repeat the Docker-unavailable diagnosis.

**Prepared:** 2026-10-12
**Scope:** handoff documentation only. This file reports the backend state and does not mark the MVP complete.

## 1. Project overview

PromiseOps helps B2B implementation and managed IT teams connect customer commitments to source evidence, contract scope, Jira work, staff capacity, and billing requirements. The central question is whether a promise is supported, in scope, deliverable, financially exposed, and safe to act on.

PromiseSeal is the application's versioned commitment receipt: a typed payload, evidence references, canonical content digest, optional Ed25519 platform attestation, confirmation state, and history. Integrity, business confirmation, source truth, legal effect, and action approval are distinct. Do not claim legal enforceability, W3C Verifiable Credential conformance, or mechanically immutable storage.

FalkorDB is intended to be the MVP's sole application knowledge/state database and must power the actual connected facts and paths. The intended demo runs on synthetic inputs, keeps extracted promises proposed until reviewed, calculates financial results deterministically, and gates a mock workload update behind approval and read-back.

## 2. Workspace and Git state

**Verified in the repository when this handoff was prepared:**

- Backend worktree: `/Users/sama/Downloads/promiseops-backend`.
- Backend branch `feat/backend`, HEAD `64132d53b8745d540dec5cd285c0e39e0fbc8949`, commit `feat(backend): add tested receipt and health foundation`.
- Remote: `origin` → `git@github.com:ADITYAchhipa/multi_agent_repo.git`.
- Backend upstream is `origin/feat/backend`; local branch was even with its upstream, and the worktree was clean before this handoff was added.
- `git ls-remote` reported `origin/feat/backend` at `64132d53b8745d540dec5cd285c0e39e0fbc8949` and `origin/feat/frontend` at `6cc8f7a3581f321d0f4d393f954650788a2385f5`.
- Frontend worktree: `/Users/sama/Downloads/promiseops-frontend`, branch `feat/frontend`, commit `6cc8f7a3581f321d0f4d393f954650788a2385f5`. Its inspected status was clean; it was one commit ahead of `origin/main` and its cached `origin/feat/frontend` ref matched HEAD.
- The backend repository also has the specification `main` worktree at `/Users/sama/Downloads/PROMISEOPS_CODEX_SPEC_BUNDLE`. Do not switch, reset, or merge worktrees as part of continuing backend work.

The frontend status and branch details are observations from the inspection session, not a fresh remote check after this document is written. Push this document to the backend branch if repository access permits.

## 3. Completed backend foundation

The last backend commit implements a limited phase-0 foundation under `backend/`:

- `backend/app/config.py`: validated settings, explicit frontend origins, secret redaction through `SecretStr`, remote graph TLS/auth guard, and a deliberate production-mode refusal while acceptance gates are incomplete.
- `backend/app/main.py`: FastAPI factory, request IDs, safe error envelopes, CORS, lifespan cleanup, `/api/health`, and internal `/internal/live`.
- `backend/app/graph/connection.py`: lazy synchronous official FalkorDB client, bounded socket/query timeouts, no automatic retry, graph-existence check, read-only parameterized probe, and close lifecycle.
- `backend/app/graph/ontology.py`: closed 35-relationship endpoint matrix and explicit directional alias normalization. A test compares it with the frozen schema.
- `backend/app/models/`: strict shared API primitives and `EvidenceRef`, health, and safe error models.
- `backend/app/ingestion/quote_verifier.py`: UTF-8 source/representation hashing, BOM/newline parse normalization, and exact Unicode-scalar quote-offset checking.
- `backend/app/promise_seal/`: custom `promiseops-json-v1` canonical encoding, strict JSON parsing, typed receipt payload/envelope, Ed25519 sign/verify against configured tenant/issuer/key identity, byte-integrity result, content hash, transition guards, and parent-link checks.
- `backend/tests/`: unit, API, offline source-to-receipt smoke, and opt-in real-server FalkorDB spike tests.
- `backend/pyproject.toml`, `backend/uv.lock`, `backend/.env.example`, and `backend/compose.spike.yaml`: pinned Python setup and a candidate disposable database service.

Implemented HTTP product routes are only `GET /api/health` and the internal `GET /internal/live`. The health response uses the frozen top-level shape and returns HTTP 503 when its configured graph is absent/unreachable. Other product endpoints currently fall through to the safe 404 envelope. No auth/session, source, promise, receipt verification, simulation, graph, trace, audit, connector, approval, action, persistence, or mock workload routes are implemented.

Important design limits: `verify_bytes` checks receipt schema/digest/signature/key trust only. It is not the API contract's full verifier and does not establish source availability, active standing, history/audit-chain validity, reviewer authority, business truth, or action eligibility. Lifecycle guards are pure functions, not authorized graph transitions. No graph write or external action path is enabled.

## 4. Verification: facts versus recorded reports

**Current repository fact:** commit `64132d5` contains the phase-0 source, tests and `uv.lock`. The handoff work itself is not in that commit until committed below.

**Results recorded by the preceding implementation session in `docs/IMPLEMENTATION_NOTES.md`; not rerun while preparing this handoff:**

| Check | Recorded outcome |
|---|---|
| `UV_CACHE_DIR=/private/tmp/promiseops-uv-cache uv sync --project backend` | Passed after network escalation; 58 packages resolved, 56 installed |
| `cd backend && .venv/bin/pytest -q` | 84 passed, 4 skipped, 1 warning |
| Ruff check and format check | Passed; format check reported 27 files already formatted |
| `python3 -m compileall -q backend/app backend/tests` | Passed |
| Installed official client inspection | FalkorDB Python client 1.7.1 `query`, `ro_query`, and `close()` signatures were inspected; this does not prove server compatibility |
| `pip-audit` | 56 installed dependencies audited, 0 known vulnerabilities, 0 skipped; this does not cover a server image or live services |
| Uvicorn HTTP smoke | Recorded server start/shutdown; `/internal/live` returned 200, actual-driver `/api/health` returned 503 with graph unavailable |
| `git diff --check` | Passed before the implementation commit |

The four skipped tests are in `backend/tests/integration/test_falkordb_spike.py`. They require `RUN_FALKORDB_INTEGRATION=1` and a real disposable server on port 16379. They cover parameter binding/read-only enforcement, index/path/tenant predicates, conditional concurrent claim, and failed-write atomicity. **They have not passed against a server.** The full e2e business workflow is unimplemented and was not run. Compose validation failed because the Docker executable was unavailable; it was not a YAML-validation pass. The single recorded pytest warning says Starlette 1.7.0 deprecates HTTPX's `TestClient` integration in favor of `httpx2`.

## 5. Blockers and open integrations

- **Docker/FalkorDB:** `docker` was absent from `PATH`; `docker compose version` and `docker compose -f backend/compose.spike.yaml config` returned command-not-found (127). Consequently no server image, container health, real Cypher syntax, query timeouts, index behavior, concurrency, atomic publication, persistence, backup, or restore has been verified.
- `falkordb/falkordb:v6.0.2` in the spike Compose file is only a candidate tag. It has no recorded image digest and is not a tested deployment pin. It starts a server only; the app expects an already-existing configured graph and will not create one.
- No complete graph repository, migration/seed routine, vetted business query catalogue, or typed write service exists. The current integration spike is intentionally partial; S01 still needs additional compatibility/recovery cases.
- Source artifacts are not retained. Idempotent ingest/diff/quarantine/conflict resolution are not implemented.
- Business-authenticated tenant context/role checks are not implemented. The graph probe configuration alone is not product authorization.
- Deterministic financial calculations, scheduling/simulation, bounded orchestration, action policy, durable idempotency/action ledger, mock adapter and read-back are not implemented.
- Vexa/Microsoft Graph, Jira, LLM, and live workload adapters are not implemented. No credentials were supplied or used. The real workload API contract remains unspecified; do not invent endpoints, fields, identities, auth, or status values. Keep live writes disabled.
- API_CONTRACTS.md is the frozen shared contract. Do not silently change it to match UI convenience or incomplete backend routes.

## 6. Prioritized next tasks

1. **Immediate:** obtain a running Docker runtime, run Compose config/startup, record the exact image digest/server version, and execute the opt-in integration tests on a disposable graph. Fix compatibility failures and extend the S01 spike before claiming M0. If Docker remains unavailable, continue only work independent of graph behavior and state the blocker.
2. Complete graph compatibility evidence for indexes/constraints, timeout behavior, query/result types, failed statement atomicity, concurrency, reconnect/cache behavior, persistence and restore. Do not write application state until supported atomic publication is demonstrated.
3. Implement the frozen ontology write boundary, tenant-resolved typed graph repository, source-version/artifact services, and named parameterized query templates. Use the synthetic seed scenario and compare actual paths/results with the graph contract.
4. Build the no-LLM source → exact evidence → proposed signed receipt → graph publication/history slice. Add replay/idempotency, source revisions, quarantine, conflicts and real graph tenant isolation tests.
5. Implement deterministic Python money/currency/unknown handling and isolated scenario overlays only after graph reads are real.
6. Implement the frozen API routes/models with server-side auth, request/error behavior and API contract tests. Coordinate any frontend-shared schema difference before changing the frozen contract.
7. Add typed mock workload proposal, backend policy/approval state machine, action ledger, exact idempotency, pre-dispatch freshness checks and read-back. Test zero writes before approval and uncertain-write reconciliation.
8. Integrate the frontend against the backend contract, then run frontend checks and full real-FalkorDB e2e twice. Keep mock mode explicit; do not present browser-only state changes as backend authorization or persisted execution.
9. Only after the credential-free MVP gates pass, evaluate optional live connectors against their official contracts and supplied permissions/credentials.

## 7. Frontend integration handoff

**Inspected branch and tree:** `feat/frontend` at `6cc8f7a3581f321d0f4d393f954650788a2385f5`; its tree was clean during inspection. This is a separate worktree; no frontend files have been changed from the backend branch. Frontend package scripts declare `npm run lint`, `npm run typecheck`, `npm test`, and `npm run build`. The frontend coordination note reports lint/typecheck/build passing and 16 tests passing; this is a report in that branch, not a result independently rerun for this handoff.

Shared API contract: `docs/API_CONTRACTS.md` on backend `feat/backend` (and the corresponding specification tree). Preserve its request/response fields and route shapes. The frontend `frontend/lib/api-client.ts` defaults to `DEMO`; `NEXT_PUBLIC_APP_MODE=LIVE` selects HTTP requests and `NEXT_PUBLIC_API_URL` defaults to `/api`. Demo data and mutations are held in in-memory module variables/fixtures. The user interface's mock policies, receipts and action results are not a live backend integration.

Specific integration gaps observed by comparing the frontend source to the contract:

- Frontend asks for `GET /simulations` collection; the frozen contract defines create `POST /simulations` and detail `GET /simulations/{scenario_id}`, but no collection route. Do not add one silently; coordinate a contract proposal or change the client to a supported flow.
- Frontend can call `/graph?depth=...` without an entity; the contract route is `GET /graph/{entity_id}` with bounded query filters.
- Live approve and execute calls send only `{reason}` and `{}` respectively. The contract requires expected revision and proposal hash for approval/execution, with idempotency headers. The client request helper adds an idempotency key but does not supply those binding fields. Frozen API contract fields must be implemented/used.
- Frontend branch docs claim the backend has no blockers and imply live integration is ready. That is stale: only health exists in this backend commit, and all other product routes are pending.
- Cross-worktree document synchronization is not verified after inspection. Compare the shared API contract before integration and keep `frontend/` owned by the frontend branch/worktree.

## 8. Continuation commands

These are copied from the committed `backend/README.md` and were documented by the prior session. Setup, unit tests and lint were reported as run there; Docker commands are follow-up commands, **not verified successful**.

From repository root:

```sh
UV_CACHE_DIR=/private/tmp/promiseops-uv-cache uv sync --project backend --locked
cd backend
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --workers 1
```

## Continuation results — 2026-10-12 (supersedes Docker blocker above)

- **Verified runtime:** Homebrew Docker CLI 29.9.0, Compose 5.6.0, Colima 0.10.3. FalkorDB
  container v4.20.4 is healthy; logs report server 4.20.4, Redis 8.6.3. Pulled ARM64 image
  digest: `sha256:adbddd418916c25618564ff8597a919b08bc76452ebeb74eb985c38d7281df62`.
  The old `v6.0.2` candidate did not exist and was replaced in backend Compose. Python client
  remains locked at 1.7.1. Production image signature/restore behavior is unverified.
- **Verified tests:** `cd backend && RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest -q` yielded
  **91 passed, no skips, 1 Starlette warning**. This includes the four original spike tests
  and one new graph-backed Promise API integration test. Offline-only run yielded 86 passed,
  5 explicit opt-in skips, 1 warning. Ruff check and format check passed after fixes.
- **Implemented routes:** `POST /api/session`, `GET /api/session`, `GET /api/promises`,
  `GET /api/promises/{promise_id}`, `GET /api/promises/{promise_id}/verify`, in addition to
  existing `GET /api/health`. Sessions use server-configured demo users and signed HttpOnly
  cookies. Promise reads use bounded parameterized Cypher and server-selected tenant graphs;
  PUBLIC_DEMO graph ACL only. Verification checks canonical digest/signature with configured
  public keys but marks retained source bytes/audit chain UNAVAILABLE and action eligibility
  false. See `backend/app/api/`, `backend/app/auth.py`, `backend/app/graph/repository.py`,
  `backend/app/graph/queries/promises.py`, `backend/tests/integration/test_promise_query.py`.
- **Still blocked/incomplete:** no application source artifact retention, graph writer,
  append-only receipt/audit publication, historical version read, review mutation, calculations,
  scenarios, approval/action/mock read-back, full demo or frontend integration. Live connectors
  remain unconfigured. The current list's `risk` filter and detail `version_id` return errors
  rather than misleading responses. The frozen shared API contract is unchanged; these routes
  are partial coverage, not full contract completion.
- **Continue commands:** from repo root, `docker-compose -f backend/compose.spike.yaml config`,
  `docker-compose --progress quiet -f backend/compose.spike.yaml up -d --wait`; then
  `cd backend && RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest -q` and
  `.venv/bin/ruff check . && .venv/bin/ruff format --check .`. Homebrew Compose is a standalone
  `docker-compose` executable here; `docker compose` was not configured as a CLI plugin.

**Immediate next task:** implement retained source bytes/version/hash plus an idempotent,
atomic tenant-scoped graph publication path for PROPOSED receipts and audit events. Test the
source→receipt→graph→read-back flow on a disposable FalkorDB graph before expanding review or
actions. This continuation's commit and push status must be checked with Git; the historical
branch/commit fields earlier in this document are not current once this section is committed.

To create a local settings file, copy `backend/.env.example` to `backend/.env`. The current defaults point at local FalkorDB port 6379 and graph `company_demo`; no signing secret is generated. Do not place real credentials in this handoff.

With Docker installed/running, the documented disposable spike commands are:

```sh
docker compose -f backend/compose.spike.yaml config
docker compose -f backend/compose.spike.yaml up -d --wait
docker image inspect falkordb/falkordb:v6.0.2 --format '{{json .RepoDigests}}'
cd backend
RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest tests/integration -v
```

Before using the integration test, confirm the server is disposable: it creates and deletes only random `spike_*` graphs. Record the pulled image digest before selecting any deployment pin. No full seed/reset/demo command exists yet. Development server command above and exact environment expectations are in `backend/README.md`.

## 9. Important files to inspect

- Product authority and build scope: `PROMISEOPS_PROMISESEAL_CODEX_BUILD_SPEC.md`.
- Frozen application route/DTO contract: `docs/API_CONTRACTS.md`.
- Current implementation scope, recorded checks and deviations: `docs/IMPLEMENTATION_NOTES.md`.
- Backend/frontend route status: `docs/BACKEND_COORDINATION.md`.
- This handoff: `docs/NEXT_SESSION_HANDOFF.md`.
- Planned gates/order: `docs/IMPLEMENTATION_PLAN.md`, especially S01 and M0/M1.
- Graph ontology/query contract: `docs/FALKORDB_SCHEMA.md`.
- Receipt bytes and lifecycle: `docs/PROMISESEAL_PROTOCOL.md`.
- Architecture and recovery: `docs/ARCHITECTURE.md`.
- Security/access and adapter boundaries: `docs/SECURITY_AND_THREAT_MODEL.md`, `docs/AGENT_DESIGN.md`, `docs/DATA_INGESTION_AND_PROVENANCE.md`.
- Deterministic simulator/formulas: `docs/COUNTERFACTUAL_SIMULATOR.md`.
- Synthetic records and expected oracle: `docs/SEED_SCENARIO.md`.
- Runtime/dependency pins: `backend/pyproject.toml`, `backend/uv.lock`, `backend/.env.example`, `backend/compose.spike.yaml`, `backend/README.md`.
- Main implementation areas: `backend/app/config.py`, `main.py`, `graph/`, `models/`, `ingestion/`, `promise_seal/`.
- Tests: `backend/tests/unit/`, `backend/tests/api/`, `backend/tests/integration/`, `backend/tests/e2e/`.
- Frontend reference only, in its separate worktree/branch: `frontend/COORDINATION.md`, `frontend/types/api.ts`, `frontend/lib/api-client.ts`, `frontend/lib/fixtures/seed-data.ts`, and `frontend/tests/`.

## 10. Rules for the next session

- Recheck the worktree before editing, preserve the existing foundation and fixture/spec work, and keep changes scoped to backend-owned paths unless integration work is explicitly coordinated.
- `docs/API_CONTRACTS.md` is shared and frozen. Keep exact route names, DTO fields, enums, and error behavior. Propose a schema change with reason and frontend impact before changing it.
- FalkorDB must be the real source of connected facts. Do not replace missing server evidence with fake paths or an in-memory application database.
- Treat model/source text as untrusted. Use reviewed parameterized query templates and typed graph services. Money uses deterministic arithmetic.
- No consequential external write before backend authorization, valid evidence, approval, freshness, idempotency, and the documented read-back/reconciliation policy. Workload live mapping is unknown.
- Never claim a repository integration, query, build, container, or test works unless this environment actually ran it. Label inherited reports as recorded reports, and distinguish skips from passes.
- Use synthetic demo data only. Do not expose secrets, private source text, employee data, tokens, or private signing keys.
- No second application state database, unrestricted model-generated Cypher, arbitrary user-controlled URL fetch, or frontend-owned file edits from this worktree.

## Ready-to-paste continuation prompt

**Later verified update:** Source upload and artifact retention are now implemented for local
UTF-8 `.txt`/`.md` files. `POST /api/sources/upload`, source/operation reads, local signed
`GET /api/audit/verify`, nonpersisting `POST /api/receipts/verify`, and a one-time configured
graph initializer passed real FalkorDB tests. Full opted-in suite: **95 passed, 0 skipped,
1 existing Starlette warning**; `pip-audit`: **57 dependencies, 0 known vulnerabilities**.
`python-multipart==0.0.32` is locked. Verification can check retained source bytes/quotes,
but receipt history/audit eligibility and action authorization remain unavailable. The next
milestone is source chunks/candidate → PROPOSED receipt graph publication and reviewer history;
the earlier subsection calling source upload unimplemented is superseded by this update.

```text
Continue PromiseOps + PromiseSeal backend implementation in /Users/sama/Downloads/promiseops-backend on feat/backend. Inspect current git status and read docs/IMPLEMENTATION_NOTES.md, docs/BACKEND_COORDINATION.md and frozen docs/API_CONTRACTS.md. Preserve the graph-tested compatibility, session, promise-read, source upload/versioning, local artifact, signed audit and receipt-copy verification work. Docker/Colima and FalkorDB v4.20.4 with client 1.7.1 already passed the opted-in suite (95 tests at the last verified run). Immediate next action: implement source chunk/candidate extraction and atomic append-only PROPOSED PromiseSeal publication from exact retained evidence, then authorized review/history verification and the remaining contract routes. Follow with deterministic money/scenarios and approval-gated mock action read-back, then frontend integration. Do not claim local audit verification is an external checkpoint or receipt integrity is business confirmation. Test each new graph query against the real server, keep docs/API_CONTRACTS.md stable, do not edit frontend files or invent live workload mappings, and commit/push only verified progress to feat/backend.
```

## 2026-10-12 continuation: verified source chunks and snippet reads

Reconciled current worktrees before implementation: backend HEAD was `7c7c955`, frontend
`54154e2`, QA `98effeb`, audit `8f49aa7`. Remote backend was still `a5cfbdc`. The later QA
report targets an older merged backend; its missing-session/source and GET-only CORS claims
do not describe this checkout. The audit's unparenthesized-except syntax concern does not
apply to the pinned Python 3.14 runtime. The current baseline actually passed 95 tests.

New text uploads now atomically publish SourceChunk nodes and HAS_CHUNK edges together with
the source version, operation, signed audit and graph revision. The deterministic text profile
uses at most 4,000 Unicode scalar characters per chunk, prefers paragraph boundaries, explicitly
segments longer paragraphs, uses zero overlap, and rejects more than 200 chunks with HTTP 422
before storing artifacts or graph publication. Chunk IDs bind tenant, version and global offset.

Source detail now returns EvidenceRef snippets and accepts chunk_id together with optional
version_id. Reads enforce tenant and node/edge ACLs, recheck retained raw/representation hashes,
exact quote offsets and chunk hashes, and report VERIFIED, REJECTED or UNAVAILABLE accordingly.
Historical source chunks remain tied to their immutable versions; replay does not duplicate them.
Existing versions created before this change are not backfilled; unchanged reuploads still return
NO_CHANGE. Source reprocessing remains a future route.

Validation: full opted-in real FalkorDB suite **101 passed, no skips, one existing Starlette
warning**; Ruff lint and format passed. Added boundary/Unicode/limit tests and real graph checks
for chunk count, replay, historical selection, missing/wrong-version chunks, oversized rejection,
tampered text and restricted chunk visibility. One sandboxed targeted run was denied socket
access; the escalated rerun passed against the local server.

Next unfinished milestone: typed candidate extraction and atomic PROPOSED receipt publication
from these chunks, then authorized append-only review/history. No automatic semantic extraction,
review writer, finance/scenarios or action execution is implemented by this change. Shared API
contract and frontend files are unchanged.

## 2026-10-12 continuation: initial PROPOSED receipt publication

Completed the bounded no-LLM upload-to-proposal slice on top of source chunks. A strict typed
candidate model and deterministic `text-commitment-lines-v1` profile select complete lines
starting with I/We + will/can + deliver/provide/complete/ship/build. Quotes must fit within one
chunk and the 2,000-character receipt text bound; unsupported wording or boundary-crossing
lines are not extracted. More than 100 unique candidates rejects the upload before artifact
storage/publication. This is intentionally limited language coverage, not a general extractor.

The producer re-reads retained artifacts, verifies exact Unicode quote offsets and raw/parse
hashes, and signs initial PROPOSED receipts with the configured trusted Ed25519 key. All
candidates remain ambiguous with unknown confidence, unresolved identity/deadline/price and
no confirmation. Source text has no execution or authorization effect. Quote-based identity
is scoped to tenant, logical source and profile; duplicate occurrences/replays and unchanged
quotes in revised sources do not duplicate receipts. Changed wording creates a separate
proposal, preserving prior evidence; conflict resolution and semantic identity remain pending.

The same revision-conditional Cypher publication creates Promise/PromiseVersion, HAS_VERSION,
PROPOSES, SUPPORTED_BY and receipt HAS_EVENT links. Extracted edges carry exact evidence and
profile metadata; the source audit event includes the receipt ID/digest manifest. Existing
promise list/detail and both verification routes read the new receipts. Full receipt history
verification is still unavailable, and action eligibility remains false.

Verified full suite: `RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest -q` → **107 passed, no skips,
one existing Starlette warning**. Ruff lint/format and diff whitespace checks passed. New tests
exercise Unicode/CRLF offsets, bounded extraction, forged offsets rejected before signing,
real source→chunk→receipt paths, signature/source verification, audit manifests, idempotency,
source revisions, restricted/cross-tenant reads, multiple chunks, inert hostile text and a
forced late-write failure rolling back all source/chunk/receipt/audit/operation changes. The
multi-chunk test initially had an incorrect hardcoded expected boundary; corrected its oracle
and reran the entire suite successfully.

Next: authorized append-only review and historical receipt access/verification, then remaining
finance/scenarios and approval-gated mock actions. No shared API contract or frontend edits.
This continuation and the preceding chunk changes are local and uncommitted/unpushed.

## 2026-10-13 continuation: reviewer receipt versions and history

Implemented the frozen review route POST /api/promises/{promise_id}/review with reviewer-role checks,
expected receipt ID/current revision, strict decision/content validation and required idempotency
key. CONFIRM requires every existing evidence reference and a fresh signature/source-byte check;
new cited evidence must resolve to a tenant-scoped PUBLIC_DEMO source chunk and pass retained-byte,
quote-offset and chunk-hash checks. FULFILL requires a confirmed parent plus at least one newly
cited verified chunk. A disputed promise cannot be confirmed through this route because conflict
resolution is not implemented. REVISE accepts only the contract's allowlisted content fields,
retains/rechecks source evidence and clears confirmation. All decisions append a signed successor
receipt; confirmation metadata binds the content digest and reviewer event.

Each mutation writes the new PromiseVersion, HAS_VERSION/SUPERSEDES/HAS_EVENT links, updates the
current pointer/revision and old standing, appends the signed audit event, and stores an
actor-scoped idempotency result under one revision-conditional graph write. Concurrent stale
writes fail closed; retry with the same key/body returns the original result and a new request ID.
Historical detail/verify accepts version_id. Verification checks contiguous predecessor IDs,
canonical hashes/signatures, current/superseded standing, the tenant audit chain and each receipt's
signed audit manifest/event binding. No independent external checkpoint exists; action eligibility
remains false.

For this continuation, no tests were added or run because the active developer instruction says
not to add or run tests unless the user asks for verification. Ruff lint/format and git diff --check
passed. Real FalkorDB behavior for the newly added review/history Cypher and the complete review
lifecycle remains unverified and should be the first check next session. Earlier verified
source/chunk/proposal tests remain as recorded; they do not establish this new route.

Remaining MVP work is substantial: full typed graph query catalogue/ACL, real fixture graph path,
finance and scenarios, action approval/ledger/mock read-back and reconciliation, frontend contract
integration, backup/restore/performance, and reproducible full demo gates. This review slice does
not complete M1–M5. All current changes remain local and uncommitted/unpushed.
