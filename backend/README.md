# PromiseOps backend foundation

Phase 0 compatibility, tenant-scoped promise reads and bounded text-source publication are
implemented. This is **not the complete business workflow**. The shared API contract in
`../docs/API_CONTRACTS.md` is unchanged; route coverage remains partial.

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

For local source upload, configure `DEMO_USERS`, `SESSION_SECRET`, a matching public key in
`PUBLIC_KEYS`, and `SIGNING_PRIVATE_KEY_PATH`, `SIGNING_KEY_ID`, `SIGNING_ISSUER_ID`. Mount the
private PEM file under the gitignored `secrets/` directory; never commit it. The upload endpoint
accepts admin-authenticated UTF-8 `.txt`/`.md` files up to 20 MiB with an `Idempotency-Key`
header. It retains raw and normalized bytes under gitignored `data/sources/`, publishes
SourceRecord/SourceVersion, a completed OperationRun and a signed audit event in one conditional
FalkorDB query. Repeat with the same key/body returns the same operation; a new key with unchanged
source bytes returns NO_CHANGE; changed content with a stable `source_key` creates a new version.
No promise is inferred or confirmed from an uploaded file yet. VTT, meeting context, structured
imports and live connectors are not enabled.

`GET /api/health` probes the configured existing graph through the official synchronous
FalkorDB client in a worker thread. It returns 503 while the graph is absent/unreachable;
it never creates a graph to manufacture readiness. `/internal/live` is a process-only probe,
excluded from OpenAPI. With `DEMO_USERS` and `SESSION_SECRET` configured, `POST /api/session`
sets a local HttpOnly cookie, `GET /api/session` reads the current identity, and
`GET /api/promises` / `GET /api/promises/{promise_id}` query PUBLIC_DEMO tenant-scoped graph
facts. `GET /api/promises/{promise_id}/verify` and nonpersisting `POST /api/receipts/verify`
check canonical hash/signature plus available retained source bytes and exact quotes. Receipt
audit/history checks remain unavailable, so action eligibility stays false. `GET /api/sources/{id}`,
`GET /api/operations/{id}` and admin `GET /api/audit/verify` read the graph publication. Audit
verification checks the local chain against GraphState; it has no independent external checkpoint.
Historical receipt reads, review writes, scenarios and actions remain pending.

Offline tests include a source → exact evidence → PROPOSED receipt → signature → tampered-copy
slice. Real graph tests cover source version publication, idempotency, local audit chain and
source/artifact tamper detection. They do not establish automatic promise extraction, full
receipt history, business confirmation, policy authorization or external action read-back.

Real graph compatibility commands (the tested Homebrew Compose executable is `docker-compose`):

```sh
docker-compose -f backend/compose.spike.yaml config
docker-compose --progress quiet -f backend/compose.spike.yaml up -d --wait
docker image inspect falkordb/falkordb:v4.20.4 --format '{{json .RepoDigests}}'
cd backend
.venv/bin/python -m app.scripts.init_graph --tenant tenant-demo
RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest tests/integration -v
```

The pulled v4.20.4 image digest on macOS ARM64 was
`sha256:adbddd418916c25618564ff8597a919b08bc76452ebeb74eb985c38d7281df62`.
The v6.0.2 tag formerly written here did not exist on Docker Hub. This is a tested spike pin,
not a release/security endorsement.
Integration tests create and delete only generated `spike_*` graphs. Use a disposable server.
Without the opt-in variable, tests skip with an explicit reason. With opt-in they fail on
unavailable/incompatible servers. On 2026-10-12 the full opted-in suite passed 95 tests, including
the original four compatibility tests, graph initialization, promise and source API tests.
`init_graph` refuses an existing graph and never resets data. Remaining S01 tests
include restart/cache, persistence/restore and native constraint behavior; the spike is a subset.

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
