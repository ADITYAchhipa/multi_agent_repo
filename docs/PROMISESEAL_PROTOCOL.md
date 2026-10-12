# PromiseSeal v1 protocol

Status: proposed custom application protocol, not implemented, legally certified or W3C-conformant. Baseline §2.6; decisions D04–D07/D15. Receipt integrity, issuer standing, evidence verification and business confirmation are separate results.

## 1. What is attested

PromiseSeal records a platform's versioned interpretation of a commitment, the evidence available to it, and authorized application review. A SHA-256 digest identifies bytes; by itself it proves neither origin nor truth. An Ed25519 signature verified against a separately trusted public key shows that the corresponding private key signed the canonical payload. It does not prove speaker identity, source authenticity, agreement, delivery feasibility, legal authority, or enforceability. A service signature is not the named reviewer's personal digital signature.

Source hashes detect changed retained bytes. They do not prove an imported transcript accurately represents a meeting. Transcript speaker labels can be wrong. User confirmations are authenticated application events; their real-world authority is a separate policy/configuration matter.

## 2. Receipt data model

`receipt_id` equals immutable `PromiseVersion.id`. `promise_id` is stable across versions. Receipt envelope consists of exactly `payload`, `payload_sha256`, `signature_base64url`; fresh verification is a separate API response. The payload contains the signing metadata to prevent unsigned algorithm/key substitution. Unsigned proposals have `issued_at`, `signing_key_id` and envelope signature null; signed receipts require all three. MVP recommendation: sign PROPOSED versions too, while explicitly stating that signature is not confirmation.

| Payload field | Type / rule |
|---|---|
| `protocol_version` | Literal `promiseseal-v1` |
| `receipt_id`, `promise_id`, `tenant_id` | Nonempty opaque string; tenant is server derived |
| `version` | Integer ≥1; contiguous within promise |
| `issuer_id` | Configured platform issuer ID, included in trusted key lookup |
| `created_at`, `issued_at` | UTC timestamp; issued_at nullable only for unsigned proposal |
| `statement` | `{exact_excerpt, interpretation}`; exact excerpt must match a source ref |
| `deliverable` | Nonempty string ≤2000 characters |
| `customer_id`, `project_id` | String or null; unresolved IDs block consequential actions |
| `deadline` | `{original_text, precision, local_date, instant, timezone, resolution_basis}`; nullable subfields; precision `UNKNOWN\|DATE\|INSTANT`; a DATE never implies midnight |
| `price_condition` | `{kind, original_text}` with kind from schema catalogue |
| `commercial_value` | Null or `{amount:decimal string, currency:uppercase ISO currency code, evidence_ref_id}`; only supplied trusted value |
| `commitment_class` | `explicit\|conditional\|suggestion\|hypothetical\|ambiguous` |
| `source_refs` | Nonempty EvidenceRef array from API; references immutable SourceVersion IDs |
| `contract_refs`, `jira_refs`, `workload_refs` | Arrays of `{entity_id, source_version_id, evidence_ref_ids}`; empty permitted; current read-back is separate |
| `status_at_issuance` | Business lifecycle value; never changed after signing |
| `confirmation` | Null or `{confirmed_by, confirmed_at, confirmation_event_id, authority_scope, reviewed_content_hash}` |
| `review_event_id` | Null for first extraction; otherwise authenticated review/correction event ID |
| `previous_receipt_version_id`, `previous_payload_sha256` | Both null for v1; both required for v2+ |
| `canonicalization` | Literal `promiseops-json-v1` in this blueprint |
| `signature_algorithm` | Literal `Ed25519` (no client algorithm negotiation) |
| `signing_key_id` | Null when unsigned; otherwise trusted issuer/tenant key registry identifier |

Review event IDs are allocated before signing; event payload contains new receipt ID/digest, which avoids circular hashes. `reviewed_content_hash` is SHA-256 over the canonical object containing exactly `promise_id`, `tenant_id`, `statement`, `deliverable`, `customer_id`, `project_id`, `deadline`, `price_condition`, `commercial_value`, `commitment_class`, `source_refs`, `contract_refs`, `jira_refs`, `workload_refs`. It excludes issuance/review timestamps, lifecycle status, version IDs, signature metadata and confirmation itself. It binds reviewer confirmation to the content presented. The event records that digest plus before/after receipt IDs. Verification compares it to the applicable receipt content. EvidenceRef.verification inside a signed payload records the issuance-time check only; fresh verification is always recomputed separately.

## 3. Canonical serialization profile

DECISION D07: define `promiseops-json-v1` precisely for the Python-owned MVP. This is not RFC 8785/JCS. The JCS reference specifies different interoperability requirements; a future migration needs a new canonicalization label and receipt version. [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) was inspected 2026-10-12.

1. Parse strict UTF-8 JSON; reject duplicate object keys, invalid Unicode/surrogates, unknown payload keys, missing required keys, nonfinite numbers and extra envelope fields. Validate schema **before** hashing.
2. The canonical domain permits objects with schema-defined ASCII keys, arrays, Unicode strings, booleans, null and integers in the safe range −9,007,199,254,740,991 to +9,007,199,254,740,991. No JSON floating-point numbers. Money/rates/hours are normalized decimal strings: base-10, no exponent, no plus, no redundant leading/trailing zero, zero represented `0`; negative zero rejected. Business amounts nonnegative.
3. Keys sort by ascending ASCII code recursively. No whitespace between tokens, UTF-8 BOM or trailing newline. Arrays retain their stored order. Producers sort source refs by `(source_version_id, start_offset, end_offset, evidence_ref_id)`, with null offsets ordered before nonnegative offsets; other ref arrays by entity_id then source_version_id and nested evidence IDs lexically. String sort uses Unicode scalar order without locale collation. Verifiers never reorder arrays to repair an altered receipt.
4. Strings use JSON quoting: `"` and backslash escaped, control U+0000–U+001F always encoded as lowercase six-character `\u00xx`; all other Unicode scalar values emitted directly as UTF-8, including U+2028/U+2029; slash unescaped. No Unicode normalization, whitespace cleanup or newline conversion during signing/verifying. Original parse representation preserves any normalization separately.
5. Integers use base-10 shortest decimal text, boolean/null literals lowercase. Required nullable fields are emitted as null, not omitted. Optional extensions are forbidden in v1; a new schema version is required.
6. Normalize timestamps in payload construction to UTC `YYYY-MM-DDTHH:mm:ss.SSSZ`. Source timestamp precision remains explicit in evidence metadata. Verification validates this form but never silently changes a signed value.
7. Canonicalize only `payload`. Compute lowercase hex SHA-256 of its bytes. Sign those exact bytes with Ed25519 (not the hex hash string). Signature is unpadded URL-safe Base64. Envelope digest/signature and fresh verification fields are excluded from payload to avoid self-reference.

Illustrative canonicalization mini-vector (not a full receipt and not an executed test): objects with keys supplied as `z`, `a` and values `1`, `Acme` must serialize exactly to `{"a":"Acme","z":1}`. Future vectors must cover Unicode decomposed/composed strings, emoji, escaped controls, array reordering, null versus missing, duplicate keys, zero, decimal scale, invalid timestamps and unsupported algorithm labels. A golden canonical-byte fixture plus known-key signature vectors are a phase-0 gate; no digest/signature is fabricated here.

## 4. Business lifecycle and version transitions

“Extracted” is an ingestion stage; “unconfirmed” displays as PROPOSED. `SUPERSEDED` is an older version's effective status and cannot be submitted as a review decision. An older payload's status_at_issuance may still say CONFIRMED even when its effective standing is SUPERSEDED or REVOKED.

| Current business state | Operation / actor | New business state and conditions |
|---|---|---|
| None | Validated extraction / service | PROPOSED v1; triage findings may immediately require review |
| PROPOSED | Flag ambiguity / service | NEEDS_REVIEW new version + finding |
| PROPOSED, NEEDS_REVIEW | CONFIRM / reviewer | CONFIRMED; exact evidence, resolved IDs/date as needed, no material unresolved conflict |
| PROPOSED, NEEDS_REVIEW, CONFIRMED | DISPUTE / reviewer | DISPUTED; reason and evidence refs required |
| PROPOSED, NEEDS_REVIEW, DISPUTED | REJECT / reviewer | REJECTED; reason required |
| DISPUTED | CONFIRM / reviewer | CONFIRMED only with documented resolution of every material conflict |
| CONFIRMED | FULFILL / reviewer | FULFILLED; completion evidence required; does not mean invoice accepted |
| FULFILLED | DISPUTE / reviewer | DISPUTED; new contradictory completion evidence |
| Any current state except REJECTED | REVISE / reviewer or validated changed source | PROPOSED, or NEEDS_REVIEW when conflict remains; changed content clears confirmation |
| REJECTED | New contrary evidence / reviewer | NEEDS_REVIEW; new version and reason; no silent reopening |

Every row produces a new PromiseVersion and audit event, with contiguous version and predecessor digest/ID; current pointer updates atomically. State-only FULFILL can carry prior confirmation only if the reviewed content hash is identical, and retains original confirmer/event. DISPUTE, REJECT and REVISE set confirmation null. Confirm always records the currently authenticated actor. Automation cannot CONFIRM, FULFILL or resolve a dispute. Reprocessing never creates another identical extraction receipt solely because a model run occurred.

## 5. Receipt standing, revocation and keys

New current receipt standing ACTIVE; predecessor becomes effective SUPERSEDED through event/projection. An admin may revoke a specific receipt with reason, expected version and authenticated event. REVOKED takes precedence over SUPERSEDED for display. Revocation withdraws platform reliance; it does not erase content or automatically claim that the business promise was cancelled. If the current receipt is revoked, no action can rely on it; reviewer must issue a replacement with fresh review before execution. Revoking an old receipt does not silently revoke all successors, but verification flags their chain dependency for review.

Trusted key registry is server configuration for MVP, with issuer, tenant, key ID, Ed25519 public key, activation/retirement/compromise times and policy. Private key is a server secret file, never graph data or client input. A public key returned alongside an untrusted receipt is not automatically trusted. Verifier resolves only configured key IDs; no fetching arbitrary `key_url` from payload.

Rotation: activate new key ID, sign future versions/events with it, keep old public keys for historical verification. Retirement stops issuance, not historical mathematics. Compromise marks affected signatures' current trust INDETERMINATE/compromised even if cryptographically valid, blocks execution and triggers source/action review. Trusted time of compromise may be uncertain; a self-reported issued_at is not an independent timestamp. Production key custody, external checkpoints and trust-distribution owner remain Q08.

## 6. Fresh verification algorithm

Return individual checks, never just a stored boolean:

1. Authenticate tenant/ACL for receipt and requested evidence. Strictly parse envelope and supported profile.
2. Canonicalize payload and compare SHA-256. A changed field yields `PAYLOAD_DIGEST_MISMATCH`; report path-level schema errors when knowable, but do not pretend a hash alone identifies the modified field.
3. Look up trusted key by issuer/tenant/key ID; reject unknown key/algorithm. Verify signature against exact bytes. Distinguish UNSIGNED, INVALID_SIGNATURE and key trust status.
4. Resolve previous versions; verify same tenant/promise, contiguous sequence, matching predecessor ID/hash and no forks/cycles. Missing historical payload is INDETERMINATE, not proof of a valid chain.
5. Recompute retained raw/parse artifact hashes and quote substring/offset checks. Source content missing or deleted gives UNAVAILABLE; mismatch gives MISMATCH and execution block. A newer source version does not retroactively make older original bytes hash-invalid; it makes reliance stale.
6. Verify confirmation event actor/authority/content binding and the applicable audit event signatures/hash chain. An authorized actor record shows system authentication, not legal authority proof.
7. Resolve current standing and freshness. Return cryptographic integrity plus standing, source checks, confirmation, latest-version status and `eligible_for_action` determined by policy.

Example result (illustrative, not executed): `integrity=VALID`, `standing=SUPERSEDED`, `sources=MATCH`, `eligible_for_action=false`. Another: `integrity=VALID`, `standing=ACTIVE`, `sources=UNAVAILABLE`, `eligible_for_action=false`. “Valid signature” is never labelled “true promise.”

`eligible_for_action` on receipt verification means the **receipt evidence prerequisites** are currently satisfied (current CONFIRMED version, trusted signature, available matching evidence and no material conflict). It is necessary but not sufficient for execution; it does not evaluate a particular target, user's execution capability, approval, scenario, expiry or connector field allowlist. Only the action policy route can authorize dispatch. UI must label it “receipt eligible as supporting evidence,” never “action approved.”

## 7. Audit trail and rollback limits

Audit events have a tenant-local contiguous sequence. Canonical event body contains protocol label `promiseops-audit-v1`, event ID, tenant, sequence, type, actor, occurred_at, request ID, payload, previous-event hash and signing key ID. Use the same canonical byte profile, SHA-256 and Ed25519. Genesis previous hash is null. Append event, state transition and GraphState audit head in the same proven atomic publication. Events include source publication/retirement, receipt issuance/review/revocation, conflict resolution, proposal/approval/execution attempts, read-back, repair and policy change.

Chain checks detect local alterations/gaps relative to the trusted head. An attacker who controls graph, signing key and all local checkpoints can replace the whole history. A checkpoint exported outside the graph can detect rollback only if independently trusted and retained. MVP provides a local signed export design; independent storage and timestamp trust are production work. Do not call the graph tamper-proof or mathematically immutable.

Deletion/redaction may make historical source or payload verification impossible. Return tombstone and component UNAVAILABLE under ACL rather than leaking erased content through audit records. Approval decisions citing removed material become unusable. Production retention/legal-hold choices remain Q05; no legal retention rule is invented.

## 8. Standards and acceptance

W3C VC issuer/claim/verifier separation informs terminology only. PromiseSeal v1 does not implement a VC context/type model, credential presentation, holder binding, standardized status list, VC securing mechanism or conformance suite. There is no implemented interoperability. Any future VC representation must specify those separately and retain PromiseSeal's business-state semantics. Sources inspected 2026-10-12: [VC Data Model 2.0 dated Recommendation](https://www.w3.org/TR/2025/REC-vc-data-model-2.0-20250515/), [Data Integrity](https://www.w3.org/TR/vc-data-integrity/).

Ed25519 signing/verification interfaces are documented by [cryptography](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/); selected stable package/runtime must still pass S02. Protocol acceptance: T07/T08/T18/T19/T29 cover canonical vectors, modified payload/signature/key, broken chain, revocation, deletion, unauthorized confirmation, concurrent versions and replay. All targets are proposed; none has been run in this phase.
