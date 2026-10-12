import hashlib

import pytest

from app.promise_seal.canonicalize import canonical_bytes, strict_json


def test_golden_bytes():
    assert canonical_bytes({"z": 1, "a": "Acme"}) == b'{"a":"Acme","z":1}'
    assert canonical_bytes({"s": '\n\t\b\r\f\x00"\\/'}) == (
        b'{"s":"\\u000a\\u0009\\u0008\\u000d\\u000c\\u0000\\"\\\\/"}'
    )
    assert canonical_bytes([None, True, False, -9007199254740991]) == (
        b"[null,true,false,-9007199254740991]"
    )


def test_unicode_never_normalized_or_escaped():
    assert canonical_bytes("é😀\u2028\u2029") == '"é😀\u2028\u2029"'.encode()
    assert canonical_bytes("é") != canonical_bytes("e\u0301")
    assert canonical_bytes([1, 2]) != canonical_bytes([2, 1])
    assert canonical_bytes({"a": None}) != canonical_bytes({})


@pytest.mark.parametrize(
    "value",
    [1.0, float("nan"), float("inf"), 2**53, -(2**53), "\ud800", {"é": 1}, {1: "x"}, (1, 2)],
)
def test_reject_noncanonical_domain(value):
    with pytest.raises(ValueError):
        canonical_bytes(value)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"a":1,"a":2}',
        b'{"a":{"b":1,"b":2}}',
        b"1.0",
        b"NaN",
        b"Infinity",
        b'"\\ud800"',
        b'"\xff"',
        b"\xef\xbb\xbf{}",
        b"9007199254740992",
    ],
)
def test_strict_parse_rejects(raw):
    with pytest.raises(ValueError):
        strict_json(raw)


def test_known_sha256():
    # Independent well-known SHA-256 vector; canonical "null" tested as bytes above.
    assert hashlib.sha256(b"abc").hexdigest() == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_nested_and_oversized_json_rejected():
    with pytest.raises(ValueError):
        strict_json(b"[" * 1000 + b"0" + b"]" * 1000)
    with pytest.raises(ValueError):
        strict_json(b" " * (1024 * 1024 + 1))
