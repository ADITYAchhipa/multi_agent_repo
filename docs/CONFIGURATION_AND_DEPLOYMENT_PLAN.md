# Configuration and deployment plan

Status: future implementation plan only. No environment files, Dockerfiles, Compose files, scripts, CI workflows or infrastructure have been created. BASELINE §§3, 15. Values below are proposed defaults/placeholders, never real secrets or working credentials.

## 1. Environment catalogue

“Secret” means server-only, omitted from logs/UI/graph/model. The future implementation validates all config before enabling dependent capability; a missing optional connector does not stop fixture mode. Production must refuse insecure demo auth/plaintext remote database configuration.

| Name | Type / proposed default | Requirement and handling |
|---|---|---|
| APP_ENV | enum development/demo/production; development | Controls explicit safety/deployment profile |
| DEMO_MODE | boolean true | Visible DEMO DATA banner; production false |
| API_KEY | secret placeholder; no default value | Baseline legacy local credential; map to one named actor only, never blanket admin/browser bundle |
| DEMO_ACTOR_CREDENTIALS_PATH | server secret path, unset | Proposed extension: per-actor credentials/roles/tenant; required for multi-role demo; API_KEY alone insufficient for separation test |
| SESSION_SECRET | secret unset | Session integrity; startup-required for UI session use |
| SESSION_IDLE_MINUTES / SESSION_MAX_HOURS | integers 60 / 8 | Proposed local session lifetimes |
| FALKORDB_HOST / FALKORDB_PORT | host falkordb / int 6379 | Backend network only |
| FALKORDB_PASSWORD | secret unset | Remote DB requires auth; local isolated profile explicitly configured |
| FALKORDB_GRAPH | string company_demo | Default tenant map entry; never request override |
| TENANT_CONFIG_PATH | server config path unset | Maps authenticated tenant to graph/ACL/role policy |
| FALKORDB_TLS | boolean false local only | Remote production true plus certificate verification |
| FALKORDB_QUERY_TIMEOUT_MS | int 2000 | Bounded query budget, test actual client syntax |
| LLM_PROVIDER | enum configured adapter, baseline openai_compatible | Provider is not selected/tested in this phase |
| LLM_API_KEY | secret unset | Required only for enabled generated analysis |
| LLM_MODEL / LLM_BASE_URL | strings unset | Server-configured, approved host/model; no user URL |
| LLM_TIMEOUT_SECONDS | int 45 | Per-call bound |
| LLM_MAX_TOOL_CALLS | int 5 | Shared across normal question's roles |
| LLM_MAX_OUTPUT_BYTES | int 32768 | Strict role output cap |
| LLM_RUN_TOKEN_BUDGET | positive int, owner-set | No price/budget invented; report usage if provider supplies it |
| OPERATION_DEADLINE_SECONDS | int 180 | Bounded analysis operation |
| MAX_INGESTION_CHUNKS | int 200 | Import/run cap |
| PROMISEOPS_SOURCE_DIR | absolute server path /app/data/sources | Generated artifact paths; not secret/key directory |
| PROMISESEAL_SIGNING_KEY_PATH | secret file /run/secrets/promise_seal_demo_ed25519.pem | Must exist for signed mode; never create silently in production |
| PROMISESEAL_KEY_ID | string demo-key-1 | Public metadata, must match trusted registry |
| PROMISESEAL_ISSUER_ID | string promiseops-demo | Proposed configured platform issuer |
| PROMISESEAL_PUBLIC_KEYS_PATH | trusted server registry path unset | Required for key trust/rotation; no client-provided trust |
| PROMISESEAL_CANONICALIZATION | literal promiseops-json-v1 | Reject unsupported profile; protocol owns bytes |
| VEXA_BASE_URL / VEXA_API_KEY | approved URL unset / secret unset | Optional source adapter, exact auth mapping S04 |
| GRAPH_TENANT_ID / GRAPH_CLIENT_ID | identifiers unset | Proposed optional Microsoft config; exact auth flow S04 |
| GRAPH_CLIENT_SECRET | secret unset | Only if selected app auth needs it; certificate alternative evaluated later |
| GRAPH_ORGANIZER_ALLOWLIST | configured IDs unset | Optional direct Graph scope; no arbitrary organizer |
| JIRA_BASE_URL | approved Cloud site URL unset | Host allowlist; scheme validation |
| JIRA_EMAIL / JIRA_API_TOKEN | account identifier unset / secret unset | Baseline token auth option; OAuth alternative owner-approved |
| JIRA_PROJECT_KEYS | configured list unset | Required for live sync scope |
| JIRA_FIELD_MAPPING_PATH | config path unset | Explicit project field and status maps |
| JIRA_WRITES_ENABLED | boolean false | Needs passing sandbox contract gate and permissions |
| WORKLOAD_MODE | enum mock/import/live; mock | Prominent MOCK MODE badge |
| WORKLOAD_API_BASE_URL / WORKLOAD_API_TOKEN | unset / secret unset | Reserved placeholders, not evidence of real vendor auth scheme |
| WORKLOAD_MAPPING_PATH | reserved path /app/config/workload_mapping.yaml | Future path only; mapping file not created; live schema remains unspecified |
| WORKLOAD_WRITES_ENABLED | boolean false | Ignored/blocked without complete verified live contract; mock writes have own approved workflow |
| DEMO_ANCHOR_DATE / DEMO_TIMEZONE | date 2026-10-12 / UTC | Fixture calendar, distinct from actual server operational time |
| MAX_UPLOAD_MB / MAX_GRAPH_NODES | ints 20 / 60 | Define upload unit as MiB in backend; UI shows MiB |
| MAX_GRAPH_DEPTH / MAX_CONNECTOR_PAGES | ints 3 / 10 | Explicit truncation and bounded sync |
| SOURCE_AGING_DAYS / SOURCE_STALE_DAYS | ints 30 / 90 | General defaults; not operational workload freshness |
| WORKLOAD_MAX_AGE_HOURS | int 24 | Capacity-specific blocking threshold |
| APPROVAL_TTL_MINUTES | int 15 | Bound approval validity |
| RETENTION_POLICY_PATH | unset | Real data disabled until owner policy supplied |
| AUDIT_CHECKPOINT_DIR | local protected export path unset | Local export is not independently trusted external storage |
| LOG_LEVEL | enum INFO default | Redaction mandatory at every level |

Do not put connector keys under NEXT_PUBLIC names. Frontend receives only safe mode/capability/health DTOs. Ports/image tags/runtime versions are not secrets but must be pinned from S01–S03 rather than copied from floating latest docs.

## 2. Future local architecture

Three services: frontend UI/proxy; backend single process and serialized mutation queue; FalkorDB with persistent graph volume. Backend mounts source artifact volume and read-only secret key/config mounts. Frontend has no DB/source/secret mounts. Expose UI on localhost; backend/DB internal network, with temporary presenter-only loopback diagnostics if needed. Optional FalkorDB Browser stays loopback. No additional queue, SQL or vector service. Vexa hosted API optional; its full self-host stack is a separate project, never PromiseOps' business database.

Later deployment artifacts should pin exact image digests, nonroot process users where supported, read-only filesystem except declared volumes, process/resource limits, graceful shutdown and health dependencies. No claim that these settings have been verified against a selected image. Keep one writer/backend replica until S01 concurrency strategy passes; do not scale replicas by changing a Compose setting without redesigning claims/leases.

## 3. Alternatives and trade-offs

| Option | Benefits | Costs / gates |
|---|---|---|
| Local three-service demo | Offline fixture repeatability, simplest trust/network boundary | Presenter machine dependency, limited concurrency, no HA |
| Single secured VM with persistent storage | Simple hosted pilot using same boundaries | HTTPS/identity, patching, backup, key custody and licensing review required |
| Managed FalkorDB + application containers + approved object storage | Outsourced DB operations, durable artifact service | Network/egress cost, service terms, tenant/auth/restore behavior S01/Q09; no new business DB |
| Multi-worker production deployment | Higher throughput | Durable fencing/leases, distributed recovery, concurrency and operational ownership; not MVP |

No current prices or total cost estimates are claimed. Cost model for later owner review: database RAM/storage/backups + app CPU/RAM + artifact storage/egress + model input/output tokens at selected provider rates + transcript provider usage + operational time. Record measured per-run token counts/latency before estimating spend. File import removes transcript-provider availability/cost from demo, not from future production planning.

## 4. Startup and health

Startup validate schema versions, tenant graph mapping, required auth config, signing key/registry match, source storage writability/safe path, graph connection/query timeout, required indexes and unsupported settings. Required graph unavailable → not ready; missing optional connector → healthy fixture mode plus configured=false. Signing unavailable → no signed verification claim and consequential writes blocked. Do not silently create a new graph after a typo in production configuration.

Liveness is process-local internal probe; public `/api/health` returns API/graph readiness only. Authenticated `/api/health/knowledge` returns authorized quality/freshness counts. `/api/connectors` exposes safe health/mode, never secret values. Readiness must not call expensive model/transcript APIs on every poll. Resume queued operations and reconcile stale EXECUTING actions before accepting new writes after restart.

## 5. Backups, restore and audit checkpoints

S01 must verify selected FalkorDB persistence format, backup/restore procedure and version compatibility using official docs and a real restore test. Do not assume a live volume copy is consistent. Capture a graph checkpoint/revision plus artifact manifest/hashes and public-key registry; quiesce writes for a local coherent backup. Encrypt protected backups and signing-key backups separately, with access restricted. Backing up the private key and graph together weakens compromise containment.

On restore: validate graph/ontology/profile versions; artifact hashes; receipt/audit chains; known external checkpoint head; apply deletion/tombstone policy; mark every potentially dispatched action for read-only reconciliation against external state. Restored APPROVED/EXECUTING actions must never blindly reexecute. Demo recovery target proposed RPO one completed seed/checkpoint and RTO 15 minutes; production RPO/RTO is Q09, not claimed tested.

## 6. Observability and operations

Structured diagnostic logs: request/run/action IDs, phase/template IDs, safe error codes, graph revision, duration, counts, retry/dispatch outcomes, provider usage when returned. No raw customer quote, credential, full prompt, signing key or hidden reasoning. Metrics: ingestion acceptance/rejection, unresolved conflict/stale count, graph query duration/timeouts, model usage, simulator unknown/constraint failures, action dispatch/read-back mismatch/reconciliation count, audit verification failures, artifact missing count.

Alert proposed: any signature/source hash mismatch; any unapproved write (must be zero); any reconciliation pending; graph unavailable; mutation publish failure; critical source deletion error. Demo UI suffices for local alerts; no unsolicited Slack/email integrations. Production alert destinations are owner-configured.

Graceful shutdown stops claiming work, records phase, lets bounded graph publication finish, never assumes an in-flight external request failed. Dependency/version changes require rerunning affected compatibility/restore/receipt vectors and updating future implementation notes. Commands/config files are future work; this phase does not create or run them.
