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


@pytest.fixture
def proposal_system(tmp_path):
    if os.environ.get("RUN_FALKORDB_INTEGRATION") != "1":
        pytest.skip("set RUN_FALKORDB_INTEGRATION=1 with a disposable FalkorDB server")
    db = FalkorDB(host="127.0.0.1", port=16379, socket_timeout=3)
    graph = db.select_graph("spike_" + uuid4().hex)
    private = Ed25519PrivateKey.generate()
    key_path = tmp_path / "key.pem"
    key_path.write_bytes(
        private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    settings = Settings(
        falkordb_port=16379,
        falkordb_graph=graph.name,
        tenant_graphs={"tenant-demo": graph.name, "tenant-other": graph.name},
        source_storage_root=tmp_path / "sources",
        demo_users={
            "reviewer": DemoUser(
                credential="reviewer-credential", tenant_id="tenant-demo", roles={"reviewer"}
            ),
            "other-reviewer": DemoUser(
                credential="other-reviewer-credential", tenant_id="tenant-other", roles={"reviewer"}
            ),
            "admin": DemoUser(
                credential="admin-credential", tenant_id="tenant-demo", roles={"admin"}
            ),
            "other": DemoUser(
                credential="other-credential", tenant_id="tenant-other", roles={"viewer"}
            ),
        },
        session_secret="test-session-secret-with-sufficient-length",
        signing_private_key_path=key_path,
        signing_key_id="test-key",
        signing_issuer_id="demo",
        public_keys=[
            PublicKeyConfig(
                tenant_id="tenant-demo",
                issuer_id="demo",
                key_id="test-key",
                public_key_base64url=base64.urlsafe_b64encode(
                    private.public_key().public_bytes_raw()
                )
                .rstrip(b"=")
                .decode(),
            )
        ],
    )
    try:
        graph.query(
            "CREATE (:GraphState {id:'graph-state',tenant_id:'tenant-demo',revision:0,"
            "audit_sequence:0,ontology_version:'v1',policy_version:'v1'})"
        )
        with TestClient(create_app(settings)) as client:
            assert (
                client.post("/api/session", json={"credential": "admin-credential"}).status_code
                == 200
            )
            yield client, graph
    finally:
        graph.delete()
        db.close()
