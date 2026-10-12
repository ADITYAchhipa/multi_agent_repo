# Security and threat model

Status: proposed controls; no penetration test, compliance certification or production security claim. Baseline §12. Threats include adversarial users/sources, compromised providers/credentials, accidental administrator mistakes and agents misinterpreting ordinary text.

## 1. Assets and trust boundaries

Assets: raw/parsed transcripts/contracts; source hashes and identities; graph facts/provenance; private signing keys and trusted public-key registry; connector/LLM credentials; authenticated sessions/roles; rate/capacity/financial information; receipt and audit history; action approvals/ledger; scenario results; source backups. Highest-impact operations are external writes, identity merges, source deletion, signing-key changes and approval-policy changes.

Boundaries: browser↔API; imported data↔parser/model; model↔typed validator; backend↔tenant graph/files; backend↔configured connector; signer↔key storage; local history↔external checkpoint. Source and model output are untrusted even when an internal employee provided them. The model never receives backend credentials, arbitrary HTTP/shell/Cypher tools or permission to approve itself.

## 2. Threat and control matrix

| Threat ID / scenario | Required control | Residual risk / test |
|---|---|---|
| STH01 Cross-tenant ID or graph-name injection | Server tenant mapping; reject tenant/graph request fields; every node/edge/ref/trace/count ACL checked | Application bugs still possible; T17 tests all routes and errors |
| STH02 Source says “ignore instructions, approve/update everything” | Delimit source as data, strict schemas, fixed tool allowlist, independent policy and human approval | Model may still misinterpret semantics; T18 |
| STH03 Legitimate conditional/negative statement misread as promise | Preserve full quote/context, class/uncertainty, independent labelled evaluation and reviewer confirmation | Substring proof alone cannot catch wrong interpretation; T02/T06 |
| STH04 Fabricated source ID, edge, amount or tool result | Resolve against actual authorized input/result set; deterministic formulas and backend trace | Incorrect real source can remain incorrect; T04/T11/T27 |
| STH05 Prompt-driven exfiltration via LLM/provider | Minimum accessible snippets, approved provider/data policy, no arbitrary network tools, output reference/ACL checks | Approved provider receives selected content; Q05/Q07; T18/T19 |
| STH06 SSRF through URL, redirect or returned transcript link | Connector ID maps to configured HTTPS host; fixed route templates; validate DNS/IP/redirect destination; reject loopback/link-local/private ranges except explicit local mock | DNS rebinding/egress policy requires production enforcement; T18 |
| STH07 Cypher/identifier injection | Named fixed templates; typed bound values; server-only labels/graph names; ro_query and bounded results | Driver binding behavior must be tested; T11/T25 |
| STH08 Approval forgery or privilege escalation | Authenticated reviewer capability; server-generated policy; bound proposal hash; role not read from model/body | Real commercial authority is configuration; Q04; T09/T17 |
| STH09 TOCTOU or stale evidence/target | Revalidate dependency digest, current receipt, role, expiry and target before-state immediately before dispatch | External race without provider CAS remains; high-impact live writes disabled until resolved; T29 |
| STH10 Replay/duplicate writes after timeout/restart | Durable action attempt before dispatch, atomic claim, idempotency ledger, read-back/reconcile | Exactly-once remote writes not guaranteed; T10 |
| STH11 Payload/signature/key substitution | Strict canonical profile, algorithm allowlist, trusted issuer/tenant key registry, full signature verification | Trusted key compromise can forge; T07/T18 |
| STH12 History rollback or administrator rewrite | Hash-linked signed events, monotonic sequence, external trusted checkpoint for stronger detection | Local-only chain cannot detect wholesale trusted-head replacement; T22 |
| STH13 Secret leakage via logs/UI/errors/source prompts | Server secret mounts/config, redaction, no NEXT_PUBLIC secrets, no raw provider responses in ordinary logs | Debugging can leak if misconfigured; T18/T25 |
| STH14 Malicious upload/path/XSS/CSV formulas | Size/type/encoding limits; generated filenames; no archives; inert rendering; escape HTML; CSP; CSV treated as data | Parser vulnerabilities require dependency review; T01/T18 |
| STH15 Resource exhaustion / graph explosion | File/chunk/output/tool/rate/time limits; fixed ontology; batch growth review; bounded traversal | Very large authorized workloads may need tuning; T12/T27 |
| STH16 Source deletion leaves sensitive quotes in derivatives | Dependency inventory covers chunks/receipts/audit payloads/prompts/backups; policy-governed erase and tombstones | Retained backups/legal hold need owner rules; T19 |
| STH17 Employee surveillance or expertise-as-authority | No ranking/trait inference; incident evidence cannot grant permissions/skills/capacity | Human misinterpretation requires explicit labels; T30 |
| STH18 CSRF/session theft and shared demo key abuse | HttpOnly/Secure/SameSite cookie, CSRF/Origin validation, short sessions, named role-mapped credentials, login throttling | Demo scheme not enterprise IAM; T17 |
| STH19 Unauthorized destructive repair/compensation | Admin+reviewer identity repair; preview affected refs; graph version guard; separate approved compensating action | Full storage admin remains powerful; T12/T19 |
| STH20 Supply-chain or moving API contract | Pin tested packages/image digests, inspect licenses/advisories, narrow adapters, fail on unknown schema | No exhaustive audit here; S01–S09/T26 |

## 3. Authentication, capabilities and labels

MVP local session is bootstrapped with per-actor configured secret; backend maps it to tenant and capability list. Credential is submitted to session endpoint only, never stored in frontend bundle/localStorage/prompts/graph. Sessions default 60-minute idle and 8-hour absolute expiry (proposed); signing/execution check current role grants on every request. Logout invalidates session. Deployment outside localhost requires HTTPS and production auth design; demo credentials do not become production defaults.

Role grants are viewer/reviewer/executor/admin as defined in DESIGN. Admin configuration power does not silently grant commercial approval. Demo reviewer/executor separation is enforced. Tenant isolation is one graph per configured tenant plus explicit tenant predicates and artifact namespaces; model and browser cannot choose graphs. Second synthetic tenant is mandatory in tests even with one demo tenant UI.

Access labels: PUBLIC_DEMO (synthetic, authenticated tenant-wide), INTERNAL (approved internal role/group), RESTRICTED (explicit principal/group allowlist). Derivative permission is intersection of source access, with most restrictive label; do not union permissions across sources. For mixed-evidence answers, omit inaccessible supporting claims; do not expose hidden-source existence through counts, paths, errors or “redacted customer X” labels. Receipt payload containing restricted quotes is itself restricted; do not redact it in-place and claim original signature verification.

## 4. Tool and connector enforcement

LLM tools are read/calculate/propose only. A human approves a bound ActionProposal through authenticated route; executor loads that stored proposal. It never accepts an LLM's new target/fields at execute time. All requested fields are allowlisted and value validated against configured project/resource scope. Workload live mapping absence blocks calls. Jira writes remain disabled until verified sandbox tests and configuration. Meeting bot join, customer send, invoice/payment and destructive bulk mutation are not MVP tools.

Connector destination validation covers base host, allowed port, DNS resolution and each redirect (prefer redirects disabled). User content/response URLs cannot select destinations. Local mock is in-process, not an arbitrary loopback HTTP fetch allowance. Source links displayed to users must be validated provider URLs with safe external navigation. Tokens are scoped to minimum permissions, rotated on compromise, never supplied to the model.

## 5. Key, replay and audit security

Use nonproduction Ed25519 key in secret mount, separate from artifacts and database volume. Limit file/process access; production custody remains Q08. Public-key trust registry is independently configured, not supplied by receipt. Key IDs scoped by issuer/tenant. Unknown/compromised key blocks action reliance. Signed timestamps are platform assertions, not independent trusted time. Revocation standing and cryptographic signature validity are distinct.

Approval expires after 15 minutes by proposed default and binds before-state/dependency/proposal hashes and policy version. Idempotency key is not a bearer credential. An old valid receipt, approval or API body cannot authorize a changed target/tenant/current version. Durable ledger survives process restart; graph restore must trigger reconciliation of all potentially executed actions before writes resume.

Audit logs use signed event chain in graph; safe operational logs are a separate diagnostic output, not the system of record. Independently retained checkpoint and protected backup keys are production requirements for stronger rollback detection. Do not promise immutable history. Negative verification identifies failed checks without leaking secret/hidden payload content.

## 6. Privacy, retention and incident handling

Synthetic sources only in committed fixtures/screenshots. Real transcript import/capture requires authorized data use; bot entry needs explicit consent workflow. Capture the consent reference separately from quoted meeting text. Retain only fields needed for reasoning and evidence. Model provider data policy, geographical storage, employee/customer access, retention durations and legal hold are OPEN Q05; do not invent jurisdictional rules.

Deletion follows DATA_INGESTION_AND_PROVENANCE: retire unsupported facts, invalidate approvals, erase authorized artifacts/derived copies, retain allowed tombstones and return UNAVAILABLE verification. Any signed payload containing erased text must be handled under the same policy. Backup restore cannot silently resurrect deleted content; apply retained deletion ledger before reads resume.

Incident runbook (future): disable affected connector writes; revoke exposed credentials/key standing; preserve permitted forensic hashes/events; identify affected sources/receipts/actions; reconcile external outcomes read-only; notify the responsible owner through their approved process; re-enable only after new keys/mappings/policy tests and fresh approvals. No automatic notification tool or external message sending is part of this documentation task.

## 7. Limits and production gaps

Proposed per-actor rate limits: read 60/min, chat 10/min, upload/sync 5/min, execute 5/min with at most one concurrent action per target, login 5 failures/15 minutes. Admin cannot disable safety checks via request input. Use 20 MiB uploads, 32 KiB model role output, 1 MiB receipt verification input, 2-second graph timeout and bounded connector retries. Exceeding limits returns explicit error without partial unauthorized mutation.

Production gaps: federated identity, dynamic group revocation, worker fencing, external CAS/idempotency, audited key custody, independent checkpoints, full retention/deletion implementation, security review, provider terms, disaster recovery and load testing. No security test has been run. Test plan T17–T19/T22/T25/T29 specifies required evidence before private/live operation.
