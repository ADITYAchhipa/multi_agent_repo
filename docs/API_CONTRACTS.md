# Application API and adapter contracts

Status: v1 design contracts with partial backend implementation. Baseline §8's 22 routes are retained; additions are marked EXTENSION (D11). Application-owned DTOs below are not vendor API schemas. Schema/protocol documents own graph labels and signed payload definitions.

### Implementation status (current backend working tree, 2026-10-13)

This mapping describes registered routes and their implemented scope, not completion of every
behavior in the design tables below. Routes absent from the implemented rows remain proposed.

| Status | Routes | Current scope / limits |
| --- | --- | --- |
| Implemented | `GET /api/health` | Existing configured graph readiness; separate `/internal/live` process probe |
| Implemented, demo only | `POST /api/session`, `GET /api/session` | Configured local identities; production identity and logout remain pending |
| Implemented, constrained ingestion | `POST /api/sources/upload`, `GET /api/sources/{source_id}`, `GET /api/operations/{operation_id}` | UTF-8 text/Markdown, deterministic chunks/candidates, signed publication and persistent operation reads; VTT, meeting context, reprocessing and cancellation pending |
| Implemented, partial projections | `GET /api/promises`, `GET /api/promises/{promise_id}` | PUBLIC_DEMO reads, historical receipt selection; current-version pointer stays current. Risk filters, finance/scope calculations and conflict resolution remain pending |
| Implemented, constrained review | `POST /api/promises/{promise_id}/review` | Authorized signed successor publication with revision/idempotency guards; disputed confirmation requires the unimplemented conflict workflow |
| Implemented | `GET /api/promises/{promise_id}/verify`, `POST /api/receipts/verify`, `GET /api/audit/verify` | Signed bytes, available source evidence and complete paginated history/audit verification; no independent rollback checkpoint; action eligibility remains false |
| Proposed, unimplemented | All other routes below | Includes knowledge health, connector import/sync/list, chat, simulations, actions/approvals/reconciliation, generic graph/trace, key lookup, revoke/retire, conflict resolution, session logout and operation cancellation |

The historical receipt is identified by `receipt.payload.receipt_id`; `promise.current_version_id`
is the current graph pointer even when `version_id` selects an older receipt. Selected receipt
content and standing describe that historical version; the promise revision remains current.

## 1. Transport, auth, errors and scalar conventions

All application routes use `/api`, same-origin HTTPS outside localhost, UTF-8 JSON except multipart upload. Unknown request keys rejected. Client cannot supply `tenant_id`, actor, approval role, signing key, graph name, query text or connector URL. Server derives these from session/configuration. Opaque IDs are URL-encoded; never interpreted as paths.

Every response includes `request_id`; response header `X-Request-ID` matches. Client may provide a bounded `X-Request-ID` correlation hint (ASCII 1–64) but server creates authoritative ID if absent/invalid; it is not an authorization or idempotency key. Success uses top-level fields in the endpoint tables, not a generic `data` wrapper. Shared optional `warnings:Warning[]` contains code/message/evidence refs. Read collections have `{request_id, items, next_cursor}`; default limit 25, max 100; opaque cursor binds tenant/filter and expires after 15 minutes.

All mutations except session bootstrap require `Idempotency-Key` (opaque 16–128 characters). Ledger key is tenant+actor+method+route+key, bound to canonical request digest. Same key/body returns original resource/result; same key/different body returns 409 IDEMPOTENCY_CONFLICT. Retain ledger at least as long as action/run records; expiry must never enable redispatch of a completed action. Approval/execution additionally require expected resource revision. JSON errors never include raw sources or tokens.

Illustrative error:

```json
{"error":{"code":"STALE_APPROVAL","message":"Relevant inputs changed; create a fresh proposal and approval.","request_id":"req-demo","details":[{"field":"dependency_digest","reason":"changed"}]}}
```

Statuses: 200 read/review/completed operation; 201 new scenario/proposal; 202 durable queued run or executing action; 204 not used where request_id would be lost. 400 invalid query/filter; 401 missing/expired auth; 403 capability/role failure; 404 absent or inaccessible object; 409 invalid transition/stale revision/idempotency mismatch; 413 oversized input; 415 unsupported type; 422 DTO/evidence validation; 429 rate limit; 502 invalid provider response; 503 unavailable graph/connector; 504 bounded timeout. Retry-After supplied on throttling when known. Integrity failure from a verify route is a **200 verification result**, not a transport error.

Timestamps: UTC millisecond RFC3339; dates separate; decimal quantities as normalized strings, unit explicit. Monetary display may add two decimal places for USD but signed/calculation values use normalized decimal strings. `null` means unknown; empty arrays mean no known entries. No NaN/Infinity. Field identifiers in this document are application design decisions except the explicitly verified external fields in §8.

## 2. Shared DTOs

Notation: `?` = nullable; `[]` = array; all listed keys required unless explicitly “optional”. IDs must resolve in tenant/ACL. Maximum evidence refs per response 200; truncation explicit.

| DTO | Fields / validation |
|---|---|
| EvidenceRef | `evidence_ref_id`, `source_id`, `source_version_id`, `source_hash`, `representation_hash`, `origin_reference` (safe logical source URI or approved provider reference, never a server path/secret URL), `quote:string?`, `start_offset:int?`, `end_offset:int?`, `start_ms:int?`, `end_ms:int?`, `structured_pointer:string?`, `source_updated_at:timestamp?`, `observed_at`, `verification:VERIFIED\|REJECTED\|UNAVAILABLE`, `access_label`; quote+offset or structured pointer required, not an unsupported locator |
| SourceSummary | `id`, `source_type`, `title`, `current_version_id`, `source_updated_at?`, `ingested_at`, `content_hash`, `retention_state`, `parse_status`, `mode:IMPORT\|MOCK\|LIVE`; no server filesystem paths |
| PromiseSummary | `id`, `current_version_id`, `revision`, `current_state`, `receipt_standing`, `customer_id?`, `project_id?`, `deliverable`, `deadline`, `scope_status`, `risk_flags[]`, `freshness`, `open_conflict_ids[]` |
| Freshness | `level:FRESH\|AGING\|STALE\|UNKNOWN`, `as_of?`, `evaluated_at`, `threshold_seconds`, `source_version_ids[]`; computed from source as-of/update, never solely ingestion time |
| Calculation | `calculation_id`, `formula_id`, `formula_version`, `amount:string?`, `currency:string?`, `status:ESTIMATE\|AT_RISK\|CONFIRMED\|UNKNOWN`, `inputs:[{name,value?,unit,evidence_ref_ids}]`, `computed_at`, `missing_inputs[]`; no derived total across overlapping exposures |
| GraphNode | `id`, `label`, `display_name`, `status?`, `source_ref_ids[]`, `properties` (label-specific safe projection) |
| GraphEdge | `id`, `type`, `from_id`, `to_id`, `status`, `provenance_kind`, `evidence_refs[]`, `derived:boolean`, `underlying_edge_ids[]`, `scenario_only:boolean` |
| GraphPath | `path_id`, `template_id`, `node_ids[]`, `edge_ids[]`, `graph_revision`, `evidence_ref_ids[]`; each edge connects adjacent nodes with direction stated; IDs from actual tool results |
| PolicyCheck | `rule_id`, `outcome:PASS\|BLOCK\|NEEDS_REVIEW`, `reason`, `evidence_ref_ids[]`; produced by backend |
| AuditRecord | `id`, `sequence`, `event_type`, `actor_id`, `occurred_at`, `request_id`, `payload` (typed by event), `prev_event_hash?`, `event_hash`, `signature_base64url`, `key_id`, `canonicalization` |
| TraceStep | `step_id`, `phase`, `tool_id`, `template_id?`, `safe_parameters`, `started_at`, `duration_ms`, `row_count`, `returned_entity_ids[]`, `returned_edge_ids[]`, `source_ref_ids[]`, `outcome`, `error_code?`; backend generated |
| Operation | `id`, `kind`, `status`, `phase`, `created_at`, `started_at?`, `finished_at?`, `result?`, `errors[]`, `progress:{completed,total?}` |
| ReceiptEnvelope | `payload` defined exactly in PromiseSeal protocol, `payload_sha256`, `signature_base64url?` |
| Verification | `integrity:VALID\|INVALID\|UNSIGNED\|INDETERMINATE`, `standing:ACTIVE\|SUPERSEDED\|REVOKED`, `checked_at`, `checks:[{code,result:PASS\|FAIL\|UNAVAILABLE,field?,reason}]`, `source_results[]`, `key_trust:TRUSTED\|RETIRED\|COMPROMISED\|UNKNOWN`, `eligible_for_action:boolean` |

Detail responses may contain fewer quotes for a caller lacking source access, but must not publish an unredacted signed payload with hidden quotes. If the receipt itself contains inaccessible evidence, the receipt/detail/verify endpoint returns 404; collection responses may show a safe authorized PromiseSummary only if its own ACL allows it. Never mutate/redact a signed payload and call its signature valid. Receipt Verification.eligible_for_action means eligible supporting evidence only; it does not grant approval or execution authority.

## 3. Health, sources and connectors

| Route | Authorization and request | Success contract / side effects |
|---|---|---|
| `GET /api/health` | Public localhost-safe; no params | `{request_id,status:OK\|DEGRADED,services:{api,graph},checked_at}`; graph disconnected → 503; no graph names/customer counts |
| `GET /api/health/knowledge` | Any authenticated role, authorized scope | `{request_id,graph_revision,counts:{nodes,edges,stale_sources,open_conflicts,unresolved_promises,open_findings},findings[],next_cursor}`; counts filtered by access |
| `POST /api/sources/upload` | admin; multipart `file`, `source_type`, optional configured `source_key`, `meeting_context` JSON string (title/start/timezone), `access_label`; 20 MiB and approved types | 202 `{request_id,operation_id,source_id,status_url}`; same source bytes after prior success → 200 `{request_id,source_id,source_version_id,outcome:NO_CHANGE}` |
| `POST /api/sources/{source_id}/reprocess` | admin; `{expected_source_version_id,parser_profile,extraction_profile,reason}`; profiles server allowlisted | 202 operation reference; identical facts do not duplicate receipts; new extraction disagreement goes to review |
| `GET /api/sources/{source_id}` | Authorized read; optional `version_id`, `chunk_id` | `{request_id,source:SourceSummary,version:{id,source_hash,representation_hash,availability},snippets:EvidenceRef[],versions:[{id,version,source_updated_at?,availability}]}` |
| `POST /api/connectors/vexa/import` | admin; `{connector_id,platform,meeting_id,consent_reference}`; configured provider only | 202 operation reference; normalized source follows same firewall; no bot creation in MVP |
| `POST /api/connectors/jira/sync` | admin; `{connector_id,query_profile_id,max_issues}`; max 500, configured JQL/project allowlist | 202 operation reference; bounded paginated sync; no write permission granted by sync |

Ingestion result: `{outcome:IMPORTED|UPDATED|NO_CHANGE|QUARANTINED|PARTIAL,source_id,source_version_id?,counts:{new_entities,new_edges,unchanged,retired,rejected_quotes,conflicts},finding_ids[],error_codes[]}`. A failed critical parse does not replace the current source version. Source import is not automatically confirmation of assertions.

## 4. Promises, review and verification

| Route | Request | Success contract |
|---|---|---|
| `GET /api/promises` | Auth read; optional `status`, `customer_id`, `deadline_from`, `deadline_to`, `risk`, `cursor`, `limit` | Collection of PromiseSummary; filters are closed enums/validated IDs |
| `GET /api/promises/{promise_id}` | Auth read; optional `version_id` | `{request_id,promise:PromiseSummary,receipt:ReceiptEnvelope,versions:[{receipt_id,version,status_at_issuance,standing}],evidence:EvidenceRef[],scope_assessment,calculations[],related_issue_ids[],milestone_ids[],conflicts[],graph_paths[]}` |
| `POST /api/promises/{promise_id}/review` | reviewer; `{expected_version_id,expected_revision,decision:CONFIRM\|DISPUTE\|REJECT\|FULFILL\|REVISE,reason,evidence_ref_ids[],revised_content?}`; revised_content only for REVISE, content fields allowlisted | `{request_id,promise:PromiseSummary,receipt:ReceiptEnvelope,audit_event_id}`; transition table from protocol; 409 if pointer/revision changed |
| `GET /api/promises/{promise_id}/verify` | Auth read; optional `version_id` (current default) | `{request_id,receipt_id,verification:Verification}`; reads bytes afresh, no cached success claim |

`scope_assessment` fields: `{status,claim,clause_ids[],evidence_refs[],conflict_ids[],missing_evidence[],assessment_kind:LLM_REVIEWED|DETERMINISTIC_RULE,reviewed_by?}`. Label suggestions as such. Evidence quality comes from backend scoring in agent document.

## 5. Chat and scenarios

`POST /api/chat`: any authenticated role. Request `{question:string(1..4000),session_id?:opaque,context?:{promise_id?,customer_id?}}`. A session is conversation correlation, not authorization. 200 synchronous result when within timeout; 202 `{request_id,operation_id,status_url}` for longer work. Polling returns the same completed result type. No raw Cypher/tool names/URLs accepted from user.

Completed chat result (all keys required): `{request_id,answer,confirmed_claims:[{claim_id,text,evidence_ref_ids,graph_path_ids}],hypotheses:[{claim_id,text,assumptions,evidence_ref_ids}],promise_ids[],graph_paths:GraphPath[],sources:EvidenceRef[],conflicts[],freshness:Freshness,evidence_quality:LOW|MEDIUM|HIGH,caveats[],calculations:Calculation[],scenario_ids[],trace:{steps:TraceStep[]},analysis_mode:GENERATED|DETERMINISTIC_ONLY|REPLAY,graph_revision}`. `confirmed_claims` means source/policy-supported claims, not that every mentioned commitment is CONFIRMED; each promise state remains explicit. Missing authorized evidence must produce abstention/caveat, not a guessed source ID.

`POST /api/simulations`: auth role. Request `{promise_id,base_graph_revision,question,scenario_types:[AS_REQUESTED,RENEGOTIATE_DATE_OR_SCOPE,CHANGE_ORDER_OR_EXTRA_CAPACITY],assumptions:[{id,description,value?,unit?,evidence_ref_ids,kind:OBSERVED|USER_ASSUMPTION}],parent_scenario_id?}`. Backend validates assumptions, resolves full dependency snapshot, creates one Scenario per requested type. 201 `{request_id,scenario_ids,results:ScenarioResult[]}` or 202 operation reference. No action executes.

`GET /api/simulations/{scenario_id}` returns `{request_id,scenario:ScenarioResult}`. ScenarioResult: `{id,type,status,base_graph_revision,input_digest,inputs,overlay,assumptions[],feasibility:FEASIBLE|INFEASIBLE|UNKNOWN,conditional:boolean,schedule:[{issue_id,person_id,start,end,hours}],constraint_results:[{rule_id,outcome,reason,evidence_ref_ids}],calculations[],affected_entity_ids[],graph_paths[],missing_inputs[],auditor?,policy_checks[],candidate_actions:ActionProposalDTO[],computed_at,calculator_version}`. Schedule fields nullable for unknown outcomes; partial schedule explicitly identified. `inputs` is an ACL-safe captured snapshot, not mutable references to latest data.

Agent handoff/proposal DTOs are fully specified in [AGENT_DESIGN](AGENT_DESIGN.md). Only backend services create ActionProposalDTO after validating a scenario; no arbitrary action-create endpoint.

## 6. Actions, approval and execution

ActionProposalDTO: `{id,revision,scenario_id,action_type:WORKLOAD_UPDATE|JIRA_UPDATE|JIRA_CREATE|DRAFT_CUSTOMER_MESSAGE,target_system:WORKLOAD_MOCK|WORKLOAD_LIVE|JIRA|LOCAL_DRAFT,target_id,mode:MOCK|LIVE|DRAFT,before_state,before_state_hash,requested_changes,proposal_hash,dependency_digest,receipt_ids[],evidence_refs[],graph_paths[],impact:Calculation[],auditor_verdict,policy_checks[],required_approval_role:reviewer,status,idempotency_key,approval?,attempts[],external_response_reference?,read_back?}`.

Only WORKLOAD_UPDATE/WORKLOAD_MOCK is executable MVP scope. JIRA actions stay blocked unless a verified sandbox adapter/configuration is enabled; customer messages remain drafts, never sent. Real workload target fields are unspecified. Mock-only normalized change example: `{resource_id:"person-ben",task_id:"jira-acme-101",allocation_slots:[{start:"2026-10-16T09:00:00.000Z",end:"2026-10-16T14:00:00.000Z"}],cost_ceiling:{amount:"750",currency:"USD"}}`. These fields are owned by the mock adapter and do not imply a vendor API.

Hash binding: `proposal_hash` is SHA-256 of the canonical object containing exactly action ID, tenant ID, action type, target system/ID, mode, requested_changes, before_state_hash, dependency_digest, receipt IDs plus payload digests, scenario ID plus input_digest, auditor result digest and policy_version. Approval stores this immutable hash; changes create a new proposal. `before_state_hash` covers the normalized allowlisted target fields used for concurrency checks, with field-set version included. `dependency_digest` covers a sorted list of relevant entity revisions, source-version/hashes, receipt standing/content hashes, rate/calendar versions and policy_version. Transient action status/revision, approval IDs, trace timestamps and GraphState revision are excluded from proposal_hash to prevent approval creation invalidating its own binding; execution still rechecks current identity/ACL and approval expiry.

| Route | Request / authorization | Success / failure behavior |
|---|---|---|
| `POST /api/actions/{action_id}/request-approval` | Any authenticated role with scenario access; `{expected_revision,proposal_hash}` | `{request_id,action,approval}`; backend computes required approver, validates proposal; PROPOSED→NEEDS_APPROVAL or BLOCKED |
| `POST /api/actions/{action_id}/approve` | reviewer; `{expected_revision,proposal_hash,reason}` | `{request_id,action,approval,audit_event_id}`; NEEDS_APPROVAL→APPROVED only after all checks; expiry now+15 min default |
| `POST /api/actions/{action_id}/reject` | reviewer; `{expected_revision,reason}` | `{request_id,action,audit_event_id}`; NEEDS_APPROVAL/APPROVED→CANCELLED; in-flight cannot be assumed cancelled |
| `POST /api/actions/{action_id}/execute` | executor; `{expected_revision,proposal_hash}` | 202 `{request_id,action_id,status:EXECUTING,status_url}` after durable claim; otherwise 409/403; repeated dispatch prevented |
| `GET /api/actions/{action_id}` | Authorized read | `{request_id,action:ActionProposalDTO}`; read-back includes expected/actual fields, mismatches, checked_at and verified:boolean |

Action transition table:

| From | To | Authority / guard |
|---|---|---|
| PROPOSED | NEEDS_APPROVAL or BLOCKED | Deterministic proposal validation |
| NEEDS_APPROVAL | APPROVED, CANCELLED or BLOCKED | Reviewer or new evidence/policy failure |
| APPROVED | EXECUTING, CANCELLED or BLOCKED | Executor claim; reviewer rejection; expiry/input/target change blocks |
| EXECUTING | SUCCEEDED, FAILED or NEEDS_RECONCILIATION | Matching read-back; definitive no-effect failure; uncertain/mismatched/partial result |
| NEEDS_RECONCILIATION | SUCCEEDED or FAILED | Read-only reconciliation establishes actual state; otherwise stays pending |

BLOCKED/CANCELLED/FAILED/SUCCEEDED are terminal for that immutable requested change. Create a new proposal/reapproval for remediation; do not edit approved requested_changes. An executor cannot repair mismatch by issuing another write under the original approval. Non-idempotent create with uncertain result remains NEEDS_RECONCILIATION unless duplicate-safe lookup proves outcome.

## 7. Graph, trace, audit and extensions

Baseline routes:

- `GET /api/graph/{entity_id}?depth=1`: auth read, depth 1–3, optional `max_nodes` ≤ configured 60, `types` allowlisted; returns `{request_id,graph_revision,nodes:GraphNode[],edges:GraphEdge[],paths:GraphPath[],truncated:boolean,expansion_hints[]}`. IDs resolve in ACL; no arbitrary Cypher.
- `GET /api/trace/{request_id}`: auth read of own run or scoped admin; `{request_id,trace_request_id,graph_revision,steps:TraceStep[],source_refs[],limitations[]}`. Traces redact tool parameters/outputs using current ACL, not only historical ACL.
- `GET /api/audit/verify`: admin; optional bounded `from_sequence`,`to_sequence`; `{request_id,checked_range,chain_result:VALID|INVALID|INDETERMINATE,checks[],checkpoint:{available,trusted,sequence?},limitations[]}`. Unauthorized counts omitted.

EXTENSION routes needed for documented behaviors (not baseline claims):

| Route | Contract |
|---|---|
| `POST /api/session` | Local-demo-only bootstrap `{credential}` (secret, never logged); server config maps credential to actor/roles/tenant; secure HttpOnly SameSite cookie; `{request_id,actor:{id,roles},mode,expires_at}`. No shared admin API key in browser bundle. Production identity remains OPEN. |
| `GET /api/session` | Auth; `{request_id,actor:{id,roles},mode,expires_at}`; no credential returned |
| `POST /api/session/logout` | Auth+CSRF check; empty body; `{request_id,logged_out:true}` |
| `GET /api/operations/{operation_id}` | Auth requester/admin and underlying ACL; `{request_id,operation:Operation}` |
| `POST /api/operations/{operation_id}/cancel` | Requester/admin; `{expected_status,reason}`; `{request_id,operation}`; cancellation is best effort; external actions handled separately |
| `GET /api/actions` | Auth read; `status,cursor,limit` filters; collection of ActionProposalDTO for Approval Queue |
| `GET /api/connectors` | admin; collection `{id,type,mode,configured,health,checked_at,write_enabled,missing_configuration_keys[]}`; no secret values |
| `POST /api/receipts/verify` | Auth; `{receipt:ReceiptEnvelope}` ≤1 MiB, tenant/ACL refs must resolve; `{request_id,verification}`; no persistence/mutation; allows tampered-copy demo |
| `GET /api/keys/{key_id}` | Auth; `{request_id,issuer_id,key_id,algorithm:Ed25519,public_key_base64url,trust_status,valid_from,retired_at?}`; registry key lookup only; public key endpoint alone is not a trust anchor |
| `POST /api/promises/{promise_id}/receipts/{receipt_id}/revoke` | admin; `{expected_revision,reason}`; `{request_id,receipt_id,standing:REVOKED,audit_event_id}`; invalidates dependent proposals |
| `POST /api/sources/{source_id}/retire` | admin; `{expected_source_version_id,mode:RETIRE\|DELETE,reason}`; 202 operation; private-data deletion only under configured retention policy, downstream facts/approvals retired or blocked |
| `POST /api/conflicts/{conflict_id}/resolve` | reviewer plus admin for identity merge repair; `{decision:ACCEPT_ASSERTION\|KEEP_DISPUTED\|DISMISS,selected_evidence_ref_ids[],reason,expected_status:OPEN}`; `{request_id,conflict,audit_event_id}`; never rewrites source bytes |
| `POST /api/actions/{action_id}/reconcile` | executor; `{expected_revision,reason}`; 202 action status; **read-only provider call**, no replayed write |

No public graph editing, arbitrary source fetch, credential-setting endpoint, bot-joining endpoint, invoice/payment endpoint or workload-vendor proxy is proposed. Source raw-file export and configuration changes are not exposed in MVP; safe metadata/snippets suffice.

## 8. External API evidence and adapter boundaries

All citations checked 2026-10-12 via public documentation; no credentials used and no API invoked.

### Microsoft Graph transcript provider

VERIFIED-DOC routes under Microsoft Graph v1.0: `GET /users/{userId}/onlineMeetings/{meetingId}/transcripts` and `GET /users/{userId}/onlineMeetings/{meetingId}/transcripts/{transcriptId}/content`. List response has `value`; documented transcript metadata includes `id`, `meetingId`, `createdDateTime`, `transcriptContentUrl`. Use configured organizer/meeting identity and validated provider host; do not blindly fetch response URLs. Content format supports attributed VTT and a documented unattributed text format, subject to tenant controls. [List reference](https://learn.microsoft.com/en-us/graph/api/onlinemeeting-list-transcripts?view=graph-rest-1.0), [get/content reference](https://learn.microsoft.com/en-us/graph/api/calltranscript-get?view=graph-rest-1.0).

Application permissions/consent policy, meeting type and tenant settings require S04. No promised personal-account support. A missing speaker remains unresolved. Imported raw bytes plus normalized parse representation become source versions. Interface: `list_or_get_transcript(reference) → TranscriptDocument`, `normalize(document) → SourceDocument`, `healthcheck() → AdapterHealth`; these are internal method contracts, not additional vendor routes.

### Vexa provider

VERIFIED-DOC README lists `GET /transcripts/{platform}/{native_meeting_id}` and optional `POST /bots`. Exact pinned response fields, allowed platform values, auth header and availability/error states remain S04 verification tasks; no guessed response DTO is frozen here. Adapter uses configured ID/base URL, preserves raw bytes, and maps only verified fields. Bot participation requires separate explicit user/consent workflow outside MVP. [README](https://github.com/Vexa-ai/vexa/blob/main/README.md).

### Jira REST

VERIFIED-DOC search: `GET`/`POST /rest/api/3/search/jql`. Relevant documented request fields include `jql`, `fields`, `maxResults`, `nextPageToken`; response includes `issues` and `isLast`. Stop on isLast, missing continuation, page/item cap or repeated token; do not assume offset pagination. [Official issue-search reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/).

Search examples expose issue `id`, `key`, `fields.summary`, `fields.status`; project-specific estimates, due dates, assignees, issue-link semantics and custom fields require mapping validation. Issue read/create/edit docs could not be retrieved in this session: exact route/payload/permission/read-after-write semantics are **TO-BE-VERIFIED S05**. No undocumented If-Match/idempotency support is assumed. Interface retains baseline `search_issues`, `get_issue`, `create_issue`, `update_issue`, `read_back_issue`, `validate_config`, `healthcheck`, but write methods stay disabled pending sandbox contracts.

### Workload placeholder — explicitly not a real API

Live base URL, endpoints, methods, auth format, field names, employee IDs, statuses and error schema: **UNSPECIFIED**. There is no live request/response example. Placeholder adapter methods describe application responsibilities only:

| Internal method | Application-owned input/output |
|---|---|
| `get_workload_snapshot` | Resource IDs + window → normalized WorkloadSnapshot and exact provider evidence, or NOT_CONFIGURED |
| `propose_update` | Scenario allocation intent → validated ActionProposal target/before-state/changes; no external write |
| `execute_update` | Approved immutable action + attempt ID → safe dispatch outcome; implementation unavailable until mapping is supplied |
| `read_back_update` | Action target → normalized actual-state subset + evidence/version; no guessed vendor route |
| `healthcheck` | Configured mapping validation → mode/configuration/error status |

Required owner checklist: OpenAPI or equivalent contract; sandbox host; auth and scopes; allowed operations; person/task identity maps; hours versus capacity meaning; timezone/holidays/overlap semantics; immutable source/version identifiers; pagination/rate limits; conditional writes; idempotency; read-after-write latency; timeout/partial-failure behavior; rollback/compensation; data retention and test fixtures. Incomplete mapping yields `WORKLOAD_ADAPTER_NOT_CONFIGURED` and zero live writes. Mock state and normalized fields are explicitly owned by PromiseOps.

## 9. Contract freeze and compatibility

Illustrative application-owned request and expected response subset for the **after-clearance** fictional scenario (not a real API exchange):

```json
{
  "promise_id": "promise-loyalty",
  "base_graph_revision": 12,
  "question": "Compare Friday delivery with a supplied five-hour internal capacity option.",
  "scenario_types": ["AS_REQUESTED", "RENEGOTIATE_DATE_OR_SCOPE", "CHANGE_ORDER_OR_EXTRA_CAPACITY"],
  "assumptions": [
    {
      "id": "assumption-ben-option",
      "description": "Use the documented optional Ben capacity if the exact reservation is approved.",
      "value": "5",
      "unit": "hours",
      "evidence_ref_ids": ["evidence-capacity-option"],
      "kind": "USER_ASSUMPTION"
    }
  ]
}
```

Expected subset, deliberately not a full serialized ScenarioResult:

```json
{
  "type": "CHANGE_ORDER_OR_EXTRA_CAPACITY",
  "status": "COMPUTED",
  "feasibility": "FEASIBLE",
  "conditional": true,
  "calculations": [
    {
      "calculation_id": "calc-extra-spend",
      "formula_id": "F03",
      "formula_version": "1",
      "amount": "750",
      "currency": "USD",
      "status": "ESTIMATE",
      "inputs": [
        {"name": "extra_hours", "value": "5", "unit": "hours", "evidence_ref_ids": ["evidence-capacity-option"]},
        {"name": "approved_hourly_cost", "value": "150", "unit": "USD/hour", "evidence_ref_ids": ["evidence-rate-ben"]}
      ],
      "computed_at": "2026-10-16T09:00:00.000Z",
      "missing_inputs": []
    }
  ]
}
```

Fixture aliases/dates/revision are illustrative; generated run IDs/hashes must come from actual future computation. Full response must include all required ScenarioResult fields and explicitly retain unapproved customer change-order and missing acceptance caveats. This example creates no action approval or provider call.

Later phase 0 produces Pydantic and matching TypeScript models from these definitions, resolves every optional field and verifies serialization against golden examples. Changes require decision/changelog/traceability updates before UI and backend diverge. Contract tests include all route success/auth/schema/stale/retry cases, accessible evidence, idempotency collisions and prohibited tenant/URL fields. This phase provides no executable OpenAPI, model files or endpoint implementation.
