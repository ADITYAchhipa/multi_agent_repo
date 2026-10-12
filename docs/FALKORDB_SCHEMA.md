# FalkorDB schema and query contract

Status: proposed ontology v1. No graph exists and no Cypher below has been executed. Baseline §5; explicit refinements D03, D08, D09, D12. This is the authoritative label/relationship catalogue for the blueprint.

## 1. IDs, types and storage rules

Every node requires `id:string`, `tenant_id:string`, `created_at:UTC timestamp`, `updated_at:UTC timestamp`, `access_label:PUBLIC_DEMO|INTERNAL|RESTRICTED`, `acl_principals_json:string` (canonical JSON array of authorized actor/group IDs; `[]` means label policy only). Tenant comes only from authenticated server context. Read filters apply to every path element. `PUBLIC_DEMO` is still authenticated and tenant-scoped in MVP; it is not internet-public.

App IDs are opaque UUIDs except fixed synthetic fixture aliases. Never expose FalkorDB internal node/edge IDs as durable IDs. External keys are separate properties. Unique business key is `(tenant_id, label, id)`; source external key is `(tenant_id, connector_id, external_id)`. Jira stable identity uses site ID plus **issue ID** when available, preserving issue key as mutable display alias; a key-only export must mark identity provisional and reconcile before live sync. This refines the baseline example of site/project/key to survive issue moves.

Use UTC RFC3339 strings with fixed millisecond precision for application timestamps, e.g. `2026-10-12T09:00:00.000Z`. Preserve source timezone/precision separately. Dates are `YYYY-MM-DD`; “Friday” is not silently promoted to an instant. Decimal money/hours properties are decimal **strings**, converted to Decimal in deterministic backend calculations; do not use graph floating-point arithmetic for finances. Integer version/sequence/offset fields are nonnegative and bounded. Unknown optional graph properties are absent (API returns null); empty string/zero never stands for unknown.

Nested objects are canonical JSON string properties (`*_json`), not assumed native nested maps. Index only scalar properties. Immutable nodes preserve payload fields; only explicitly identified projection/standing/retention metadata can change. `last_verified_at` is optional on mutable entities, never proof that the source is fresh.

## 2. Node dictionary

R = required in addition to common fields; O = optional. An `R?` value is a required API key whose value may be null, represented absent in graph storage. Enumerations are closed; other fields reject unknown keys at write-service boundary.

| Label | Required properties | Optional / nullable properties and invariants |
|---|---|---|
| Customer | `name`, `status:ACTIVE\|INACTIVE` | `industry`, `aliases_json`, `renewal_context_json` with source/amount/currency; not a loss estimate |
| Person | `name`, `active:boolean`, `identity_status:RESOLVED\|AMBIGUOUS`, `external_ids_json` | `email`, `role`, `team_id`, `aliases_json`; human speaker identity is distinct from auth actor binding |
| Team | `name` | `external_id`; Person.team_id must resolve in tenant |
| Meeting | `title`, `platform:FILE\|TEAMS\|VEXA\|OTHER`, `source_id` | `start_at`, `end_at`, `timezone`, `external_meeting_id`; missing time leaves relative dates unresolved |
| SourceRecord | `source_type`, `title`, `connector_id`, `external_id`, `retention_state:ACTIVE\|RETIRED\|DELETED`, `parse_status` | `current_version_id`, `uri_or_path`, `content_hash`, `content_hash_algorithm`, `source_updated_at`, `ingested_at`, `content_type`; latter fields are latest projections only |
| SourceVersion | `source_id`, `version:int>=1`, `content_hash`, `content_hash_algorithm:SHA-256`, `representation_hash`, `representation_version`, `parser_version`, `content_type`, `ingested_at`, `original_artifact_id`, `representation_artifact_id`, `parse_status:STORED\|PARSED\|PUBLISHED\|FAILED`, `availability:AVAILABLE\|DELETED\|MISSING` | `source_updated_at`, `observed_at`, `predecessor_version_id`, `normalization_map_artifact_id`; raw payload immutable, availability metadata mutable |
| SourceChunk | `source_id`, `source_version_id`, `text`, `start_offset:int`, `end_offset:int`, `chunk_hash` | `start_ms`, `end_ms`, `speaker_label`, `speaker_id`; offsets are Unicode scalar indices in parse representation, half-open |
| Contract | `customer_id`, `name`, `status:DRAFT\|SIGNED\|EXPIRED\|RETIRED`, `source_id`, `source_version_id` | `effective_from`, `effective_to`; signed status is a source assertion, not cryptographic validation of a contract |
| ContractClause | `contract_id`, `clause_ref`, `text_excerpt`, `clause_type:SCOPE\|EXCLUSION\|CHANGE_CONTROL\|ACCEPTANCE\|PAYMENT\|OTHER`, `source_id`, `source_version_id`, `source_hash`, `evidence_ref_json` | `supersedes_clause_id`; clause text immutable per source revision |
| Promise | `current_version_id`, `current_state`, `revision:int` | `customer_id`, `project_id`; both nullable for unresolved extraction; projections only |
| PromiseVersion | `promise_id`, `version`, `payload_json`, `payload_hash`, `canonicalization`, `statement`, `deliverable`, `commitment_class`, `status_at_issuance`, `receipt_standing:ACTIVE\|SUPERSEDED\|REVOKED` | `deadline_iso`, `deadline_text`, `price_condition`, `amount`, `currency`, `signature`, `key_id`, `issued_at`, `supersedes_version_id`; payload_json normative, duplicated fields checked against payload |
| Project | `customer_id`, `name`, `status:PLANNED\|ACTIVE\|DONE\|CANCELLED` | `planned_start`, `planned_end`, `source_id`, `source_version_id` |
| JiraIssue | `external_id`, `site_id`, `issue_key`, `summary`, `status`, `source_id`, `source_version_id`, `source_updated_at`, `revision:int` | `description_excerpt`, `priority`, `assignee_id`, `estimate_hours`, `due_at`, `external_url`, `project_id`, `completion_state:TODO\|IN_PROGRESS\|DONE\|UNKNOWN`; native status mapping is configured |
| WorkloadSnapshot | `person_id`, `as_of`, `window_start`, `window_end`, `available_hours`, `committed_hours`, `unit:hours`, `calendar_json`, `source_id`, `source_version_id`, `mode:MOCK\|LIVE\|IMPORT` | `provider_revision`; available means **free capacity after committed work**, never subtract commitments twice; immutable |
| RateCard | `role_or_resource_key`, `hourly_cost`, `currency`, `effective_from`, `source_id`, `source_version_id`, `approval_status:APPROVED\|PROPOSED\|RETIRED` | `effective_to`; overlaps cause conflict; rates nonnegative |
| InvoiceMilestone | `customer_id`, `contract_id`, `project_id`, `amount`, `currency`, `condition_text`, `status:NOT_READY\|READY\|INVOICED\|UNKNOWN`, `source_id`, `source_version_id` | `target_date`; READY requires all REQUIRES checks; AT_RISK is separate calculated exposure |
| AcceptanceRequirement | `milestone_id`, `kind:TASK_DONE\|DOCUMENT`, `description`, `status:MISSING\|PRESENT\|VERIFIED\|DISPUTED`, `evidence_refs_json`, `source_id`, `source_version_id` | `required_task_id`, `accepted_by_actor_id`, `accepted_at`; absence modeled explicitly, never an invented document |
| ChangeOrder | `customer_id`, `contract_id`, `status:PROPOSED\|APPROVED\|REJECTED\|SUPERSEDED`, `currency`, `source_id`, `source_version_id` | `proposed_amount`, `proposed_due_at`, `approved_at`; APPROVED needs imported authoritative evidence and authorized review |
| Scenario | `created_by`, `question`, `status`, `scenario_type`, `assumptions_json`, `overlay_json`, `inputs_json`, `results_json`, `graph_snapshot_as_of`, `graph_revision`, `input_digest`, `calculator_version`, `policy_version` | `parent_scenario_id`; result immutable after COMPUTED, status may become STALE |
| ActionProposal | `scenario_id`, `action_type`, `target_system`, `target_id`, `mode`, `changes_json`, `before_state_json`, `before_state_hash`, `dependency_digest`, `proposal_hash`, `evidence_refs_json`, `receipt_ids_json`, `policy_result_json`, `policy_version`, `status`, `revision`, `idempotency_key` | `approval_id`, `approved_until`, `attempt_id`, `external_result_json`, `read_back_json`; action state rules in API |
| Approval | `action_id`, `requested_by`, `decision:PENDING\|APPROVED\|REJECTED\|EXPIRED\|INVALIDATED`, `proposal_hash`, `required_role:reviewer` | `reviewed_by`, `reason`, `decided_at`, `expires_at`; bind exact dependencies/target state through proposal_hash |
| AuditEvent | `event_type`, `actor_id`, `occurred_at`, `sequence`, `payload_json`, `prev_event_hash`, `event_hash`, `signature`, `key_id`, `canonicalization` | `request_id`, `action_id`, `promise_id`; signed chain details in protocol; tenant genesis has null previous hash |
| Conflict | `entity_id`, `relationship_type`, `candidate_values_json`, `source_refs_json`, `status`, `detected_at` | `resolved_by`, `resolution_event_id`; never delete disagreeing source evidence on resolution |
| KnowledgeFinding | `finding_type`, `severity:INFO\|WARNING\|CRITICAL`, `source_refs_json`, `details_json`, `status` | `entity_id`, `resolved_at`, `resolution_event_id`; details may contain quarantined candidate refs, not active edges |
| OperationRun | `kind:INGESTION\|CONNECTOR_SYNC\|ANALYSIS\|REPROCESS\|REPAIR\|RETIREMENT`, `status`, `phase`, `requested_by`, `request_id`, `input_digest`, `input_json`, `result_json`, `errors_json`, `attempt_count` | `started_at`, `finished_at`, `cancel_requested_at`; bounded durable work record, not a general queue framework |
| GraphState | `revision`, `ontology_version`, `policy_version`, `audit_head_hash`, `audit_sequence` | Exactly one id `graph-state` per tenant; server-owned projections updated under single writer |

Source types: `TRANSCRIPT`, `NOTES`, `CONTRACT`, `JIRA_EXPORT`, `WORKLOAD_EXPORT`, `RATE_CARD`, `ACCEPTANCE`, `CHANGE_ORDER`, `INCIDENT`, `CONFIG`. Receipt commitment classes are `explicit`, `conditional`, `suggestion`, `hypothetical`, `ambiguous`; price conditions `NO_ADDITIONAL_CHARGE`, `CHANGE_ORDER_REQUIRED`, `PRICED`, `UNKNOWN` preserve original wording in payload.

Receipt projection mapping is exact: API `receipt_id`→PromiseVersion.id; `payload_sha256`→payload_hash; `signature_base64url`→signature; payload.signing_key_id→key_id; payload.deadline.instant→deadline_iso; payload.deadline.original_text→deadline_text; payload.commercial_value.amount/currency→amount/currency; payload.price_condition.kind→price_condition. AuditRecord.signature_base64url maps to AuditEvent.signature. SourceVersion.content_hash is API EvidenceRef.source_hash. Graph storage names preserve baseline names; DTO mapping is explicit and tested, not separate competing fields.

## 3. Closed relationship endpoint matrix

Each row is a permitted type and exact endpoint set; alternatives are explicit unions, not wildcard entity labels. No other type is allowed. Stored direction is authoritative. Structural edges need creation event, semantic edges need source evidence.

| Type | From → to | Meaning / extra invariant |
|---|---|---|
| HAS_CONTRACT | Customer → Contract | Customer association |
| HAS_CLAUSE | Contract → ContractClause | Versioned source clause |
| FOR_CUSTOMER | Project → Customer | No mirror customer-project edge |
| PARTICIPATED_IN | Person → Meeting | Requires supported identity |
| HAS_SOURCE | Meeting, Contract, Project, JiraIssue, PromiseVersion, ChangeOrder → SourceRecord | Logical source association; immutable evidence uses version refs |
| HAS_SOURCE_VERSION | SourceRecord → SourceVersion | Added source-history edge, ordered by version |
| HAS_CHUNK | SourceVersion → SourceChunk | Refines baseline SourceRecord→Chunk to immutable owner |
| MENTIONED_IN | Customer, Person, Project, JiraIssue, Contract, PromiseVersion → SourceChunk | Mention only, not endorsement |
| SPOKEN_BY | SourceChunk → Person | Resolved identity only; otherwise label remains property |
| PROPOSES | SourceChunk → PromiseVersion | Candidate extraction |
| HAS_VERSION | Promise → PromiseVersion | Same promise and tenant; unique version integer |
| SUPERSEDES | PromiseVersion → PromiseVersion | Newer to immediate older, same promise, version +1 |
| ASSERTED_BY | PromiseVersion → SourceRecord | Attribution to source; use SPOKEN_BY for human speaker |
| ABOUT_CUSTOMER | PromiseVersion → Customer | Optional until resolution |
| ABOUT_PROJECT | PromiseVersion → Project | Optional until resolution |
| SUPPORTED_BY | PromiseVersion → SourceChunk, ContractClause, SourceVersion | Evidence association; does not assert correctness |
| POSSIBLY_COVERED_BY | PromiseVersion → ContractClause | Scope assessment with classification and finding ref |
| CONFLICTS_WITH | PromiseVersion, ContractClause → PromiseVersion, ContractClause, SourceChunk | Canonical Conflict node ID required; avoid reciprocal duplicate |
| TRACKED_BY | PromiseVersion → JiraIssue | Related tracking record; not necessarily implementation |
| IMPLEMENTED_BY | PromiseVersion → JiraIssue | Work item explicitly maps to deliverable |
| ASSIGNED_TO | JiraIssue → Person | At most one active resolved assignee per snapshot |
| DEPENDS_ON | JiraIssue → JiraIssue | Dependent → prerequisite; disallow self/cycle; no BLOCKS edge |
| HAS_WORKLOAD | Person → WorkloadSnapshot | Snapshot for that person |
| USES_RATE | Person → RateCard | Effective approved resource rate; role mapping resolved by service |
| HAS_MILESTONE | Contract, Project → InvoiceMilestone | Both associations allowed, count milestone ID once |
| REQUIRES | InvoiceMilestone → JiraIssue, AcceptanceRequirement | All requirements conjunctive in MVP |
| SATISFIED_BY | AcceptanceRequirement → SourceVersion | Evidence artifact satisfying requirement; added edge |
| AFFECTS | JiraIssue, PromiseVersion → InvoiceMilestone, Project, Customer | Evidence-backed impact, no inferred causality without qualifier |
| HAS_CHANGE_ORDER | Contract → ChangeOrder | Change-order association |
| APPROVED_BY | ChangeOrder, ActionProposal → Person | Auth actor explicitly bound to Person and approval evidence |
| HAS_ACTION | Scenario → ActionProposal | Proposal from scenario |
| EVIDENCED_BY | ActionProposal → SourceChunk, SourceVersion, PromiseVersion, JiraIssue, ContractClause | Exact inputs backing action |
| HAS_APPROVAL | ActionProposal → Approval | Human review record |
| HAS_EVENT | Promise, PromiseVersion, ActionProposal, Conflict, SourceRecord, OperationRun, GraphState → AuditEvent | Event ownership; event can have multiple owners but one tenant sequence |
| HAS_FINDING | SourceRecord, SourceVersion, SourceChunk, Person, Customer, Project, JiraIssue, Contract, ContractClause, Promise, PromiseVersion, Scenario, ActionProposal, InvoiceMilestone, AcceptanceRequirement, OperationRun → KnowledgeFinding | Source/subject of quality finding |

No relationship target `Task` exists. `SourceRecord→HAS_CHUNK` and `SUPPORTED_BY→SourceRecord` from baseline are refined to source-version paths; the stable source is still reachable. All deviations must be implemented as one ontology version, not mixed aliases.

## 4. Edge provenance and temporal semantics

Every stored edge requires `id`, `tenant_id`, `created_at`, `status:ACTIVE|RETIRED`, `valid_from`, optional `valid_to`, `recorded_at`, `provenance_kind:EXTRACTED|STRUCTURED|REVIEW|STRUCTURAL|CALCULATED`, `provenance_json`, `access_label`, `acl_principals_json`. `provenance_json` is an array of EvidenceRef or audit-event refs. Extracted edges additionally require `source_id`, `source_version_id`, `source_hash`, `evidence_quote`, offsets, `extracted_at`, model ID and confidence; source_updated_at is retained when supplied, otherwise absent with freshness UNKNOWN. Structured edges carry exact JSON pointer/CSV cell refs and source version; semantic interpretations never inherit confidence 1.0 from their structured input.

Edge ID is deterministic from tenant, type, endpoints, source-version assertion key and qualifier. Reimport same source version yields same ID. Distinct sources supporting a relation may create separate assertion edges; business path results deduplicate endpoint/type while returning **all** supporting assertion IDs. Retirement removes only the relevant assertion; corroborating sources remain active. Financial/scheduling joins deduplicate JiraIssue and milestone IDs before counting. Never rely on count of parallel edges as count of work.

`valid_from/valid_to` express asserted business validity; `recorded_at` expresses ingestion time. Unknown business date uses observed time with `validity_basis:OBSERVED`, not a fabricated effective date. Historical receipt verification follows its exact version refs, not active-edge filters. Normal reasoning uses active, authorized facts at captured revision. Conflicts retain both assertions and block definitive single-valued conclusions.

## 5. Invariants, isolation and concurrency

All writes enforce: one tenant per node/edge/path; mandatory properties; allowed endpoints; source availability and verified evidence; unique stable keys; no dangling scalar references; monotonic source/promise versions; no supersession cycles; one active current receipt; no new confirmation without review event; revoked receipt cannot support execution; approval binds existing proposal hash; signed payload never changed in place.

Application serialized writes and conditional revision checks are mandatory even if database constraints are available. On startup verify the expected graph schema, indexes and ontology version; do not accept a graph name from HTTP or the model. Index is not uniqueness. S01 must test native uniqueness/mandatory constraints and transactional behavior before relying on them; deploy fails closed if required atomic publication cannot be proven. Multi-worker writes are out of MVP scope.

Tenant graph mapping plus tenant predicates provide defense in depth, not a claim that a graph name is an authorization system. All scalar ID references and JSON evidence refs are resolved through the same tenant/ACL service. Cross-tenant IDs produce 404 and no count/trace leak.

## 6. Indexes and feature verification

**VERIFIED-DOC, 2026-10-12:** official documentation describes read-only `GRAPH.RO_QUERY` and indexing facilities. Read-only query rejects write attempts; indexing documentation covers scalar indexes and lists full-text/vector options. These are documentation facts, not proof that every release/image supports each feature. [Read-only command](https://docs.falkordb.com/commands/graph.ro-query), [index overview](https://docs.falkordb.com/cypher/indexing).

Proposed indexes: `id` on every label; SourceRecord external lookup key; SourceVersion source_id/content_hash; Promise current_state; PromiseVersion promise_id; JiraIssue external_id/issue_key; Person normalized exact identity keys; AuditEvent sequence; OperationRun status/request_id; ActionProposal status/idempotency_key. Application can persist a canonical composite key string where composite index support is not established. Validate index creation/listing/query plans with the pinned engine. No runtime LLM-created indexes.

Full-text names/aliases is optional. Fallback is bounded indexed exact keys plus normalized aliases; do not add another database. Vectors are stretch and require their own dimensions/model/version policy. Native transaction/constraint/backup/copy features and exact DDL syntax are **OPEN S01**. Current docs may describe different 4.x and 6.x features; pin image digest and test. No graph clone is required for MVP scenarios.

## 7. Query catalogue and illustrative Cypher

Every template has fixed labels/relations, typed parameters, timeout, authorized property projection and row/node cap. Default depth 1, max 3 for user graph expand; named business paths may have fixed longer length (e.g. 6 edges) and capped rows. User input cannot alter query grammar. Read queries use client `ro_query` after verifying parameter behavior.

| ID | Purpose / inputs | Output and gate |
|---|---|---|
| Q01 promise_context | promise_id, current_version_id, tenant | Receipt + exact sources/clauses/tasks; current revision |
| Q02 scope_evidence | customer/project/receipt IDs | Signed contract clauses, approved changes, conflicts; no legal verdict from query alone |
| Q03 delivery_dependencies | issue_ids | Distinct tasks and prerequisite edges; cycle/max-depth indicator |
| Q04 resource_capacity | person_ids, window | Latest eligible snapshots and effective rates; ambiguity flag |
| Q05 commercial_impact | task/receipt IDs | Distinct milestones, requirement state, separate renewal context |
| Q06 source_impact | source_version_id | Affected receipts, scenarios and proposals for invalidation |
| Q07 version_history | promise_id | Ordered versions/events; chain continuity |
| Q08 knowledge_health | bounded filters | Authorized counts/findings/staleness and logical orphan IDs |
| Q09 graph_expand | entity_id, fixed template depth | ≤60 nodes by default; explicit truncation; all edge provenance |
| Q10 trace_lookup | request_id | Stored backend steps, result IDs/timings; no reasoning narrative invented by model |

Illustrative query fragment only; not production-ready, not executed. Full implementation must add active-fact, ACL, source-availability and temporal predicates and ensure all returned endpoints share tenant. Client parameter binding syntax must pass S01.

```cypher
MATCH (p:Promise {id: $promise_id, tenant_id: $tenant_id})
      -[:HAS_VERSION]->(v:PromiseVersion)
WHERE v.id = p.current_version_id AND v.tenant_id = $tenant_id
MATCH (v)-[i:IMPLEMENTED_BY]->(j:JiraIssue)
WHERE i.tenant_id = $tenant_id AND i.status = 'ACTIVE'
  AND j.tenant_id = $tenant_id
RETURN p.id, v.id, j.id, i.id, i.provenance_json
LIMIT 60
```

Illustrative dependency direction: integration depends on credentials, not the reverse.

```cypher
MATCH (j:JiraIssue {id: $issue_id, tenant_id: $tenant_id})
      -[d:DEPENDS_ON]->(prerequisite:JiraIssue)
WHERE d.status = 'ACTIVE' AND d.tenant_id = $tenant_id
  AND prerequisite.tenant_id = $tenant_id
RETURN j.id, d.id, prerequisite.id, d.provenance_json
LIMIT 60
```

Index example is a **version-specific spike candidate**, not a verified deployment instruction:

```cypher
CREATE INDEX FOR (p:Promise) ON (p.id)
```

A judge must be able to correlate template ID, safe bound values, result node/edge IDs, evidence refs and displayed path. Query logs must not disclose hidden-source text or credentials. See T05/T12/T17/T25 in the test plan.
