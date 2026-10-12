from fastapi.testclient import TestClient

from app.config import DemoUser, Settings
from app.main import create_app


class OfflineGraph:
    def ready(self):
        return False

    def close(self):
        pass


def settings():
    return Settings(
        demo_users={
            "actor-viewer": DemoUser(
                credential="local-secret-for-test", tenant_id="tenant-demo", roles={"viewer"}
            )
        },
        session_secret="test-session-secret-with-sufficient-length",
    )


def test_session_bootstrap_and_authentication():
    with TestClient(create_app(settings(), OfflineGraph())) as client:
        assert client.get("/api/session").status_code == 401
        bad = client.post("/api/session", json={"credential": "wrong"})
        assert bad.status_code == 401
        result = client.post("/api/session", json={"credential": "local-secret-for-test"})
        assert result.status_code == 200
        assert result.json()["actor"] == {"id": "actor-viewer", "roles": ["viewer"]}
        assert result.json()["request_id"] == result.headers["X-Request-ID"]
        assert "httponly" in result.headers["set-cookie"].lower()
        assert client.get("/api/session").json()["actor"]["id"] == "actor-viewer"


def test_session_rejects_cross_origin_and_tampering():
    with TestClient(create_app(settings(), OfflineGraph())) as client:
        assert (
            client.post(
                "/api/session",
                json={"credential": "local-secret-for-test"},
                headers={"Origin": "https://evil.example"},
            ).status_code
            == 403
        )
        client.cookies.set("promiseops_session", "forged.token", path="/api")
        assert client.get("/api/session").status_code == 401
