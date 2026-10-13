"""Conservative, deterministic candidate profile for local UTF-8 text imports.

Only complete lines beginning with I/We will/can deliver/provide/complete/ship/build
are selected. Classification stays ambiguous until human review. Source instructions
are inert text; no identity, date, price or business authority is inferred.
"""

import hashlib
import re
from typing import Literal

from pydantic import Field

from app.ingestion.chunks import TextChunk
from app.models.common import Digest, SafeInt, StrictModel, Text

PROFILE = "text-commitment-lines-v1"
_PATTERN = re.compile(r"(?:I|We) (?:will|can) (?:deliver|provide|complete|ship|build) \S.*", re.I)


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
    extraction_profile: Literal["text-commitment-lines-v1"] = PROFILE
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
            )
        )
        if len(candidates) > 100:
            raise CandidateLimitExceeded("source exceeds candidate profile limit")
    return candidates
