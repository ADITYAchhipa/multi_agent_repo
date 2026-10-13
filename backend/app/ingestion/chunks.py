"""Bounded text-v1 chunks with exact global Unicode scalar offsets."""

import hashlib
from dataclasses import dataclass


class ChunkLimitExceeded(ValueError):
    pass


@dataclass(frozen=True)
class TextChunk:
    start: int
    end: int
    text: str
    digest: str


def chunk_text(text: str) -> list[TextChunk]:
    """Prefer paragraph boundaries; explicitly segment paragraphs over 4,000 scalars.

    This profile uses no overlap. Every scalar belongs to exactly one chunk.
    Reject a source needing more than 200 chunks before graph publication.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + 4000, len(text))
        if end < len(text):
            boundary = text.rfind("\n\n", start, end)
            if boundary >= start:
                end = boundary + 2
        excerpt = text[start:end]
        chunks.append(TextChunk(start, end, excerpt, hashlib.sha256(excerpt.encode()).hexdigest()))
        if len(chunks) > 200:
            raise ChunkLimitExceeded("source exceeds text-v1 chunk limit")
        start = end
    return chunks
