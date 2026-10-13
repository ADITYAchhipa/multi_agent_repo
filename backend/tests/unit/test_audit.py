import base64

import pytest

from app.config import PublicKeyConfig, Settings
from app.promise_seal.canonicalize import canonical_bytes, digest
from app.services.audit import SNAPSHOT_ATTEMPTS, verify_audit_chain, verify_stable_audit


@pytest.mark.parametrize("damage", [None, "signature", "missing", "rewound_head"])
def test_single_pass_audit_stream(keys, damage, tmp_path):
    private, trusted, _ = keys
    settings = Settings(
        signing_issuer_id=trusted.issuer_id,
        signing_key_id=trusted.key_id,
        signing_private_key_path=tmp_path / "unused.pem",
        public_keys=[
            PublicKeyConfig(
                tenant_id=trusted.tenant_id,
                issuer_id=trusted.issuer_id,
                key_id=trusted.key_id,
                public_key_base64url=base64.urlsafe_b64encode(
                    private.public_key().public_bytes_raw()
                )
                .rstrip(b"=")
                .decode(),
            )
        ],
    )
    rows = []
    previous = None
    for sequence in range(1, 4):
        payload = {
            "event_id": f"audit-{sequence}",
            "tenant_id": trusted.tenant_id,
            "sequence": sequence,
            "prev_event_hash": previous,
            "signing_key_id": trusted.key_id,
            "event_type": "TEST_EVENT",
        }
        raw = canonical_bytes(payload)
        event_hash = digest(payload)
        signature = base64.urlsafe_b64encode(private.sign(raw)).rstrip(b"=").decode()
        rows.append(
            [
                payload["event_id"],
                sequence,
                raw.decode(),
                event_hash,
                previous,
                signature,
                trusted.key_id,
                payload["event_type"],
            ]
        )
        previous = event_hash
    state = [3, previous]
    if damage == "signature":
        rows[1][5] = "A" * 86
    elif damage in {"missing", "rewound_head"}:
        rows.pop()
        if damage == "rewound_head":
            state = [2, rows[-1][3]]
    expected = "INVALID" if damage in {"signature", "missing"} else "VALID"
    result, checks, limitations = verify_audit_chain(
        settings, trusted.tenant_id, state, iter(rows), collect_checks=False
    )
    assert result == expected
    assert len(checks) <= 1
    assert "No independently trusted external checkpoint" in limitations[0]


def test_changing_audit_boundaries_exhaust_retries_without_invalid():
    class ChangingRepository:
        reads = 0

        def audit_chain(self, _tenant):
            self.reads += 1
            return [0, None, self.reads], iter(())

        def audit_boundary(self, _tenant):
            return [0, None, self.reads + 1]

    repository = ChangingRepository()
    _, result, checks, limitations = verify_stable_audit(Settings(), repository, "tenant-demo")
    assert repository.reads == SNAPSHOT_ATTEMPTS
    assert result == "INDETERMINATE"
    assert checks == []
    assert "changed during audit verification" in limitations[-1]
