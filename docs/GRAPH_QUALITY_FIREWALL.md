# Graph quality firewall

Status: proposed control specification. All graph writes, including structured imports, reviewed repairs and agent candidates, pass the same ontology/identity/provenance boundary. No model has a direct write tool.

## 1. Validation order and outcomes

| Rule | Deterministic check | Failure outcome / test |
|---|---|---|
| G01 TENANT_ACL | Nodes, endpoints, refs and source access within authenticated tenant and authorized scope | Reject batch; critical finding; T17 |
| G02 ONTOLOGY | Closed labels, property types/enums and exact relation endpoint matrix | Reject candidate; record proposed type, never create it; T12 |
| G03 RELATION_NORMALIZATION | Map known extraction aliases to canonical types; direction explicit | Unknown alias quarantined; no dynamic vocabulary; T12 |
| G04 IDENTITY | Exact external ID or reviewed alias; unique context match only | Quarantine identity-dependent edges; keep source label; T30 |
| G05 EVIDENCE | Retained raw/parse hashes, exact quote span or structured pointer | Reject unsupported fact; REJECTED_QUOTE finding; T02 |
| G06 DUPLICATE | Assertion key, external identity, overlapping chunks and semantic candidate keys | Suppress exact duplicate; ambiguous near-duplicate to review; T13 |
| G07 ORPHAN | All scalar IDs/refs resolve; semantic entity has evidence and required associations | Quarantine missing-reference fact; flag existing logical orphan; T12 |
| G08 CONFLICT | Multiple active incompatible owner/date/value/status/scope assertions | Preserve both with Conflict OPEN; block definitive conclusion/action; T03/T29 |
| G09 GROWTH | Distinct types subset of ontology; per-source entity/edge/fanout bounds | Stop publication for anomalous batch, retain manifest; T12 |
| G10 TEMPORAL | Ordered versions, active intervals, freshness, predecessor chain | Reject cycles/forks, stale label, invalidate dependencies; T08/T29 |
| G11 DEPENDENCY | No self/cyclic task dependence; capped traversal explicitly reports truncation | Scenario invalid/unknown, not assumed feasible; T05 |
| G12 SIGNED_STATE | Payload/projection equality; review/audit state consistent | Critical integrity finding; block dependent action; T07/T08 |

Normalization table (proposal, fixed at ontology v1): “assigned to”/“assignee” → ASSIGNED_TO with JiraIssue→Person; “requires task”/“depends on” → DEPENDS_ON with dependent→prerequisite; “blocks” → DEPENDS_ON with reversed endpoints; “mentioned” → MENTIONED_IN. Normalization is not permission to invent endpoints. An ambiguous natural-language relationship becomes a candidate for review. No automatic generic RELATED_TO edge is allowed.

FalkorDB relationships inherently have endpoints; “dangling edge” here includes invalid application references and missing provenance, not a claim that the engine routinely stores physically endpoint-less edges. An orphan Person without a meeting/task/team may be an intentional unresolved import, flagged with reason rather than deleted automatically.

## 2. Duplicate and conflict semantics

Exact source/version/hash reimport is NO_CHANGE. Exact external IDs resolve to one entity. Different provider IDs with similar names are separate until reviewed. Same issue key from different Jira sites is not a duplicate. Parallel evidence assertions are not duplicate tasks; query/calculator deduplicates entity IDs. Do not destroy independent corroboration when consolidating display edges.

Single-valued conflict records contain candidate values and all immutable evidence refs, first-detected time, severity and affected entity/relationship. Semantic disagreement about scope is not resolved by model confidence or newest timestamp. Conflicting commercial values stay UNKNOWN for calculations unless an authorized selection with authority/source basis is recorded. Contradictory transcript quotes can both be valid evidence.

## 3. Proposed growth limits

Per source-run: ≤200 chunks, ≤500 candidate entities, ≤2,000 assertion edges, ≤100 outgoing semantic assertions for a single new subject; exact thresholds configurable. Any nonallowlisted relationship count must be zero. A >2× source assertion count versus its predecessor is a warning requiring admin review before publication when the increase exceeds 100 assertions. A first import uses absolute limits. These defaults are design assumptions, not FalkorDB performance limits or a measured anomaly detector.

Record rejected count, accepted count, new relation vocabulary count, evidence coverage, unresolved identities, orphan references, conflicts, source age and per-stage latency. Knowledge Health exposes only caller-authorized records and counts. Never store rejected raw model output with secrets/unbounded source contents in ordinary logs.

## 4. Quarantine and safe repair

Quarantine stores bounded candidate JSON in OperationRun and finding details; it creates no active business edge. A partial source import can publish independent verified candidates, but not half a promise/evidence unit. Source-wide hash/parser/tenant failure prevents publication entirely.

Admin/reviewer repair flow: inspect original source and candidate → choose corrected mapping/identity/assertion with reason → preview affected nodes/receipts/actions and permission impact → run firewall again → publish a new audited correction under expected graph revision. Identity merges require admin plus reviewer capability; select surviving ID, retain alias/tombstone and redirect references through a recorded migration. Never rewrite past receipt payload IDs; historical aliases remain resolvable for verification. Destructive bulk cleanup is not an agent tool and requires a separately scoped plan, backup and owner authorization.

Rollback uses compensating graph events and prior version selection; it does not remove audit history. A repair affecting signed evidence creates a new receipt and invalidates pending approval. A repair cannot transform a service signature into human agreement.

## 5. SDK issue evidence and its limits

Public discussions inspected 2026-10-12: [GraphRAG-SDK #285](https://github.com/FalkorDB/GraphRAG-SDK/issues/285) reports excessive relationship vocabulary under open-schema extraction; [#284](https://github.com/FalkorDB/GraphRAG-SDK/issues/284) discusses concurrent incremental updates; [#283](https://github.com/FalkorDB/GraphRAG-SDK/issues/283) discusses bulk relationship write round trips. Pages were shown open in the retrieved view where status was available; cached views and future changes limit this observation. No reproduction or deployed-version confirmation was performed.

These are SDK-level reports and design motivation for bounded, controlled writes. They are not evidence here of an active core FalkorDB defect. The graph firewall is required by PromiseOps' ontology and evidence rules independently of those reports. SDK ingestion is excluded from the MVP live graph.

## 6. Acceptance checklist

T12 must reject unknown label/type/property, inverted endpoint, invalid span, unsupported provenance, cross-tenant reference, dangling scalar reference and pathological batch growth. T13 proves idempotent reimport and independent-source retirement. T30 proves ambiguous identities are not merged and historical expertise does not confer authority. T29 proves conflict/staleness invalidates execution. Tests must inspect the real graph after rejection: finding/run records may increase, active business facts must not.
