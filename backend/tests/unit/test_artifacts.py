import hashlib

import pytest

from app.ingestion.artifacts import ArtifactStore


def test_artifact_store_retains_raw_and_normalized_bytes(tmp_path):
    store = ArtifactStore(tmp_path / "sources")
    raw = b"\xef\xbb\xbfFirst\r\nSecond\r"
    item = store.save_text("tenant-demo", raw)
    assert item.raw_hash == hashlib.sha256(raw).hexdigest()
    assert item.representation == "First\nSecond\n"
    assert store.read("tenant-demo", item.raw_hash, "raw") == raw
    assert store.read("tenant-demo", item.representation_hash, "representation") == (
        b"First\nSecond\n"
    )
    assert store.save_text("tenant-demo", raw) == item
    with pytest.raises(ValueError):
        store.read("../other", item.raw_hash, "raw")


def test_artifact_tampering_is_detected(tmp_path):
    store = ArtifactStore(tmp_path / "sources")
    item = store.save_text("tenant-demo", b"original")
    path = store._path("tenant-demo", item.raw_hash, "raw")
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash mismatch"):
        store.read("tenant-demo", item.raw_hash, "raw")
    with pytest.raises(ValueError, match="hash mismatch"):
        store.save_text("tenant-demo", b"original")
