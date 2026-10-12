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
