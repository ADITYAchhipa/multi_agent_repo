"""Conservative, deterministic candidate profile for local UTF-8 text imports.

Complete bounded lines with explicit subject and delivery verbs are selected.
Only explicit ISO dates and unambiguous currency-coded amounts are structured.
Classification and identity resolution remain subject to human review.
"""

import hashlib
import re
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.ingestion.chunks import TextChunk
from app.models.common import Digest, SafeInt, StrictModel, Text
from app.promise_seal.models import Deadline, PriceCondition

PROFILE = "text-commitment-lines-v2"
_PATTERN = re.compile(
    r"(?:(?P<speaker>[A-Z][\w .&'-]{0,79}): )?"
    r"(?P<party>(?i:I|We)|[A-Z][\w&'-]*(?: [A-Z][\w&'-]*){0,5}) "
    r"(?i:will|can) (?P<work>(?i:deliver|provide|complete|ship|build) \S.*)"
)
_MONEY = re.compile(
    r"\bfor (?P<currency>USD|EUR|GBP|INR|CAD|AUD|JPY) "
    r"(?P<amount>\d{1,15}(?:\.\d{1,4})?)(?!\d|\.\d)(?=[.;, ]|$)"
)


def _terms(quote: str) -> dict:
    # Only a single explicit ISO date is resolvable without meeting/timezone context.
    dates = list(re.finditer(r"\b(?:by|on) (\d{4}-\d{2}-\d{2})(?=[.;, ]|$)", quote))
    deadline = dict(
        original_text=None,
        precision="UNKNOWN",
        local_date=None,
        instant=None,
        timezone=None,
        resolution_basis=None,
    )
    if len(dates) == 1:
        deadline["original_text"] = dates[0].group(0)
        try:
            date.fromisoformat(dates[0].group(1))
        except ValueError:
            pass
        else:
            deadline.update(
                precision="DATE",
                local_date=dates[0].group(1),
                resolution_basis="Explicit ISO calendar date in retained evidence",
            )
    price = dict(kind="UNKNOWN", original_text=None)
    money = list(_MONEY.finditer(quote))
    free = re.search(r"\bat no additional charge\b", quote, re.I)
    change = re.search(r"\bsubject to (?:a )?change order\b", quote, re.I)
    amount = currency = None
    ambiguous_money = len(
        re.findall(r"\b(?:USD|EUR|GBP|INR|CAD|AUD|JPY)\b", quote)
    ) != 1 or re.search(r"\b(?:not|per|each|monthly|annually|hourly|daily)\b", quote, re.I)
    if len(money) == 1 and not free and not change and not ambiguous_money:
        value = money[0]
        price.update(kind="PRICED", original_text=value.group(0))
        amount = format(Decimal(value["amount"]), "f")
        if "." in amount:
            amount = amount.rstrip("0").rstrip(".")
        currency = value["currency"]
    elif free and not money and not change:
        price.update(kind="NO_ADDITIONAL_CHARGE", original_text=free.group(0))
    elif change and not money and not free:
        price.update(kind="CHANGE_ORDER_REQUIRED", original_text=change.group(0))
    return dict(
        deadline=Deadline(**deadline),
        price_condition=PriceCondition(**price),
        commercial_amount=amount,
        commercial_currency=currency,
    )


class CandidateLimitExceeded(ValueError):
    pass


class PromiseCandidate(StrictModel):
    exact_excerpt: Text
    interpretation: Text
    deliverable: Text
    start_offset: SafeInt
    end_offset: SafeInt
    chunk_start: SafeInt
    assertion_key: Digest
    commitment_class: Literal["ambiguous"] = "ambiguous"
    extraction_profile: Literal["text-commitment-lines-v2"] = PROFILE
    deadline: Deadline
    price_condition: PriceCondition
    commercial_amount: str | None = None
    commercial_currency: str | None = None
    confidence: str = Field(default="UNKNOWN", pattern="^UNKNOWN$")


def extract_candidates(text: str, chunks: list[TextChunk]) -> list[PromiseCandidate]:
    candidates = []
    seen = set()
    offset = 0
    for line in text.splitlines(keepends=True):
        quote = line.strip()
        start = offset + len(line) - len(line.lstrip())
        end = start + len(quote)
        offset += len(line)
        if len(quote) > 2000 or not _PATTERN.fullmatch(quote):
            continue
        chunk = next((c for c in chunks if c.start <= start < end <= c.end), None)
        if chunk is None:
            continue
        key = hashlib.sha256(quote.encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            PromiseCandidate(
                exact_excerpt=quote,
                interpretation=quote,
                deliverable=quote,
                start_offset=start,
                end_offset=end,
                chunk_start=chunk.start,
                assertion_key=key,
                **_terms(quote),
            )
        )
        if len(candidates) > 100:
            raise CandidateLimitExceeded("source exceeds candidate profile limit")
    return candidates
