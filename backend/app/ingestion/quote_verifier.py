import hashlib

from app.models.api import EvidenceRef


def verify_quote(original: bytes, representation: str, evidence: EvidenceRef) -> bool:
    """Use Unicode scalar offsets; no fuzzy repair or normalization while verifying."""
    try:
        encoded = representation.encode("utf-8", errors="strict")
    except UnicodeError:
        return False
    return (
        hashlib.sha256(original).hexdigest() == evidence.source_hash
        and hashlib.sha256(encoded).hexdigest() == evidence.representation_hash
        and evidence.quote is not None
        and evidence.start_offset is not None
        and evidence.end_offset is not None
        and 0 <= evidence.start_offset < evidence.end_offset <= len(representation)
        and representation[evidence.start_offset : evidence.end_offset] == evidence.quote
    )


def parse_text(raw: bytes) -> str:
    if len(raw) > 20 * 1024 * 1024:
        raise ValueError("source exceeds 20 MiB")
    text = raw.decode("utf-8-sig", errors="strict")
    return text.replace("\r\n", "\n").replace("\r", "\n")
