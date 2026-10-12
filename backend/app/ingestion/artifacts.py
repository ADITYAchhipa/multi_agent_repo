"""Content-addressed local source artifacts; graph records are the authoritative index."""

import hashlib
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.ingestion.quote_verifier import parse_text


@dataclass(frozen=True)
class StoredArtifact:
    raw_hash: str
    representation_hash: str
    representation: str


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def _path(self, tenant_id: str, digest: str, kind: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", tenant_id):
            raise ValueError("invalid tenant ID")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("invalid artifact digest")
        if kind not in {"raw", "representation"}:
            raise ValueError("invalid artifact kind")
        return self.root / tenant_id / digest[:2] / f"{digest}.{kind}"

    def _save_one(self, tenant_id: str, digest: str, kind: str, content: bytes) -> None:
        target = self._path(tenant_id, digest, kind)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.parent.resolve().is_relative_to(self.root):
            raise ValueError("artifact path escapes configured root")
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError("stored artifact hash mismatch")
            return
        fd, temporary = tempfile.mkstemp(prefix=".staged-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def save_text(self, tenant_id: str, raw: bytes) -> StoredArtifact:
        representation = parse_text(raw)
        raw_hash = hashlib.sha256(raw).hexdigest()
        representation_bytes = representation.encode("utf-8")
        representation_hash = hashlib.sha256(representation_bytes).hexdigest()
        self._save_one(tenant_id, raw_hash, "raw", raw)
        self._save_one(tenant_id, representation_hash, "representation", representation_bytes)
        return StoredArtifact(raw_hash, representation_hash, representation)

    def read(self, tenant_id: str, digest: str, kind: str) -> bytes:
        target = self._path(tenant_id, digest, kind)
        if not target.parent.resolve().is_relative_to(self.root):
            raise ValueError("artifact path escapes configured root")
        content = target.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError("stored artifact hash mismatch")
        return content
