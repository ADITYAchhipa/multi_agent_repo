# Next Codex Session Handoff

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

```text
Continue PromiseOps + PromiseSeal backend implementation in /Users/sama/Downloads/promiseops-backend on branch feat/backend. First inspect current git status and read docs/NEXT_SESSION_HANDOFF.md, docs/IMPLEMENTATION_NOTES.md, docs/BACKEND_COORDINATION.md, docs/API_CONTRACTS.md, docs/IMPLEMENTATION_PLAN.md, docs/FALKORDB_SCHEMA.md, and docs/PROMISESEAL_PROTOCOL.md. Preserve the committed backend foundation; do not repeat its 84 passing offline tests or claim the four skipped FalkorDB tests passed. Immediate next action: make Docker available if possible, run the documented compose compatibility spike against a disposable FalkorDB server, record image digest/version, and diagnose the four opt-in tests. If Docker is still unavailable, report that evidence and do only useful work independent of unverified graph semantics. After the S01 graph compatibility and atomic publication gate passes, implement the next narrow no-LLM graph/source/receipt vertical slice using the frozen docs/API_CONTRACTS.md exactly. Do not modify frontend-owned files, invent live workload mappings, alter shared API schemas without a proposal, use another state database, or claim any test/integration passed unless actually run. Keep docs/NEXT_SESSION_HANDOFF.md and docs/IMPLEMENTATION_NOTES.md current with commands, actual outcomes, blockers, and commit/push status.
```
