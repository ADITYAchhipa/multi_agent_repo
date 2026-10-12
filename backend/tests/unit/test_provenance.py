import hashlib

import pytest

from app.ingestion.quote_verifier import parse_text, verify_quote
from app.models.api import EvidenceRef


def test_raw_and_parse_hashes_unicode_offsets(payload_dict):
    raw = b"\xef\xbb\xbf" + "header\r\n😀e\u0301\r\n".encode()
    representation = parse_text(raw)
    assert representation == "header\n😀e\u0301\n"
    data = payload_dict["source_refs"][0]
    data.update(
        source_hash=hashlib.sha256(raw).hexdigest(),
        representation_hash=hashlib.sha256(representation.encode()).hexdigest(),
        quote="😀e\u0301",
        start_offset=7,
        end_offset=10,
    )
    evidence = EvidenceRef.model_validate(data)
    assert verify_quote(raw, representation, evidence)
    assert not verify_quote(raw + b"x", representation, evidence)
    assert not verify_quote(raw, representation.replace("e\u0301", "é"), evidence)
    data["end_offset"] = 11
    assert not verify_quote(raw, representation, EvidenceRef.model_validate(data))


def test_parser_limits_and_encoding():
    with pytest.raises(ValueError):
        parse_text(b"x" * (20 * 1024 * 1024 + 1))
    with pytest.raises(UnicodeError):
        parse_text(b"\xff")
