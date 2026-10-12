# Backend implementation notes

## 2026-10-12 — Audit and phase-0 foundation

The user authorized implementation, superseding the prior documentation-only phase. Original
input specifications remain unchanged. Initial `pwd` was `/Users/sama/Downloads/promiseops-backend`;
`git status --short --branch` was clean `feat/backend...origin/main`. History: `b04cdcb docs`,
`09a084c Initial commit`. No AGENTS.md, manifests, services, tests, scripts, Docker files or
environment examples existed. Read the master specification and generated design documents.

Use the documented `backend/app` layout. Synchronous official FalkorDB client stays behind a
connection abstraction; synchronous FastAPI routes run in the threadpool. No additional database,
SDK graph writer, copied upstream code, frontend changes or live provider connections were added.

### Implemented scope and limits

- Validated environment settings, explicit CORS origins, safe request/error envelopes, process
  liveness versus graph readiness, client lifecycle and disabled production profile.
- Strict evidence/receipt models; exact UTF-8 source hashing and Unicode scalar quote offsets;
  named canonical encoding, SHA-256, Ed25519, scoped key trust, pure parent/transition guards.
- Closed 35-relationship endpoint matrix with a contract comparison test; known aliases preserve
  direction and unknown relationships fail validation. No graph publication is implied.
- Offline source-to-proposed-receipt signing/tamper slice. This is not the required graph/action demo.
- Opt-in real-engine compatibility candidates for parameter binding, read-only enforcement,
  index/path direction and tenant predicates, concurrent conditional writes and failed publication.

No full receipt Verification response is claimed: graph source retention, standing/history,
authenticated confirmation/audit events and action prerequisites are not implemented. Pure guards
do not provide authorization or append-only persistence. No external write path exists. No
idempotency ledger/read-back claim is made. All product routes except health remain pending.

### Dependency evidence and choices

Observed PyPI metadata on 2026-10-12: FastAPI 0.143.0 (MIT), Pydantic 2.14.1 (MIT),
pydantic-settings 2.15.0 (MIT), HTTPX 0.28.1 (BSD-3-Clause), FalkorDB Python 1.7.1,
cryptography 50.0.2 (Apache-2.0 OR BSD-3-Clause), Uvicorn 0.54.0 (BSD-3-Clause), pytest 9.1.1
(MIT), Ruff 0.17.0 (MIT), pip-audit 2.10.1. Official FalkorDB client repository identifies MIT;
server is separately SSPLv1. Exact transitive resolutions/hashes are in `backend/uv.lock`.
Python constraint 3.14 reflects the installed 3.14.7 runtime; other runtimes are not tested.

Primary sources inspected (package/API use only, zero source copied):

- [Official client 1.7.1 connection API](https://github.com/FalkorDB/falkordb-py/blob/v1.7.1/falkordb/falkordb.py)
- [Official client 1.7.1 graph API](https://github.com/FalkorDB/falkordb-py/blob/v1.7.1/falkordb/graph.py)
- [FalkorDB 6.0.2 release](https://github.com/FalkorDB/FalkorDB/releases/tag/v6.0.2)
- [Ed25519 API](https://cryptography.io/en/stable/hazmat/primitives/asymmetric/ed25519/)
- [PyPI release metadata](https://pypi.org/project/FalkorDB/) and corresponding project metadata
  for each pinned direct dependency, fetched via PyPI JSON API.

The server release page reports a GitHub-verified release commit; no container signature or
artifact attestation was independently verified. Candidate Compose tag is `v6.0.2`; no image
digest or server/client compatibility is claimed. Native constraints, transaction rollback,
index syntax and restore behavior remain OPEN S01. No optional connector activation.

### Environment blockers

`docker compose version` exits 127: `command not found: docker`. No Docker app in /Applications
or executable at common locations. Consequently Compose validation, container health, actual
graph tests and the full demo are blocked. No substitute database or fake graph was introduced.
Per TEST_AND_EVALUATION_PLAN §3 and IMPLEMENTATION_PLAN S01, dependent graph writes remain disabled.

Initial dependency lookup/install failed sandbox DNS. Repeated with requested network escalation.
The UV cache is under `/private/tmp/promiseops-uv-cache` because the default home cache is not
writable. Setup/test/follow-up commands are in backend/README.md.

### Verification results

Executed on macOS ARM64 with Python 3.14.7 and the pinned dependencies above:

| Command/check | Actual result |
|---|---|
| `UV_CACHE_DIR=/private/tmp/promiseops-uv-cache uv sync --project backend` | Passed after network escalation; 58 resolved, 56 installed |
| `cd backend && .venv/bin/pytest -q` | **84 passed, 4 skipped, 1 warning**, 0.33s final run |
| Offline test breakdown | 78 unit, 5 API, 1 source/receipt slice passed; 4 real graph spike tests skipped |
| `.venv/bin/ruff check .` | Passed |
| `.venv/bin/ruff format --check .` | Passed, 27 files formatted |
| `python3 -m compileall -q backend/app backend/tests` | Passed |
| Installed client inspection | `query/ro_query(q, params=None, timeout=None)` and `close()` verified against installed 1.7.1; does not verify server behavior |
| `.venv/bin/pip-audit --cache-dir /private/tmp/promiseops-audit-cache --format json --output reports/dependency-audit.json` | **56 dependencies audited, 0 known vulnerabilities, 0 skipped**, exit 0; no automatic fixes |
| Uvicorn factory, localhost:18000, one worker | Started and shut down cleanly after sandbox port-binding escalation |
| HTTP `/internal/live` | 200, request ID in header and body |
| HTTP `/api/health` using actual driver/offline graph | 503 DEGRADED, graph UNAVAILABLE, no graph name/credentials leaked |
| `docker compose version` and `docker compose -f backend/compose.spike.yaml config` | Both exit 127, Docker not installed |
| Container health, real Cypher/atomicity, full business demo | **NOT RUN / BLOCKED**; skipped tests do not establish compatibility |
| Static type checker | Not configured/run in this foundation; no typing-pass claim |
| Original input SHA-256 manifest | All three originals match docs/CHANGELOG.md |
| `git diff --check` | Passed |

The first test run had 1 failure / 79 passes / 4 skips: the ontology contract test mistakenly
parsed the Markdown header as an edge. Corrected its header parsing; all 35 real matrix rows
already matched. Reran the targeted test (8 passed) then full suite. Added four additional
negative/lifecycle checks and reran to the final 84 passes. Initial Ruff formatting/import
findings were fixed and rechecked. Nothing was skipped to hide a failure.

One visible dependency warning: Starlette 1.7.0 deprecates HTTPX use in TestClient in favor of
httpx2. Current tests work; HTTPX remains the mandated stack choice. No warning filter was added.
Future test-client migration needs its own package review. pip-audit first failed on an
unwritable default cache, then rejected `--disable-pip` without `-r`; the corrected command above
completed. No vulnerability finding was ignored. The audit covers Python packages, not the
unpulled container, API providers or a general security assessment.

### Remaining gate and follow-up

Provide a Docker runtime, then run the exact Compose/integration commands in backend/README.md.
Record image digest and extend S01 with timeout/constraints/cache/restart/restore tests before
declaring M0 complete. M1–M5 remain pending: source artifact retention/idempotent ingest, graph
query catalogue and atomic audit/version publication, auth/ACL, money/scheduling, bounded
orchestration, frozen route coverage, approval ledger/mock write/read-back and full demo.
All live connectors are unimplemented/untested and disabled; workload mapping remains unknown.
The initial API/crypto slice is useful independently but is not a completed MVP or full M0.

### Commit and coordination

No GitHub MCP configured. Endpoint status is in BACKEND_COORDINATION.md; API_CONTRACTS.md is
untouched. Commit/push result will be reported after checks.

## 2026-10-12 continuation: real graph gate and read-only API slice

Earlier phase-0 notes above are historical. This continuation installed Docker CLI 29.9.0,
Compose 5.6.0 and Colima 0.10.3, then pulled `falkordb/falkordb:v4.20.4`. The old candidate
`v6.0.2` returned Docker Hub `not found`. The pulled ARM64 digest was
`falkordb/falkordb@sha256:adbddd418916c25618564ff8597a919b08bc76452ebeb74eb985c38d7281df62`.
Container logs identify FalkorDB 4.20.4 and Redis 8.6.3; Compose reported healthy. Official
Python client 1.7.1 remains locked. Docker server reported 29.5.2. Image signature/security
and production deployment were not verified.

`docker-compose -f backend/compose.spike.yaml config` passed. The pinned image started with
`docker-compose --progress quiet -f backend/compose.spike.yaml up -d --wait`. The four formerly
skipped S01 tests passed against that server: parameter binding/read-only rejection, index and
tenant-scoped path, single-winner conditional publication under four threads, and failed-write
rollback. They do not prove restart/restore durability, native uniqueness or all Q01–Q10 queries.

Added configured local demo sessions (server-side actor/tenant/roles, signed HttpOnly cookie),
server-selected tenant graph, fixed read-only promise queries, bounded cursor, Promise Inbox,
current detail and current receipt verification routes. Detail reads a stored receipt, checks
accessible source-version metadata, and returns an actual Promise→Version edge ID. Verification
checks canonical bytes/signature with configured public keys; retained source bytes and audit
chain are explicitly UNAVAILABLE and `eligible_for_action` is false. A disposable graph API test
checks tenant isolation, cursor binding, detail, valid integrity and altered-payload detection.
No application source artifact ingestion or persistence writer exists yet.

| Command | Actual result |
|---|---|
| `cd backend && RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest tests/integration -v` | 5 passed, 1 Starlette warning |
| `cd backend && RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest -q` | 91 passed, 1 Starlette warning, no skips |
| `cd backend && .venv/bin/pytest -q` | 86 passed, 5 opt-in graph skips, 1 warning |
| `cd backend && .venv/bin/ruff format --check .` | Passed after formatting |
| `cd backend && .venv/bin/ruff check .` | Passed after import cleanup |
| Targeted tampered graph API test | 1 passed, 1 Starlette warning |

Contract coverage is partial. Session logout, historical receipt reads, source upload/retention,
reviews, graph health, finance/simulations, approval/action/mock read-back, connectors,
trace/audit/operations and full demo remain unimplemented. `risk` filtering and historical
`version_id` currently reject rather than return incorrect data. Current scope/freshness are
UNKNOWN and no calculation or execution conclusion is made. Frontend remains mock-only.
`docs/API_CONTRACTS.md` was not changed.

## 2026-10-12 continuation: source/artifact/audit slice

Implemented a backend-owned, local-demo text source path while keeping FalkorDB as the only
application state database. `POST /api/sources/upload` accepts admin-authenticated UTF-8
`.txt`/`.md` files (20 MiB bound) with an idempotency key. Exact raw bytes and normalized
representation bytes are stored by SHA-256 in gitignored `backend/data/sources/`; graph records
are the authoritative artifact index. A single conditional Cypher statement publishes a source
version, completed OperationRun, signed AuditEvent and GraphState revision/head. Reuse of the
same key/body returns the original operation with the current request ID; same key/different
body is 409; a new key with unchanged bytes yields NO_CHANGE; a stable `source_key` with changed
bytes creates a new version. A configured Ed25519 runtime private key and matching trusted public
key are required before writes. The private key is never stored in the graph or source tree.

`GET /api/sources/{source_id}` and `GET /api/operations/{operation_id}` read these graph records.
Admin `GET /api/audit/verify` checks the local signed chain against GraphState; it explicitly
reports that no external rollback checkpoint exists. Receipt GET verification now re-reads
retained source artifacts and validates exact quote offsets/hashes when available. The
nonpersisting `POST /api/receipts/verify` detects a tampered copy without changing the graph.
Receipt audit/history verification and action eligibility remain unavailable/false. An explicit
`python -m app.scripts.init_graph --tenant tenant-demo` command initializes only a configured
empty graph and refuses an existing graph; index syntax and the CLI were tested on disposable
real graphs. No automatic promise extraction or review/version writer exists yet.

Pinned `python-multipart==0.0.32` after checking its published PyPI package metadata, then
updated `backend/uv.lock`. `UV_CACHE_DIR=/private/tmp/promiseops-uv-cache uv lock --project backend`
failed in the sandbox because DNS was unavailable; the approved network retry resolved 59
packages. Locked sync installed the new package. `pip-audit` then reported **57 dependencies,
0 known vulnerabilities**, exit 0. This is a Python dependency advisory check, not a server
image/credential or source-content security review.

Final verified commands for this slice: `cd backend && RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest -q`
→ **95 passed, no skips, 1 Starlette warning**; `ruff check .` and `ruff format --check .`
passed after formatting. `docker-compose ... config` and `up -d --wait` previously passed;
`init_graph` CLI ran successfully against `spike_cli_20261012_1340`, which was then deleted.
The real graph tests include source version/idempotency/role/filename checks, local signed audit
chain/tamper detection, source byte/quote verification, receipt-copy tamper detection and graph
initializer refusal to overwrite. The warning remains the existing TestClient deprecation.

Still pending: VTT/meeting-context and structured imports, SourceChunk/candidate extraction,
source reprocess/retire, complete PromiseSeal append-only review history, historical reads,
full graph query catalogue, finance/scenarios, action policy/approval/ledger/mock read-back,
frontend integration and full e2e demo. The current upload returns an OperationRun completed
synchronously behind the contract's 202 operation response. No live connector credentials or
workload mappings were supplied; no live connector was activated. Frozen API contract unchanged.
