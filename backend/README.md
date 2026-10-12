# PromiseOps backend foundation

Phase 0 work in progress. This is **not the complete business workflow**. No application graph
writes or external action routes are enabled until real FalkorDB compatibility and atomic
publication pass. The API contract in `../docs/API_CONTRACTS.md` is unchanged.

Python 3.14.7 is the available local runtime. Dependencies are pinned in `pyproject.toml`
and locked with hashes in `uv.lock`. From the repository root:

```sh
UV_CACHE_DIR=/private/tmp/promiseops-uv-cache uv sync --project backend --locked
cd backend
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --workers 1
```

Copy `.env.example` to `.env` inside `backend/` if overriding settings. No signing key is
generated or silently persisted by startup. Tests generate temporary in-memory keys.
Production is deliberately disabled pending identity and acceptance gates.

`GET /api/health` probes the configured existing graph through the official synchronous
FalkorDB client in a worker thread. It returns 503 while the graph is absent/unreachable;
it never creates a graph to manufacture readiness. `/internal/live` is a process-only probe,
excluded from OpenAPI. All other product routes remain unimplemented (404).

Offline tests include a source → exact evidence → PROPOSED receipt → signature → tampered-copy
slice. They do not establish graph persistence, audit-chain continuity, source retention,
business confirmation, policy authorization, idempotent dispatch or read-back.

Real graph compatibility commands, once Docker is installed and running:

```sh
docker compose -f backend/compose.spike.yaml config
docker compose -f backend/compose.spike.yaml up -d --wait
docker image inspect falkordb/falkordb:v6.0.2 --format '{{json .RepoDigests}}'
cd backend
RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest tests/integration -v
```

The candidate server tag is not a verified deployment pin; record the digest after pulling.
Integration tests create and delete only generated `spike_*` graphs. Use a disposable server.
Without the opt-in variable, tests skip with an explicit reason. With opt-in they fail on
unavailable/incompatible servers. Remaining S01 tests include restart/cache, persistence/restore,
native constraint behavior and application query templates; the current spike is a subset.

Dependency audit (network required; reports are gitignored):

```sh
cd backend
mkdir -p reports
.venv/bin/pip-audit --cache-dir /private/tmp/promiseops-audit-cache --format json --output reports/dependency-audit.json
```

PromiseSeal canonicalization is custom `promiseops-json-v1`, not JCS. `verify_bytes` checks only
schema/digest/signature and tenant/key trust. It does not return action eligibility. Future full
verification must additionally resolve ACL, retained sources, current standing, complete history,
authenticated review events and audit chain from FalkorDB. Retired public keys verify history;
retired/compromised keys cannot issue receipts. Private PEM keys must come from runtime mounts;
the loader is a library boundary and is not exposed to HTTP input.

See `../docs/IMPLEMENTATION_NOTES.md` for actual results and `../docs/BACKEND_COORDINATION.md`
for frontend handoff status.
