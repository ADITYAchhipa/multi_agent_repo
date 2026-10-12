# Decisions, discrepancies and open questions

Status: documentation decisions, 2026-10-12. No implementation has started. The master remains unchanged. Entries below are explicit elaborations or corrections; they do not imply owner approval of real business policy.

## Decision log

| ID | Decision and rationale | Baseline reference / consequence |
|---|---|---|
| D01 | Documentation-only instruction governs this phase. Preserve all original inputs. | Overrides master §0, §14–18 and final instruction to create/run code. |
| D02 | Keep Next.js/React/TypeScript UI; FastAPI/Pydantic 2/Python backend; FalkorDB only application database; local source artifacts. Bounded orchestrator, no agent framework. | Preserves §3; versions remain unpinned pending S01–S03. |
| D03 | Add immutable `SourceVersion` beneath stable `SourceRecord`; receipt evidence references a version, not mutable latest content. | §5–6 only define SourceRecord/Chunk, yet require historical hash verification. Necessary elaboration. |
| D04 | Keep business states `PROPOSED`, `NEEDS_REVIEW`, `CONFIRMED`, `DISPUTED`, `FULFILLED`, `REJECTED`; expose `SUPERSEDED` as an older version's effective state. “Extracted/unconfirmed” maps to PROPOSED. Revocation is a separate receipt standing `REVOKED`, with an audit event. | Reconciles user-requested vocabulary with §0.13 and §2.6; never overwrite signed `status_at_issuance`. |
| D05 | Every review/state change issues a new PromiseVersion and audit event. The prior version becomes effectively SUPERSEDED without editing its signed payload. An edit resets confirmation; a confirmation is never inherited across changed content. | Resolves mutable-looking convenience state versus immutable receipt wording in §2.6. |
| D06 | Add action state `NEEDS_RECONCILIATION`; success requires matching read-back. Store attempt/partial-result details separately. Reject maps to CANCELLED with reason. | §12.6 requires reconciliation but §2.7 enum omits it. |
| D07 | MVP uses explicitly specified `promiseops-json-v1`, SHA-256 and Ed25519; no JCS or VC conformance claim. JCS library evaluation remains a future interoperability option. | §2.6 permits a named internal canonical format and §15 already defaults to this label. Profile is frozen in protocol, not an invented cryptographic primitive. |
| D08 | Finalize `DEPENDS_ON` only JiraIssue→JiraIssue; derive reverse blocking. Do not store BLOCKS. Do not add undefined Task/role-key labels. ASSERTED_BY targets SourceRecord; human attribution uses chunk SPOKEN_BY. Jira identity prefers site+stable issue ID, with mutable key as alias. | Resolves incomplete endpoint alternatives in §5.2 and its issue-key identity example; avoids identity break on issue move. |
| D09 | Add AcceptanceRequirement, OperationRun and GraphState labels for explicit missing billing evidence, durable bounded jobs and publication revision. | These are FalkorDB state, not extra databases; addresses recovery, readiness and scenario snapshots. |
| D10 | Mock workload scheduling is the sole mandatory write. Live workload connector remains disabled and unmapped. Internal mock fields do not define a real vendor schema. | §9.3 asks for a configurable HTTP adapter; no route templates/mapping files are created now, and live mapping cannot be activated without the real contract. |
| D11 | Preserve all 22 baseline API routes. Add narrowly scoped operation polling, session bootstrap, connector health, receipt-copy verification, source retirement, conflict review, key lookup, and receipt revocation routes in API contract. | §8 lacks routes required by its screens, asynchronous processing, revocation and tampered-copy demo. Extensions are clearly marked. |
| D12 | Single backend process and serialized tenant mutation queue for MVP. Publish a bounded graph batch with audit records atomically only after a real-engine spike proves the transaction pattern. No multi-worker deployment until durable concurrency is proved. | MERGE alone is not a concurrency/uniqueness guarantee; do not assume constraints or cross-system transactions. |
| D13 | Proposal approval binds target, allowed changes, before-state digest, dependency digest, receipt hashes and policy version. Execution rechecks all of them; stale approval cannot authorize changed work. | Makes §2.7 and §12.6 actionable. Reviewer and executor are distinct in the seeded demo. |
| D14 | Deterministic calendar uses 15-minute slots, explicit local timezone and supplied free-capacity windows. Costs use decimal strings; no implied points conversion or FX. | Resolves “8 hours/days” / “3 units” in §11: fixture uses hours only. |
| D15 | Retention deletion may remove source bytes and signed payloads containing personal data under a documented policy. Verification must then return UNAVAILABLE, not VALID evidence. Keep minimal tombstones where permitted. | Reconciles §2.6 retention/append history with §12.5 privacy; logical append-only is not physical immutability. |
| D16 | SDK #285 is a reported open-schema relationship issue; #284 is concurrent-update safety/serialization. Bulk relationship round trips are #283. None is established here as a current core server defect. | Corrects master §20.5's issue description. Audit includes direct discussions and cached-status caveat. |
| D17 | No dependency is “compatible” based on release visibility alone. Server 6.x engine transition makes version and backup-format checks mandatory; do not use a floating latest image. | Research updates baseline context without changing stack. |
| D18 | Separate technical completion, customer acceptance, and invoice readiness. A milestone can be AT_RISK without being lost revenue. Renewal context stays outside totals. | Preserves §§2.3, 7 and prevents misleading commit-to-cash claims. |

## Concrete conflicts and their resolution

1. **Implement versus document:** the user's current task explicitly prohibits code, including master-requested configuration, fixtures and scripts. All examples remain Markdown; the future tree is only a plan.
2. **Immutable receipt wording:** master §2.6 calls the receipt immutable while §0.12 prohibits claiming the application is immutable. Here “immutable payload” means an application invariant; a database administrator can still change storage. Independent checkpoints strengthen detection, not mathematical immutability.
3. **State enums:** reconciliation is added to the action enum; revocation is separate from business confirmation. Existing seven user-visible promise labels are retained without conflating signature validity and business state.
4. **Source identity:** a stable external source ID cannot also identify every immutable source byte sequence. SourceVersion resolves this while keeping baseline source routes stable.
5. **Graph vocabulary:** Task, role key and symmetric BLOCKS alternatives are intentionally closed. Acceptance requirements have a real label; every relation's endpoints are enumerated.
6. **External action on unconfirmed evidence:** exploratory scenarios and draft proposals are allowed, but execution requires current confirmed relevant receipts and nonconflicting authoritative operational inputs. Internal confirmation does not amend contract terms or authorize a customer message.
7. **SDK citation:** #284 is not the bulk-write issue. Confirmed from linked issue titles/body, not from running SDK code.
8. **Jira issue docs:** search docs were accessible; issue read/write reference returned retrieval errors twice. Individual read/create/edit payloads remain TO-BE-VERIFIED; no live-write compatibility claim.

## Assumptions chosen to unblock design

| ID | Assumption | Validation / fallback |
|---|---|---|
| A01 | One synthetic demo tenant; viewer/reviewer/executor/admin are server-granted capabilities, not a hierarchy. | Role tests with a second tenant; production IAM requires Q04. |
| A02 | Three named synthetic people; clocks use an injected anchor; all fixture money USD. | SEED_SCENARIO defines exact data; never transfer values to real customers. |
| A03 | Default workload freshness 24 hours, action approval lifetime 15 minutes, graph read timeout 2 seconds. | Proposed defaults; owner configuration and measured limits in phase 0/5. |
| A04 | Serialized local mutation queue plus one atomic graph statement per bounded publication is feasible. | S01 is a blocking engineering spike. If unsupported, document another proven atomic pattern before writes ship. |
| A05 | Small bounded scheduling heuristic is adequate for five fixture issues. | Report feasible schedule/constraint failure, never global optimality. |
| A06 | Source ACL inheritance uses the most restrictive label and intersection of permitted principals. | Deny retrieval/derived outputs if no safe authorized evidence remains. |

## Questions requiring owner or environment input

These are recorded for the later build; answers are not needed to finish this documentation package.

| ID | Exact question | Blocks | Owner / safe default |
|---|---|---|---|
| Q01 | What is the real workload API specification, sandbox, auth, identity mapping, units, calendar semantics, versioning, idempotency and read-back behavior? | Live workload integration only | API owner; deterministic mock. Never guess. |
| Q02 | Which Teams tenant/meeting types, permissions, admin settings and recording/import consents are available, or which Vexa deployment/API contract is approved? | Live transcript capture/import | Tenant admin; synthetic VTT import. |
| Q03 | Which Jira Cloud site, projects, field mappings, account identifiers, scopes and sandbox write permissions are approved? | Live Jira sync/writes | Jira admin; synthetic export import. |
| Q04 | Which users may confirm commitments, approve capacity/cost, execute actions and view restricted sources? What separation-of-duties rule applies? | Real-user release | Product/security owner; explicit demo roles, distinct approver/executor. |
| Q05 | What source retention, deletion/legal-hold policy, region, model data processing terms and raw-source access policy apply? | Private-data use / production | Data owner; synthetic data only. |
| Q06 | Which real rate cards, currencies, calendars, scheduling priorities and invoice acceptance conditions are authoritative? | Real financial or delivery conclusions | Delivery/finance owner; illustrated synthetic inputs only. |
| Q07 | Which LLM provider/model/base URL and budget may process approved data? | Live extraction/generation | Owner; fixture extraction/replay explicitly labelled. |
| Q08 | Who owns production signing keys, trusted public-key distribution, compromise response and external checkpoint storage? | Production receipt trust | Security owner; nonproduction key and local trusted registry. |
| Q09 | What deployment target, concurrency, availability, recovery and commercialization/licensing requirements apply? | Production deployment | Platform/business owner; localhost single-process demo. |

## Engineering validation tasks, not owner questions

S01–S09 in [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) cover actual version compatibility, atomic graph writes and persistence, canonical-byte vectors, UI compatibility, connector mappings, LLM schema support, license dependencies, and measured performance. Do not ask the owner questions already answered by the baseline (database, product audience, required graph paths, stack, mock-first strategy or code prohibition).
