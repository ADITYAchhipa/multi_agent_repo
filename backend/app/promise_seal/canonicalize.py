"""promiseops-json-v1; deliberately not JCS. See PROMISESEAL_PROTOCOL §3."""

import hashlib
import json

MAX_SAFE_INTEGER = 9007199254740991


def _string(value: str) -> str:
    pieces = ['"']
    for char in value:
        code = ord(char)
        if 0xD800 <= code <= 0xDFFF:
            raise ValueError("surrogate is not a Unicode scalar")
        if code < 32:
            pieces.append(f"\\u{code:04x}")
        elif char in {'"', "\\"}:
            pieces.append("\\" + char)
        else:
            pieces.append(char)
    return "".join(pieces) + '"'


def canonical_bytes(value: object, *, _depth: int = 0) -> bytes:
    if _depth > 64:
        raise ValueError("canonical input nesting exceeds limit")
    if value is None:
        return b"null"
    if type(value) is bool:
        return b"true" if value else b"false"
    if type(value) is int:
        if abs(value) > MAX_SAFE_INTEGER:
            raise ValueError("integer outside canonical safe range")
        return str(value).encode("ascii")
    if type(value) is str:
        return _string(value).encode("utf-8")
    if type(value) is list:
        return b"[" + b",".join(canonical_bytes(v, _depth=_depth + 1) for v in value) + b"]"
    if type(value) is dict:
        if any(type(k) is not str or not k.isascii() for k in value):
            raise ValueError("canonical object keys must be ASCII strings")
        return (
            b"{"
            + b",".join(
                _string(k).encode("ascii") + b":" + canonical_bytes(value[k], _depth=_depth + 1)
                for k in sorted(value)
            )
            + b"}"
        )
    raise ValueError("unsupported canonical value type")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def strict_json(raw: bytes) -> object:
    if len(raw) > 1024 * 1024:
        raise ValueError("JSON input exceeds one MiB")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate object key")
            result[key] = value
        return result

    def forbidden(_):
        raise ValueError("floating point and nonfinite numbers are forbidden")

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_float=forbidden,
            parse_constant=forbidden,
        )
        canonical_bytes(value)
        return value
    except (UnicodeError, RecursionError) as exc:
        raise ValueError("invalid UTF-8 JSON") from exc
