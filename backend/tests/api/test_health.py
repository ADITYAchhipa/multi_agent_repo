from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class Probe:
    def __init__(self, available):
        self.available = available
        self.closed = False
        self.calls = 0

    def ready(self):
        self.calls += 1
        return self.available

    def close(self):
        self.closed = True


def test_health_contract_and_lifecycle():
    probe = Probe(True)
    with TestClient(create_app(Settings(), probe)) as client:
        response = client.get("/api/health", headers={"X-Request-ID": "correlation/example"})
        assert response.status_code == 200
        assert (
            response.json()["request_id"]
            == response.headers["X-Request-ID"]
            == "correlation/example"
        )
        assert set(response.json()) == {"request_id", "status", "services", "checked_at"}
        assert response.json()["services"] == {"api": "OK", "graph": "OK"}
    assert probe.closed


def test_unready_is_503_and_liveness_does_not_query_graph():
    probe = Probe(False)
    with TestClient(create_app(Settings(), probe)) as client:
        live = client.get("/internal/live")
        assert live.status_code == 200 and probe.calls == 0
        response = client.get("/api/health")
        assert response.status_code == 503
        assert response.json()["status"] == "DEGRADED"
        assert "company_demo" not in response.text


def test_safe_errors_and_request_id():
    with TestClient(create_app(Settings(), Probe(False))) as client:
        response = client.get("/not-a-route", headers={"X-Request-ID": "a" * 65})
        assert response.status_code == 404
        assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
        assert response.headers["X-Request-ID"] != "a" * 65
        assert response.json()["error"]["code"] == "NOT_FOUND"
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_internal_exception_has_no_secret_or_traceback():
    class Broken(Probe):
        def ready(self):
            raise RuntimeError("secret-token-canary")

    with TestClient(create_app(Settings(), Broken(False))) as client:
        response = client.get("/api/health")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_ERROR"
        assert "secret-token-canary" not in response.text
        assert "Traceback" not in response.text


def test_cors_explicit_origins_only():
    with TestClient(create_app(Settings(), Probe(True))) as client:
        good = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
        bad = client.get("/api/health", headers={"Origin": "https://evil.example"})
        assert good.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert "access-control-allow-origin" not in bad.headers
