import hashlib

import pytest

from app.ingestion.chunks import ChunkLimitExceeded, chunk_text


@pytest.mark.parametrize(
    "text",
    ["", "🙂\n\nhello", "a" * 3998 + "\n\n" + "é" * 5000, "a" * 3999 + "\n\nend", "x" * 800000],
)
def test_chunks_cover_exact_unicode_representation(text):
    chunks = chunk_text(text)
    assert "".join(chunk.text for chunk in chunks) == text
    assert len(chunks) <= 200
    for chunk in chunks:
        assert 0 < chunk.end - chunk.start <= 4000
        assert text[chunk.start : chunk.end] == chunk.text
        assert chunk.digest == hashlib.sha256(chunk.text.encode()).hexdigest()
    assert chunks == chunk_text(text)


def test_paragraph_boundary_and_limit():
    text = "a" * 3500 + "\n\n" + "b" * 1000
    assert chunk_text(text)[0].end == 3502
    with pytest.raises(ChunkLimitExceeded):
        chunk_text("x" * 800001)
