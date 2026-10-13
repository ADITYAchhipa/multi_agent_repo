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

## 2026-10-13 review/history verification and fixes

This entry supersedes the preceding review slice's unverified status. Inspected the current
status/diff, whitespace, review/history/idempotency/audit code, tests and documented setup.
Preserved existing uncommitted source/chunk/proposal work; stayed on `feat/backend` without
committing, merging or pushing.

Defects reproduced and fixed:

- FalkorDB rejected duplicate `v.id` return-column names in the detail query. Aliased the
  selected version and restricted default reads to the current pointer (explicit historical
  reads still select the requested version).
- Review could extend invalid receipt/audit history, including REVISE and REJECT. Every
  review decision now requires valid integrity and passing verification checks.
- Verification missed inconsistent current pointers and missing SUPERSEDES/HAS_EVENT links.
  It now checks graph linkage, contiguous signed versions, issuance state and current head.
- Idempotent replay bypassed changed source access controls. Replay now rechecks historical
  receipt access and equality. Graph revision is captured before validation; same-key races
  recheck the committed result when stale reads or mixed verification snapshots occur.
- Review omitted deadline projections from the graph write. Deadlines and current customer/
  project projections are persisted; historical detail content comes from the selected
  receipt payload, preserving that version's values.

Added `tests/integration/test_review_history.py` (27 real graph cases) and shared the existing
proposal fixture through `tests/integration/conftest.py`. These exercise independent successor
signature verification, parent hashes, historical/copied receipt verification, replay after
later versions, revised content read-back, idempotency conflicts, invalid receipt and audit
signatures, absent audit entries, inconsistent standing/version/pointer/edges, and correctly
signed audits whose digest/actor/decision contradict the receipt. The latter first establish
that the audit chain alone is VALID, then require receipt-history verification to fail.
Tenant tests map both tenants to the same graph and require foreign reads/reviews to fail.
Four concurrent requests test identical and different keys; only one successor/audit entry
is published. A deliberately invalid late Cypher write checks rollback and successful retry.
Graph storage is real; monkeypatches only synchronize reads or inject a write failure.

Commands ran from `backend/` using the existing `.venv`, unless noted:

| Command | Final result |
| --- | --- |
| `.venv/bin/ruff check .` | Passed |
| `.venv/bin/ruff format --check .` | Passed; 60 files formatted |
| `.venv/bin/pytest -q` | 97 passed, 0 failed, 37 skipped |
| `RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest -q` | 134 passed, 0 failed, 0 skipped |
| `git -c core.fsmonitor=false diff --check` (repository root) | Passed |

The final real suite executes all 37 integration cases, including all 27 review/history
cases. Both final pytest runs emit one existing Starlette TestClient/httpx deprecation warning.
Initial normal run: 97 passed/10 skipped. Initial real full run: 104 passed/3 failed (detail
query). Initial new review run: 10 passed/12 failed; fixes produced 22 passed, then full
129 passed. Additional audit/repeated-review cases exposed a same-key race (25 passed/1
failed), fixed to 26 passed; full suite then 133 passed. Deadline read-back regression
produced 26 passed/1 failed before the final fix and 134-pass full run. One sandboxed targeted
attempt had 26 setup errors because local TCP was denied; reran with approved network access.
Those errors and skipped offline tests are not evidence of graph compatibility.

Real environment: existing healthy `backend-falkordb-1`, `falkordb/falkordb:v4.20.4`, actual
Redis graph module version `42004`, reachable at `127.0.0.1:16379`. No restart was needed.
Confirmed with `docker-compose -f backend/compose.spike.yaml ps` and
`docker-compose -f backend/compose.spike.yaml exec -T falkordb redis-cli MODULE LIST` from root.
`docker image inspect falkordb/falkordb:v4.20.4 --format '{{json .RepoDigests}}'` confirmed
digest `sha256:adbddd418916c25618564ff8597a919b08bc76452ebeb74eb985c38d7281df62`.
Tests create and remove their own disposable graphs; existing application graphs are preserved.

Remaining limitations: no independently trusted audit checkpoint (whole-store rollback is
not detected); bounded verification (100 receipt versions/1000 audit events); PUBLIC_DEMO
access scope; conflict resolution and action eligibility remain unavailable. These tests are
not a load/stress proof or exhaustive coverage of every FULFILL/evidence/REVISE field combination.
No remaining failing test or environment blocker in the verified slice. Finance, simulation,
actions and full demo milestones are not established by this verification.

Final working-tree inventory: branch `feat/backend`, ahead of cached `origin/feat/backend`
by 1 pre-existing commit; 12 modified tracked files and 8 untracked files, none staged.
No commit or push was performed.

## 2026-10-13 Copilot findings: historical metadata, complete history and upload races

Reinspected the current uncommitted source and documented setup before changing it. Preserved
the earlier source/chunk/proposal/review work and all untracked files on `feat/backend`.
This entry supersedes the preceding 100-receipt/1000-audit verification limits.

### Findings and changes

1. **Historical metadata:** DETAIL now returns the actual `p.current_version_id` separately
   from the selected `v.id`. The selected signed receipt and historical content remain v1
   when requesting v1 after v2 publication; the summary current pointer remains v2. The real
   graph successor/history regression asserts both values.
2. **History dead end:** replaced the 101-row receipt read and 1001-row audit read with
   complete 100-row paginated iterators, preserving duplicate rows with deterministic
   tie-breakers. `services/history.py` retains one predecessor, verifies every signed
   receipt and its scoped audit/predecessor links, checks the complete signed audit chain,
   and checks the final current head. Verification detects graph-revision changes and fails
   closed for retry. There is no silently crossed lifecycle limit or truncated history.
   Per-receipt linkage reads are bounded to three rows: a valid version has at most two
   links, so an extra row invalidates it. Audit verification can discard per-event check
   output internally while still validating every event. Public detail/audit response arrays
   retain their contract shape and therefore grow with history; those responses are not
   claimed to use constant memory.
3. **Upload coordination:** independent services no longer rely on the process-local lock
   for correctness. Source publication atomically requires an absent operation ledger and
   matching graph revision/audit sequence. Recheck the ledger after reading state and after
   an unsuccessful publication CAS; same digest recovers the original operation with the
   caller's request ID, different digest raises `SourceConflict`. An unrelated writer with
   no matching committed operation still produces a retryable conflict. Two separate
   service instances/connections with distinct locks were synchronized immediately before
   real publication; identical requests both succeeded with one operation/version/audit,
   and differing requests produced exactly one success and one conflict. Later changed-body
   reuse was also rejected. This is persisted CAS recovery, not an added distributed lock.
4. **Source traversal:** STATE now scopes the current target and HAS_SOURCE_VERSION edge
   by tenant, active status, matching access label and source identity. An inaccessible
   target cannot be mistaken for genesis or unchanged content. SOURCE_DETAIL now excludes
   inactive edges and mismatched source identity. Existing source-version/chunk read paths
   already applied tenant/access/active checks. Five real-graph negative cases mutate the
   target tenant, edge status, edge tenant, target access label or edge access label; public
   detail/version/chunk reads deny access and fresh uploads cannot advance that source.
   Admin access-label bypass in source reads remains intentional; tenant and active-edge
   checks are not bypassed.
5. **Rollback boundary:** real audit suffix deletion is INVALID while the old head remains.
   After rewinding the stored head to the remaining signed prefix, `/api/audit/verify`
   returns VALID and explicitly reports no trusted checkpoint. A unit test independently
   establishes the same behavior. We do not claim detection of this rollback. If rollback
   resistance is required, store authenticated, monotonic tenant sequence/hash checkpoints
   outside this graph under independent access control. That entails another durable trust
   store, checkpoint publication/recovery semantics, availability/latency costs and restore
   tests; no such architectural change was introduced here.
6. **Route status:** inspected registered routes and corrected `API_CONTRACTS.md`'s blanket
   "not implemented" statement with a scoped implementation table. Updated backend README
   statements that still called historical reads/review/audit history unavailable. Proposed
   finance, simulations, chat, actions, connectors and other incomplete routes remain pending.

### Executed verification

Commands below ran from `backend/` with its existing virtual environment:

| Command | Actual final result |
| --- | --- |
| `.venv/bin/pytest tests/unit/test_audit.py tests/unit/test_receipts.py tests/unit/test_candidates.py tests/unit/test_artifacts.py -q` | 43 passed, 0 failed, 0 skipped |
| `.venv/bin/pytest -q` | 101 passed, 0 failed, 47 skipped |
| `RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest tests/integration/test_review_history.py tests/integration/test_upload_coordination.py -q` | 37 passed, 0 failed, 0 skipped |
| `RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest -q` | 148 passed, 0 failed, 0 skipped (27.93 seconds) |
| `.venv/bin/ruff check .` | Passed |
| `.venv/bin/ruff format --check .` | Passed; 63 files formatted |
| `git -c core.fsmonitor=false diff --check` (root) | Passed |

All 47 real integration cases executed in the full opt-in run; none of its success count is
from skipping graph tests. New coverage includes v99/v100/v101 verification and subsequent
review through v102, historical v1 reads at those boundaries, rejection of a corrupted earlier
page, and a valid 1001-event audit history followed by source publication and receipt
verification. Corrupting event 1000 is detected. The graph was real, not mocked; concurrency
tests only synchronize calls to the real driver. New tests are 10 integration cases plus four
unit cases; the existing historical metadata test gained the pointer assertion.

Intermediate results: first targeted real run 36 passed; after adding the >1000-event case,
37 passed. The first new unit run had 39 passed/4 failed because the test Settings fixture
omitted the required signing-key configuration tuple; corrected the fixture and reran to
43 passed. Initial lint/format issues were corrected before the final clean checks. A shell
attempt to run `.venv/bin/ruff` from root could not find that path; all actual checks used
`backend/.venv`. Normal and integration/full runs emitted the existing single Starlette
TestClient/httpx deprecation warning; the targeted unit run emitted none.

Verified the existing server with root commands
`docker-compose -f backend/compose.spike.yaml ps` and
`docker-compose -f backend/compose.spike.yaml exec -T falkordb redis-cli MODULE LIST`:
healthy `backend-falkordb-1`, image `falkordb/falkordb:v4.20.4`, graph module `42004`, local
test endpoint `127.0.0.1:16379`. No server restart or application-graph deletion was needed;
tests created/deleted disposable `spike_*` graphs. Networked tests ran with approved access.

Remaining risks: complete verification does more work as histories grow; offset pagination,
per-version link queries and full response arrays need performance work before production
scale. This run is not a load test. Concurrent graph changes may require retry. Whole-store
rollback remains undetectable without an independent checkpoint. PUBLIC_DEMO scope and
disabled action eligibility remain unchanged; broader milestones are not complete.

Files changed in this follow-up: `backend/README.md`, `backend/app/api/promises.py`,
`backend/app/graph/queries/{promises,sources}.py`, `backend/app/graph/repository.py`,
`backend/app/services/{audit,history,source_ingest}.py`,
`backend/tests/integration/{test_review_history,test_upload_coordination}.py`,
`backend/tests/unit/test_audit.py`, `docs/API_CONTRACTS.md`, and this file.
Final status: `feat/backend` remains ahead of cached `origin/feat/backend` by the same existing
commit, with 14 modified tracked files and 11 untracked files, none staged. No reset, stash,
discard, merge, commit or push was performed.

## 2026-10-13 final audit verification hardening

Investigated the two follow-up review findings against the current local tree before editing.
The installed FalkorDB Python client performs one `GRAPH.RO_QUERY` per call; the existing
bounded pagination requires multiple calls and does not provide one shared read snapshot.
The implemented consistency strategy therefore checks a boundary of tenant graph revision,
audit sequence and audit head hash before and after each complete verification attempt.
Receipt verification additionally compares the promise pointer/revision/state before and
after. At most three attempts are made. A stable invalid chain or receipt history still
fails; an unstable audit read returns `INDETERMINATE` with no claimed checked range and an
unstable receipt read returns `UNAVAILABLE`. The API reports why the result is unavailable.

The currently supported source-import/update and review publications append the audit event
and change `GraphState.revision`, `audit_sequence` and `audit_head_hash` in the **same** guarded
Cypher write. Each publication now also compares the current audit head to the head used to
sign its successor, including the empty head at genesis. This prevents a write from silently
appending after a head change that did not advance revision or sequence. New real-graph tests
change the head immediately before each publication and confirm that no new receipt/source or
audit event appears. Prior rollback tests prove a failed late query does not publish a partial
write. The new real-graph race tests verify that a committed source upload or review changes the
boundary and triggers a retry. This boundary detects legitimate concurrent application
writes even when one lands between audit pages. It is not a database-wide, immutable read
snapshot. Direct graph edits outside these publication paths are not guaranteed to advance
the revision; an independently trusted checkpoint is still required to detect whole-store
rollback or a coordinated rewrite of the local head/history.

The receipt history verifier now checks signed `event_type` against the graph event-type
projection and the receipt lifecycle. A version-1 PROPOSED receipt must be issued by
`SOURCE_IMPORTED` or `SOURCE_UPDATED` and refer to the source/version/hash in that event.
Both genesis types are required: publication of a changed existing source may discover a
new assertion and issue that assertion's first receipt. A successor must have a
`PROMISE_REVIEW` event targeting the same promise/receipt, a valid predecessor and a
decision that leads from its parent's issuance state to its own issuance state. The current
workflow still forbids confirming a disputed parent until conflict resolution exists.
The confirmation actor/event binding and signed receipt digest manifest remain checked.
There is no compatibility exception for other audit event types to issue receipts. General
audit-chain verification can verify other event types without treating them as receipt
issuance; it also checks that a stored event type equals its signed event type.

### Executed commands and results

Commands ran from `backend/` using its existing virtual environment, except Docker and Git
commands from the repository root:

| Command | Actual result |
| --- | --- |
| `.venv/bin/pytest tests/unit/test_audit.py tests/unit/test_history.py -q` | 9 passed, 0 failed, 0 skipped |
| `.venv/bin/pytest -q` | 106 passed, 0 failed, 58 skipped |
| `RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest tests/integration/test_review_history.py::test_review_commit_during_history_verification_retries tests/integration/test_upload_coordination.py::test_source_commit_during_paginated_audit_read_retries -q` | 2 passed, 0 failed, 0 skipped |
| `RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest tests/integration/test_review_history.py::test_review_publication_rejects_changed_audit_head tests/integration/test_upload_coordination.py::test_source_publication_rejects_changed_audit_head tests/integration/test_review_history.py::test_signed_successor_replay_and_historical_reads tests/integration/test_upload_coordination.py::test_independent_instances_recover_committed_ledger -q` | 5 passed, 0 failed, 0 skipped |
| `RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest tests/integration -q` | 58 passed, 0 failed, 0 skipped (33.58 seconds) |
| `.venv/bin/ruff check .` | Passed |
| `.venv/bin/ruff format --check .` | Passed; 64 files formatted |
| `git -c core.fsmonitor=false diff --check` | Passed |

The 58 integration tests used actual FalkorDB queries and disposable `spike_*` graphs, not a
mock graph. Test synchronization paused the audit read at an exact query/page boundary and
released it after a real review or upload committed. A separate controlled double advanced
the boundary on every attempt to exercise exhaustion. Stable bad signatures and broken
audit links still returned `INVALID`; correctly re-signed but semantically wrong event types
kept the general audit chain `VALID` while receipt-history checks failed. Unit tests cover
both permitted genesis event types, a valid successor, wrong type, invalid decision and
invalid transition. Existing review/history tests remained green.

The first real-graph targeted run after adding synchronization hooks reported 44 passed and
2 failed: the test assumed its named ThreadPoolExecutor thread would run FastAPI's handlers,
but FastAPI dispatched those handlers in its own thread pool. Corrected the deterministic
hook to pause the first relevant graph read; the two focused tests then passed, followed by
the complete 58-pass graph suite. An earlier Ruff formatting check identified two files;
both were formatted before the final clean check. A later Ruff lint check found one import
order error in a new test; it was corrected before the final clean check. The normal and
integration runs each emitted one existing Starlette TestClient/httpx deprecation warning;
focused unit tests emitted none. The healthy Docker service was `backend-falkordb-1`, image
`falkordb/falkordb:v4.20.4`, graph module `42004`, checked with the documented Compose
`ps` and `redis-cli MODULE LIST` commands. No restart was needed.

Remaining limits: verification may return unavailable under sustained writes; callers can
retry after writes settle. Pagination and full audit/receipt verification costs grow with
history. The graph boundary is only as reliable as the rule that all authorized writes
advance it atomically. Local audit verification still cannot detect an attacker who deletes
a valid suffix and rewinds its local head, as demonstrated by the earlier rollback test.
No external checkpoint, finance/simulation/action workflow or full demo gate was added.

Files changed in this follow-up: `backend/app/api/audit.py`,
`backend/app/graph/queries/{promises,sources}.py`, `backend/app/graph/repository.py`,
`backend/app/models/audit.py`, `backend/app/services/{audit,history}.py`,
`backend/tests/integration/{test_review_history,test_upload_coordination}.py`,
`backend/tests/unit/{test_audit,test_history}.py`, and this file. Earlier modified and
untracked files remain intact. No reset, clean, stash, discard, merge, commit or push.
Final Git status: `feat/backend` is ahead of cached `origin/feat/backend` by the same
pre-existing commit; 16 tracked files are modified, 12 files are untracked, and nothing is
staged.

## 2026-10-14 Python syntax and receipt-binding review

Checked the exact current checkout after an independent review flagged 11 comma-separated
`except` clauses in `history.py`, `audit.py`, `sources.py`, `promises.py`, `auth.py`, and
`connection.py`. All flagged text is present. The project requires Python `>=3.14,<3.15`
and Ruff targets `py314`; the installed environment is Python 3.14.7. In this Python version,
those clauses parse as multiple-exception handlers: `ast.parse` parsed all 63 app/test Python
files and identified the flagged handlers as `ast.Tuple` nodes. `compileall` succeeded before
and after the regression tests were added, and Ruff accepts the current formatting. Thus no
syntax error was confirmed and no exception handling was changed. The review appears to have
applied an older Python grammar assumption to this Python 3.14 checkout; it was not a missing
line or a failed test hidden by skipped graph coverage. Python versions below 3.14 are outside
the declared and tested range.

Added real-FalkorDB regression coverage for two receipt-history bindings. A validly re-signed
review audit event targeting a different `receipt_id` or `promise_id` leaves the general audit
chain `VALID` but fails the receipt-history check. Redirecting a successor's `SUPERSEDES` edge
to another real receipt in the same tenant likewise fails `RECEIPT_HISTORY`, while the audit
chain itself remains `VALID`. No production verifier change was needed: the current verifier
already enforced both bindings. The new tests exercise that behavior through the HTTP API and
disposable real `spike_*` graphs.

### Executed commands and results

Commands using `.venv` ran from `backend/` except the root-level `backend/.venv/bin/python`
compile command. Git and Docker commands ran from the repository root.

| Command | Actual result |
| --- | --- |
| `git -c core.fsmonitor=false status --short --branch` | `feat/backend`, ahead of cached origin by one existing commit; existing modified and untracked work retained |
| `backend/.venv/bin/python --version` | Python 3.14.7 |
| `backend/.venv/bin/python -m compileall -q backend/app backend/tests` | Passed before and after test edits; 0 compilation errors |
| Python `ast.parse` over `backend/app` and `backend/tests` | Parsed 63 files; 20 tuple exception handlers including all 11 flagged lines |
| `docker-compose -f backend/compose.spike.yaml ps` | `backend-falkordb-1`, image `falkordb/falkordb:v4.20.4`, healthy |
| `RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest tests/integration/test_review_history.py::test_valid_audit_signature_cannot_hide_receipt_mismatch tests/integration/test_review_history.py::test_redirected_supersedes_edge_fails_history_verification -q --tb=short` | **6 passed, 0 failed, 0 skipped, 1 warning** after correcting a new test assertion to use `code` |
| `.venv/bin/pytest tests/unit/test_audit.py tests/unit/test_history.py -q` | **9 passed, 0 failed, 0 skipped** |
| `.venv/bin/pytest -q` | **106 passed, 0 failed, 61 skipped, 1 warning**; skips are the opt-in integration tests |
| `RUN_FALKORDB_INTEGRATION=1 .venv/bin/pytest tests/integration -q` | **61 passed, 0 failed, 0 skipped, 1 warning** against real FalkorDB |
| `.venv/bin/ruff check .` | Passed |
| `.venv/bin/ruff format --check .` | Passed; 64 files already formatted |
| `git -c core.fsmonitor=false diff --check` | Passed |

The first focused real-graph attempt inside the sandbox produced six fixture setup errors
because the sandbox denied the localhost socket. The approved external rerun reached FalkorDB:
five cases passed and the new redirect case failed only because its assertion used a nonexistent
`name` field. The API check field is `code`; correcting the assertion yielded the six-pass run
above. The sole warning in each full HTTP test run was the existing Starlette TestClient/httpx
deprecation warning. No graph test was counted as passed while skipped or while socket access
was denied.

Limits from the prior sections remain: Python <3.14 is unsupported; verification still lacks
an independent rollback checkpoint, and broader finance, simulation, action and demo milestones
are not established by these tests. This review changed the existing untracked
`backend/tests/integration/test_review_history.py` and this notes file only; it did not commit,
push, merge, reset, clean, stash, discard or overwrite earlier work.
