import base64
import os
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from falkordb import FalkorDB
from fastapi.testclient import TestClient

from app.config import DemoUser, PublicKeyConfig, Settings
from app.main import create_app

pytestmark = pytest.mark.integration


def test_text_upload_retention_versioning_and_idempotency(tmp_path):
    if os.environ.get("RUN_FALKORDB_INTEGRATION") != "1":
        pytest.skip("set RUN_FALKORDB_INTEGRATION=1 with a real disposable FalkorDB server")
    db = FalkorDB(host="127.0.0.1", port=16379, socket_timeout=3)
    name = "spike_" + uuid4().hex
    graph = db.select_graph(name)
    private = Ed25519PrivateKey.generate()
    key_path = tmp_path / "signing.pem"
    key_path.write_bytes(
        private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    try:
        graph.query(
            "CREATE (:GraphState {id:'graph-state',tenant_id:'tenant-demo',revision:0,"
            "audit_sequence:0,ontology_version:'v1',policy_version:'v1',"
            "access_label:'PUBLIC_DEMO',acl_principals_json:'[]',"
            "created_at:'2026-10-12T00:00:00.000Z',updated_at:'2026-10-12T00:00:00.000Z'})"
        )
        settings = Settings(
            falkordb_port=16379,
            falkordb_graph=name,
            tenant_graphs={"tenant-demo": name},
            source_storage_root=tmp_path / "sources",
            demo_users={
                "actor-admin": DemoUser(
                    credential="admin-local-credential", tenant_id="tenant-demo", roles={"admin"}
                ),
                "actor-viewer": DemoUser(
                    credential="viewer-local-credential", tenant_id="tenant-demo", roles={"viewer"}
                ),
            },
            session_secret="test-session-secret-with-sufficient-length",
            signing_private_key_path=key_path,
            signing_key_id="test-key",
            signing_issuer_id="promiseops-demo",
            public_keys=[
                PublicKeyConfig(
                    tenant_id="tenant-demo",
                    issuer_id="promiseops-demo",
                    key_id="test-key",
                    public_key_base64url=base64.urlsafe_b64encode(
                        private.public_key().public_bytes_raw()
                    )
                    .rstrip(b"=")
                    .decode(),
                )
            ],
        )
        with TestClient(create_app(settings)) as client:
            assert (
                client.post(
                    "/api/sources/upload",
                    data={"source_type": "NOTES", "access_label": "PUBLIC_DEMO"},
                    files={"file": ("note.txt", b"hello", "text/plain")},
                    headers={"Idempotency-Key": "unauth-key-123456"},
                ).status_code
                == 401
            )
            client.post("/api/session", json={"credential": "admin-local-credential"})

            def upload(raw: bytes, key: str):
                return client.post(
                    "/api/sources/upload",
                    data={
                        "source_type": "NOTES",
                        "access_label": "PUBLIC_DEMO",
                        "source_key": "northstar-demo-note",
                    },
                    files={"file": ("note.txt", raw, "text/plain")},
                    headers={"Idempotency-Key": key},
                )

            original = b"A promise\r\nby Friday."
            first = upload(original, "first-upload-key-123")
            assert first.status_code == 202, first.text
            first_body = first.json()
            source_id = first_body["source_id"]
            replay = upload(original, "first-upload-key-123")
            assert replay.status_code == 202
            assert replay.json()["operation_id"] == first_body["operation_id"]
            assert replay.json()["request_id"] == replay.headers["X-Request-ID"]
            repeat = upload(original, "second-upload-key-123")
            assert repeat.status_code == 200, repeat.text
            assert repeat.json()["outcome"] == "NO_CHANGE"
            assert upload(b"Changed content", "first-upload-key-123").status_code == 409
            detail = client.get(f"/api/sources/{source_id}")
            assert detail.status_code == 200, detail.text
            assert len(detail.json()["versions"]) == 1
            operation = client.get(first_body["status_url"])
            assert operation.status_code == 200, operation.text
            assert operation.json()["operation"]["status"] == "SUCCEEDED"
            updated = upload(b"A revised promise.", "third-upload-key-123")
            assert updated.status_code == 202, updated.text
            assert (
                client.post(
                    "/api/sources/upload",
                    data={
                        "source_type": "NOTES",
                        "access_label": "RESTRICTED",
                        "source_key": "northstar-demo-note",
                    },
                    files={"file": ("note.txt", b"changed access", "text/plain")},
                    headers={"Idempotency-Key": "fourth-upload-key-123"},
                ).status_code
                == 409
            )
            assert (
                client.post(
                    "/api/sources/upload",
                    data={"source_type": "NOTES", "access_label": "PUBLIC_DEMO"},
                    files={"file": ("bad.pdf", b"not a pdf", "application/pdf")},
                    headers={"Idempotency-Key": "bad-file-key-12345"},
                ).status_code
                == 415
            )
            detail2 = client.get(f"/api/sources/{source_id}")
            assert len(detail2.json()["versions"]) == 2
            assert detail2.json()["source"]["current_version_id"].endswith("-v2")
            assert graph.ro_query("MATCH (a:AuditEvent) RETURN count(a)").result_set == [[2]]
            assert graph.ro_query("MATCH (s:GraphState) RETURN s.revision").result_set == [[2]]
            audit = client.get("/api/audit/verify")
            assert audit.status_code == 200, audit.text
            assert audit.json()["chain_result"] == "VALID"
            assert audit.json()["checkpoint"]["available"] is False
            graph.query(
                "MATCH (a:AuditEvent {sequence:2,tenant_id:'tenant-demo'}) "
                "SET a.event_hash='tampered'"
            )
            assert client.get("/api/audit/verify").json()["chain_result"] == "INVALID"
            client.post("/api/session", json={"credential": "viewer-local-credential"})
            assert (
                client.post(
                    "/api/sources/upload",
                    data={"source_type": "NOTES", "access_label": "PUBLIC_DEMO"},
                    files={"file": ("note.txt", b"forbidden", "text/plain")},
                    headers={"Idempotency-Key": "viewer-upload-key-123"},
                ).status_code
                == 403
            )
            assert client.get("/api/audit/verify").status_code == 403
    finally:
        graph.delete()
        db.close()
