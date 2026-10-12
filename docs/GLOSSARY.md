# Glossary and canonical vocabulary

Status: proposed normative terminology, 2026-10-12. State namespaces are distinct even where they reuse a word.

| Term | Definition |
|---|---|
| PromiseOps | Business application connecting commitments, delivery risk and commit-to-cash evidence. |
| PromiseSeal | Custom v1 receipt protocol and verification behavior inside PromiseOps; not a separate blockchain, legal signature system or VC implementation. |
| Promise / commitment | A stable business undertaking identity (`Promise`) with versioned interpretations. Extraction is a candidate, not proof of agreement. |
| Claim | A specific assertion in an answer, extracted fact or receipt. A claim carries supporting/contradicting evidence and classification. |
| Evidence | Exact retained source-version content and location, or a structured source field pointer, validated by deterministic checks. Evidence can support a false or disputed assertion. |
| SourceRecord | Stable identity of an imported external object or upload. Holds current-version projection, not historical bytes. |
| SourceVersion | Immutable metadata for one exact byte representation and its parse representation, hashes and ACL. |
| SourceChunk | Immutable bounded substring of the parse representation with offsets and optional cue timestamps. |
| Receipt / PromiseVersion | One canonical payload version; receipt_id equals PromiseVersion.id. Signature envelope and fresh verification are separate. |
| Service attestation | The platform key signed these payload bytes. Does not prove the attributed person signed, agreed, or had commercial authority. |
| Confirmation | Authenticated reviewer event confirming a specified interpretation for operational use. Not customer acceptance or contract amendment. |
| Dispute | Recorded challenge to a particular interpretation with reason/evidence. Blocks dependent execution until resolved. |
| Supersession | A newer receipt version replaces an older version for current use; old bytes and issuance status are retained. |
| Revocation | Issuer withdrawal of a receipt's standing via a signed audit event; signature mathematics may still verify. |
| Scope gap | Possible mismatch between proposed work and source-supported scope. Missing contract evidence is insufficient evidence, not a scope gap finding. |
| Exposure | Separately presented cost estimate, milestone amount at risk, or renewal context. Not an automatic loss or sum. |
| Commit-to-cash | Trace from undertaking through execution and required acceptance evidence to milestone readiness; no invoice submission/payment in MVP. |
| Scenario | Isolated hypothetical overlay on a captured graph/input revision; does not change live business state. |
| Feasibility | Deterministic ability to schedule modeled work under explicit inputs/constraints. Conditional assumptions are displayed; unknown inputs prevent a definitive result. |
| ActionProposal | Version-bound intent to change one allowlisted target after policy and human approval. |
| Approval | Server-validated human authorization bound to an exact proposal, before state, dependencies and expiry. |
| Verified action | Execution with successful field-by-field read-back against expected state. HTTP success alone is insufficient. |
| Graph provenance | Relationship origin, source version, quote/pointer, validation, authoring mechanism, time and audit linkage. |
| Evidence quality | Deterministic assessment of completeness, freshness and conflicts; independent of extraction-model confidence. |
| Confidence | Model-provided triage estimate only; never permission, identity proof or probability of business loss. |
| Snapshot | Explicit captured inputs/revision used by a calculation; not an assumed database point-in-time capability. |
| Freshness | Age/availability of a source version relevant to the operation, using source update/as-of time rather than recent reimport time. |
| Quarantine | Nonpublishable candidate records retained in an OperationRun/KnowledgeFinding, outside active business edges. |
| Audit event | Append-only-by-policy record of a transition/attempt with hash linkage and service signature. Not immutable against full administrator compromise. |
| Mock mode | Application-owned deterministic connector with synthetic state. Never presented as a real workload integration. |
| Replay | Previously captured result displayed with provenance/time and a REPLAY label. Does not prove a current live execution. |

## State namespaces

- Business lifecycle: `PROPOSED`, `NEEDS_REVIEW`, `CONFIRMED`, `DISPUTED`, `FULFILLED`, `REJECTED`. Older versions also expose effective `SUPERSEDED`.
- Receipt standing: `ACTIVE`, `SUPERSEDED`, `REVOKED`. Receipt integrity: `VALID`, `INVALID`, `UNSIGNED`, `INDETERMINATE`. Source verification component: `MATCH`, `MISMATCH`, `UNAVAILABLE`.
- Scope: `POSSIBLE_IN_SCOPE`, `POSSIBLE_OUT_OF_SCOPE`, `CONFLICT`, `INSUFFICIENT_EVIDENCE`, `NEEDS_LEGAL_REVIEW`.
- Action: `PROPOSED`, `NEEDS_APPROVAL`, `APPROVED`, `EXECUTING`, `SUCCEEDED`, `FAILED`, `BLOCKED`, `CANCELLED`, `NEEDS_RECONCILIATION`.
- OperationRun: `QUEUED`, `RUNNING`, `SUCCEEDED`, `PARTIAL`, `FAILED`, `CANCELLED`.
- Scenario computation: `DRAFT`, `COMPUTED`, `INVALID`, `STALE`. Feasibility: `FEASIBLE`, `INFEASIBLE`, `UNKNOWN`; assumptions may make feasibility conditional.
- Fact validity: `ACTIVE`, `RETIRED`, `QUARANTINED`. Conflict: `OPEN`, `RESOLVED`, `DISMISSED`. Finding: `OPEN`, `ACKNOWLEDGED`, `RESOLVED`.
- Calculation: `ESTIMATE`, `AT_RISK`, `CONFIRMED`, `UNKNOWN`. Auditor: `PASS`, `NEEDS_REVIEW`, `BLOCK`.

Canonical field names, transitions and case are defined in [API_CONTRACTS](API_CONTRACTS.md), [PROMISESEAL_PROTOCOL](PROMISESEAL_PROTOCOL.md), and [FALKORDB_SCHEMA](FALKORDB_SCHEMA.md). Do not use `verified`, `confirmed`, or `approved` as interchangeable UI badges.
