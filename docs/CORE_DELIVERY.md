# Core source and receipt delivery

## Implemented

Source detail now fetches history in stable 100-row database pages, ordered by version and relationship identity. A graph revision guard retries the complete read up to three times if concurrent writes change its snapshot; repeated changes return the existing graph-unavailable error. The frontend response contract is unchanged and includes all versions, so both the current source and historical selection work beyond 100 revisions. Each database query is bounded; total response size still grows with history and a future public pagination contract is warranted.

The deterministic `text-commitment-lines-v2` extraction profile accepts complete lines with `I`, `We`, or an explicitly capitalized party name followed by `will`/`can` and `deliver`, `provide`, `complete`, `ship`, or `build`. An explicit `Speaker: ` prefix is accepted. Exact Unicode quote offsets, chunk containment, candidate deduplication and the 100-candidate cap remain enforced. No source instructions are executed.

A single explicit `by YYYY-MM-DD` or `on YYYY-MM-DD` date is calendar-validated and signed as DATE precision, without inventing a timezone or instant. Invalid, relative, absent, and multiple matching dates remain UNKNOWN. A single `for USD/EUR/GBP/INR/CAD/AUD/JPY <amount>` clause yields a normalized decimal commercial value referencing the retained evidence. Multiple currencies, conflicting free/change-order clauses, rates or negations leave commercial value unresolved. Exact `at no additional charge` and `subject to a change order` clauses map to the corresponding price condition only when unambiguous. All proposals remain ambiguous and PROPOSED, requiring human review.

Dates are also projected into graph fields so the existing promise-list deadline filters work. Extraction profile v2 is recorded in the signed source audit and evidence relationships. Existing v1 receipts remain readable and verifiable; changing a source under v2 may create new proposals for previously seen lines because profile version participates in candidate identity. An unchanged source remains NO_CHANGE and is not automatically re-extracted.

## Deliberate uncertainty and remaining work

No party name is converted into a customer/project ID. Parties, dependencies, and conditional wording remain in the exact signed source excerpt and full deliverable text; this phase does not add structured party/dependency fields to the v1 receipt schema. General prose, speaker attribution without the supported grammar, relative dates, negotiated totals, currency symbols, tax/rate calculations and cross-line context need further extraction/review design. This deterministic parser is not a general language understanding system.

All source history is returned to preserve the established contract. Large histories therefore have aggregate memory/response costs despite bounded database reads. Revision guards assume all legitimate graph mutations increment GraphState.revision.

## Verification commands

From `backend/`, with disposable FalkorDB at 127.0.0.1:16379:

```sh
DEBUG_DOCS=false RUN_FALKORDB_INTEGRATION=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest \
  tests/unit/test_candidates.py tests/unit/test_source_history_pages.py \
  tests/integration/test_core_delivery.py tests/integration/test_source_upload.py \
  tests/integration/test_proposal_publication.py -q -p no:cacheprovider
```

Live regression covers 101 genuine versioned uploads, current and first-version reads, explicit date filtering, signed commercial evidence and receipt verification. Unit tests cover Unicode evidence, boundary containment, invalid/ambiguous dates, ambiguous commercial values, read retries and continuous concurrent-change failure.
