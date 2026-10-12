# Data ingestion and provenance

Status: proposed pipeline. Sources and fixtures are described in Markdown only; no input parser or dataset file has been created. Baseline §§2.1, 3.3, 6, 9.

## 1. Source inventory and trust

| Input | Mandatory parse representation | Evidence coordinates / limits |
|---|---|---|
| VTT transcript | UTF-8 original plus extracted cue text representation; retain cue IDs/voice labels/times | Half-open Unicode scalar offsets in parse text plus original cue time range; speaker label is not authenticated identity |
| TXT/MD notes/email/contract excerpt | Original bytes plus UTF-8 parse text, line-ending policy recorded | Offsets and line information; Markdown rendered inert, never executable HTML |
| JSON issue/workload/rate/acceptance export | Original JSON bytes plus deterministic human-readable parse representation where needed | Exact JSON pointer and original scalar value; schema type validated; no assumed vendor mapping |
| CSV structured export | Original bytes, declared encoding/delimiter/header, row/cell representation | Row number + column name plus stable structured pointer; formulas remain inert strings |
| Graph/Vexa fetched transcript | Raw response/content and mapped parse representation | Provider metadata/version if supplied, timestamps and attribution only where present |
| Jira sync | Raw minimal authorized issue response per version | Configured field pointers and stable site/issue IDs; not full private issue dump |
| PDF/DOCX | Stretch only | Page/paragraph/offset mapping and vetted parser required; unsupported in MVP |

All text is untrusted input, including legitimate documents that could be misinterpreted. Source type/ACL is supplied by an authorized admin from a closed list, not inferred as authority by a model. “Signed contract” is a documented/imported status with provenance, not a cryptographic signature verification claim.

## 2. Stable identity, artifacts and canonicalization

SourceRecord identifies logical external object: configured provider+external object ID; upload identity defaults to content hash within tenant/source type. An admin-provided source_key can group updates to the same logical upload; two unrelated uploads must not be conflated solely because their filenames match. Reimport idempotency key includes tenant, source identity, raw hash and parser/extraction profile; unchanged raw bytes with same profile returns NO_CHANGE. Reprocess with new profile compares semantic fact keys before creating any versions.

SourceVersion has monotonic version per source and immutable raw/parse hashes. Store exact original bytes and stable parse representation under generated artifact IDs in future `data/sources/{tenant_id}/`; original user filename is display metadata only. Reject path traversal, symlinks outside configured storage, oversized decompression, unsupported MIME/extension combinations and nonallowed encodings. No archive extraction in MVP. Hash is SHA-256 of exact respective bytes; raw hash and parse hash must not be confused.

Parse profile v1: strict UTF-8; record/strip UTF-8 BOM in parse representation only; convert CRLF/CR to LF for parse text; preserve all other whitespace and Unicode without NFC/NFKC normalization. VTT tags/cue metadata are parsed into separate fields; normalized cue text is retained as its own representation and mapped to original cue/byte ranges. Quotes must match that exact retained representation. Raw bytes remain available to show transformations. Structured JSON canonicalization for pointer comparisons is distinct from receipt signing; receipt canonicalization never modifies an evidence quote.

## 3. Chunking and candidate schema

Deterministic proposed chunk policy: group complete VTT cues or text paragraphs up to 4,000 Unicode scalar characters; retain up to 200-character overlap at paragraph/cue boundaries. Do not split a cue if under source limit; flag unusually large cue and use explicit segments. Max 200 chunks/run. Each chunk records global representation offsets, its exact text/hash, cue time interval and speaker label when single speaker. Multi-speaker chunk keeps per-span attribution in parse metadata; never assign the entire chunk to one guessed person.

Promise candidate has exact excerpt, normalized interpretation, deliverable, customer/project candidate IDs or null, speaker label/ID or null, nullable deadline with original wording/timezone/precision, price condition, explicitly sourced commercial value, commitment class, source/version/hash/offset refs, extraction model/template versions, extracted_at and confidence. Scope facts and structured relationships use the same evidence envelope. A candidate is not a signed agreement or an active change order.

## 4. Evidence validation and entity resolution

Evidence verifier checks `0 ≤ start < end ≤ representation length` and `representation[start:end] == quote`, with character indices defined as Unicode scalars. Also compare chunk global span, source/representation hashes and cue times. No case-folding, fuzzy matching or model “close enough” correction. If quote occurs multiple times, require explicit matching offsets. If source bytes cannot be decoded/retained, candidate is unpublishable. Structured facts require pointer existence and exact typed value equivalence; a fabricated pointer fails even if similar text appears elsewhere.

Entity order: exact tenant+provider ID; verified mapped account/email where authorized; reviewed alias; unique full normalized name within explicit customer/team context. Otherwise quarantine identity relation and keep source speaker label. Normalize names for candidate lookup only; do not merge distinct identities automatically. First-name-only, ambiguous alias, shared mailbox, stale user ID and cross-tenant matches require review. Auth actor binding to Person is server configuration, never transcript inference.

## 5. Publication stages and source-to-edge map

1. Authenticate import scope, validate limits, reserve durable OperationRun and idempotency record.
2. Save exact artifacts and hashes; build immutable SourceVersion draft/chunks.
3. Parse structured records or propose LLM candidates; validate typed output.
4. Verify quotes/pointers, entity identity, allowed relation endpoints and ACL inheritance.
5. Build assertion keys `(source_version_id,subject,type,object,qualifier,span)`; deduplicate overlap extraction.
6. Diff against prior published source version: unchanged fact retains logical identity; new evidence points to new version; missing assertions become RETIRED for that source only.
7. Run firewall; critical source-wide failures prevent publication; isolated rejected candidates become findings while safe candidates can publish with PARTIAL result.
8. Under tenant writer/revision check, publish source/chunks/accepted facts/receipts/findings and audit together. Advance current SourceRecord only for accepted publication; invalid critical input leaves prior current version intact.
9. Traverse Q06 to mark affected scenarios STALE and dependent pending/approved actions BLOCKED. New content never inherits confirmation; return structured changes and findings.

| Fact | Stored graph path / evidence |
|---|---|
| Spoken candidate | SourceRecord→HAS_SOURCE_VERSION→SourceVersion→HAS_CHUNK→SourceChunk→PROPOSES→PromiseVersion; optional SPOKEN_BY Person |
| Scope comparison | Contract→HAS_CLAUSE→ContractClause; PromiseVersion→POSSIBLY_COVERED_BY→clause, with classification and both source refs |
| Issue dependency | JiraIssue→DEPENDS_ON→JiraIssue; configured export/provider link pointer |
| Capacity | Person→HAS_WORKLOAD→immutable WorkloadSnapshot; provider/import version and calendar evidence |
| Milestone missing evidence | InvoiceMilestone→REQUIRES→AcceptanceRequirement with MISSING status; no fake satisfaction source |
| Authorized review | Promise/PromiseVersion→HAS_EVENT→AuditEvent; actor and content binding, separate from source speaker |

## 6. Incremental updates, conflicts and rollback

Source effective time and observed/import time are distinct. Out-of-order older external versions do not overwrite a newer known version; quarantine if ordering cannot be established. Missing source timestamp means freshness UNKNOWN unless a documented snapshot/as-of policy supplies one. Reimport today does not freshen a 100-day-old incident. Structured Jira updates preserve prior source versions; source deletion invalidates only assertions supported solely by that source.

Conflicts on single-valued owner/date/amount/scope are first-class Conflict records, not last-write-wins. Contract authority ranking is configured by source type/status, but newer speech never automatically overrides signed scope. Reviewer resolution selects operational interpretation with reason and evidence; opposing source remains historical. Automated repairs may normalize a known alias or duplicate assertion key before publication, not silently resolve semantic disagreements.

Rollback means a new corrective publication selecting prior known-good assertions, recording reason and superseding/retiring erroneous ones. It never edits a signed payload or erases the failed run. Receipt versions invalidated by a rollback remain auditable and cannot authorize execution. No external successful action is automatically undone; propose compensation separately.

## 7. Retirement, deletion and dead-letter handling

RETIRE stops active reasoning but retains bytes/history subject to ACL. DELETE is a policy-governed erasure request: identify every artifact/snippet/chunk/signed payload/audit copy containing source content; remove/redact as allowed; replace with minimal tombstones; retire unsupported edges; block dependent actions; mark evidence UNAVAILABLE. Do not leave quotations in a signed payload merely to preserve verification while claiming the source was erased. Deletion effects and retention policy are recorded without duplicating deleted content in the new event. Backups need expiry/redeletion handling; Q05 governs real data.

Dead-letter record is a failed/partial OperationRun plus KnowledgeFinding, with stage, retryability, safe error code, artifact hashes and remediation. It is stored in FalkorDB; no queue/database added. Retries use same source/version/idempotency keys after checking actual publication state. Unauthorized, unsupported-type, invalid-quote and schema errors need corrected input/review; transient provider read failures have bounded retries. Admin reprocess is the explicit retry interface. Staged artifact cleanup is retention-aware, not automatic destructive rollback.

Acceptance: T01/T02/T12/T13/T19/T29 test exact hash/offsets, overlapping chunks, malicious instructions, duplicate source/reprocess, conflict preservation, crashes between artifact and graph, deletion impact and stale approval invalidation.
