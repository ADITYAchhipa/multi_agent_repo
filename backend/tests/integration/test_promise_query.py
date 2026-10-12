import base64
import os
from uuid import uuid4

import pytest
from falkordb import FalkorDB
from fastapi.testclient import TestClient

from app.config import DemoUser, PublicKeyConfig, Settings
from app.ingestion.artifacts import ArtifactStore
from app.main import create_app
from app.promise_seal.canonicalize import canonical_bytes
from app.promise_seal.crypto import sign

pytestmark = pytest.mark.integration


def test_promise_list_is_tenant_scoped_and_cursor_bound(payload, keys, tmp_path):
    if os.environ.get("RUN_FALKORDB_INTEGRATION") != "1":
        pytest.skip("set RUN_FALKORDB_INTEGRATION=1 with a real disposable FalkorDB server")
    db = FalkorDB(host="127.0.0.1", port=16379, socket_timeout=3)
    name = "spike_" + uuid4().hex
    graph = db.select_graph(name)
    try:
        private, trusted, _ = keys
        receipt = sign(payload, private, trusted)
        evidence = payload.source_refs[0]
        graph.query(
            "CREATE (:GraphState {id:'graph-state',tenant_id:$tenant,revision:1})",
            {"tenant": "tenant-demo"},
        )
        graph.query(
            "CREATE (p:Promise {id:$id,tenant_id:$tenant,access_label:'PUBLIC_DEMO',"
            "current_version_id:$version,current_state:'PROPOSED',revision:1})"
            "-[e:HAS_VERSION {id:$edge,tenant_id:$tenant,access_label:'PUBLIC_DEMO',"
            "status:'ACTIVE'}]->"
            "(v:PromiseVersion {id:$version,tenant_id:$tenant,access_label:'PUBLIC_DEMO',"
            "receipt_standing:'ACTIVE',deliverable:$deliverable,deadline_text:'Friday',"
            "scope_status:'UNKNOWN'})",
            {
                "id": "promise-a",
                "tenant": "tenant-demo",
                "version": "receipt-a",
                "edge": "edge-a",
                "deliverable": "Loyalty integration",
            },
        )
        graph.query(
            "CREATE (p:Promise {id:$id,tenant_id:$tenant,access_label:'PUBLIC_DEMO',"
            "current_version_id:$version,current_state:'PROPOSED',revision:1,"
            "customer_id:$customer,project_id:$project})"
            "-[:HAS_VERSION {id:'edge-loyalty',tenant_id:$tenant,"
            "access_label:'PUBLIC_DEMO',status:'ACTIVE'}]->"
            "(v:PromiseVersion {id:$version,tenant_id:$tenant,"
            "access_label:'PUBLIC_DEMO',receipt_standing:'ACTIVE',version:1,"
            "status_at_issuance:'PROPOSED',deliverable:$deliverable,"
            "deadline_text:'Friday',scope_status:'UNKNOWN',payload_json:$payload,"
            "payload_hash:$hash,signature:$signature})",
            {
                "id": payload.promise_id,
                "tenant": payload.tenant_id,
                "version": payload.receipt_id,
                "customer": payload.customer_id,
                "project": payload.project_id,
                "deliverable": payload.deliverable,
                "payload": canonical_bytes(payload.model_dump(mode="json")).decode(),
                "hash": receipt.payload_sha256,
                "signature": receipt.signature_base64url,
            },
        )
        graph.query(
            "CREATE (s:SourceRecord {id:$source,tenant_id:$tenant,"
            "access_label:'PUBLIC_DEMO'})"
            "-[:HAS_SOURCE_VERSION {id:'edge-source',tenant_id:$tenant,"
            "access_label:'PUBLIC_DEMO',status:'ACTIVE'}]->"
            "(:SourceVersion {id:$version,tenant_id:$tenant,"
            "access_label:'PUBLIC_DEMO',content_hash:$source_hash,"
            "representation_hash:$representation_hash,availability:'AVAILABLE'})",
            {
                "source": evidence.source_id,
                "tenant": payload.tenant_id,
                "version": evidence.source_version_id,
                "source_hash": evidence.source_hash,
                "representation_hash": evidence.representation_hash,
            },
        )
        graph.query(
            "CREATE (:Promise {id:'promise-other',tenant_id:'other',"
            "access_label:'PUBLIC_DEMO',current_version_id:'other-v1',"
            "current_state:'PROPOSED',revision:1})"
            "-[:HAS_VERSION {id:'other-edge',tenant_id:'other',"
            "access_label:'PUBLIC_DEMO',status:'ACTIVE'}]->"
            "(:PromiseVersion {id:'other-v1',tenant_id:'other',"
            "access_label:'PUBLIC_DEMO',receipt_standing:'ACTIVE',"
            "deliverable:'Private',deadline_text:'Friday'})"
        )
        settings = Settings(
            falkordb_port=16379,
            falkordb_graph=name,
            tenant_graphs={"tenant-demo": name},
            demo_users={
                "actor-viewer": DemoUser(
                    credential="test-credential", tenant_id="tenant-demo", roles={"viewer"}
                )
            },
            session_secret="test-session-secret-with-sufficient-length",
            source_storage_root=tmp_path / "sources",
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
        store = ArtifactStore(settings.source_storage_root)
        store.save_text("tenant-demo", payload.statement.exact_excerpt.encode())
        with TestClient(create_app(settings)) as client:
            assert client.get("/api/promises").status_code == 401
            client.post("/api/session", json={"credential": "test-credential"})
            response = client.get("/api/promises", params={"limit": 1})
            assert response.status_code == 200, response.text
            assert [item["id"] for item in response.json()["items"]] == ["promise-a"]
            assert response.json()["items"][0]["deliverable"] == "Loyalty integration"
            assert response.json()["next_cursor"] is not None
            next_page = client.get(
                "/api/promises", params={"limit": 1, "cursor": response.json()["next_cursor"]}
            )
            assert [item["id"] for item in next_page.json()["items"]] == ["promise-loyalty"]
            assert (
                client.get(
                    "/api/promises",
                    params={"cursor": response.json()["next_cursor"], "status": "CONFIRMED"},
                ).status_code
                == 400
            )
            detail = client.get("/api/promises/promise-loyalty")
            assert detail.status_code == 200, detail.text
            assert detail.json()["receipt"]["payload_sha256"] == receipt.payload_sha256
            assert detail.json()["graph_paths"][0]["edge_ids"] == ["edge-loyalty"]
            verification = client.get("/api/promises/promise-loyalty/verify")
            assert verification.status_code == 200, verification.text
            assert verification.json()["verification"]["integrity"] == "VALID"
            assert verification.json()["verification"]["eligible_for_action"] is False
            assert verification.json()["verification"]["source_results"][0]["result"] == "MATCH"
            copy = receipt.model_dump(mode="json")
            copy["payload"]["deliverable"] = "Unapproved free work"
            copy_result = client.post("/api/receipts/verify", json={"receipt": copy})
            assert copy_result.status_code == 200, copy_result.text
            assert copy_result.json()["verification"]["integrity"] == "INVALID"
            artifact_path = store._path("tenant-demo", evidence.source_hash, "raw")
            artifact_path.write_bytes(b"tampered bytes")
            mismatched_source = client.get("/api/promises/promise-loyalty/verify")
            assert mismatched_source.json()["verification"]["source_results"][0]["result"] == (
                "MISMATCH"
            )
            artifact_path.write_bytes(payload.statement.exact_excerpt.encode())
            altered = (
                canonical_bytes(payload.model_dump(mode="json"))
                .decode()
                .replace(
                    '"deliverable":"Loyalty integration"',
                    '"deliverable":"Unapproved free work"',
                )
            )
            graph.query(
                "MATCH (v:PromiseVersion {id:$id,tenant_id:$tenant}) SET v.payload_json=$payload",
                {"id": payload.receipt_id, "tenant": payload.tenant_id, "payload": altered},
            )
            tampered = client.get("/api/promises/promise-loyalty/verify")
            assert tampered.status_code == 200
            assert tampered.json()["verification"]["integrity"] == "INVALID"
            assert client.get("/api/promises/promise-other").status_code == 404
    finally:
        graph.delete()
        db.close()
