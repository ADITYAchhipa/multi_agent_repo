import httpx
import pytest

from app.connectors.http import ConnectorError, VendorHTTP
from app.connectors.jira import JiraClient, JiraCredentials
from app.connectors.teams import TeamsClient, TeamsCredentials


def transport(handler):
    return VendorHTTP(httpx.Client(transport=httpx.MockTransport(handler)), sleep=lambda _: None)


def jira(handler):
    return JiraClient(
        JiraCredentials(
            base_url="https://demo.atlassian.net",
            email="test@example.test",
            api_token="private-token",
        ),
        transport(handler),
    )


def teams(handler):
    return TeamsClient(
        TeamsCredentials(
            directory_id="directory", client_id="client", client_secret="private-secret"
        ),
        transport(handler),
    )


def test_teams_token_discovery_and_transcript_preserves_evidence():
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.host == "login.microsoftonline.com":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        assert request.headers["Authorization"] == "Bearer token"
        if request.url.path.endswith("/content"):
            return httpx.Response(
                200, content=b"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nWe will ship."
            )
        return httpx.Response(200, json={"value": [{"id": "transcript"}]})

    client = teams(handler)
    assert client.transcripts("user", "meeting") == [{"id": "transcript"}]
    assert b"We will ship." in client.transcript("user", "meeting", "transcript")
    assert len(calls) == 3  # Token reused, never printed.


def test_teams_rejects_credential_exfiltration_nextlink():
    def handler(request):
        if request.url.host == "login.microsoftonline.com":
            return httpx.Response(200, json={"access_token": "token"})
        return httpx.Response(200, json={"value": [], "@odata.nextLink": "https://evil.test/"})

    with pytest.raises(ConnectorError, match="INVALID_PAGINATION"):
        teams(handler).transcripts("user", "meeting")


def test_jira_search_paginates_new_api():
    calls = []

    def handler(request):
        calls.append(request)
        assert request.url.path == "/rest/api/3/search/jql"
        return httpx.Response(
            200,
            json={
                "issues": [{"id": str(len(calls)), "fields": {}}],
                "nextPageToken": "next" if len(calls) == 1 else None,
            },
        )

    assert len(jira(handler).search("project = DEMO")) == 2
    assert b'"nextPageToken":"next"' in calls[1].content


def test_reads_retry_but_writes_do_not_and_errors_are_redacted():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(503, text="private-token secret vendor details")

    client = jira(handler)
    with pytest.raises(ConnectorError) as error:
        client.issue("DEMO-1")
    assert len(calls) == 3
    assert "private-token" not in str(error.value)
    with pytest.raises(ConnectorError):
        client.update_and_readback("DEMO-1", {"duedate": "2026-12-01"})
    assert len(calls) == 4


def test_jira_update_readback_reports_discrepancy():
    calls = []

    def handler(request):
        calls.append(request.method)
        if request.method == "PUT":
            return httpx.Response(204)
        return httpx.Response(
            200, json={"id": "1", "key": "DEMO-1", "fields": {"duedate": "2026-12-02"}}
        )

    result = jira(handler).update_and_readback("DEMO-1", {"duedate": "2026-12-01"})
    assert calls == ["PUT", "GET"]
    assert result["mode"] == "LIVE"
    assert result["reconciled"] is False
    assert result["mismatched_fields"] == ["duedate"]


def test_unsupported_update_never_reaches_vendor():
    def handler(request):
        pytest.fail("must not send")

    with pytest.raises(ConnectorError, match="UNSUPPORTED_UPDATE_FIELDS"):
        jira(handler).update_and_readback("DEMO-1", {"status": "Done"})


def test_invalid_json_is_redacted():
    with pytest.raises(ConnectorError, match="INVALID_VENDOR_RESPONSE"):
        jira(lambda _: httpx.Response(200, text="secret non-json")).issue("DEMO-1")


def test_jira_pagination_cycle_fails_instead_of_truncating():
    with pytest.raises(ConnectorError, match="INVALID_PAGINATION"):
        jira(lambda _: httpx.Response(200, json={"issues": [], "nextPageToken": "same"})).search(
            "x"
        )


def test_redirect_never_receives_vendor_credentials():
    calls = []

    def handler(request):
        calls.append(request.url.host)
        return httpx.Response(302, headers={"Location": "https://evil.test"})

    with pytest.raises(ConnectorError):
        jira(handler).health()
    assert calls == ["demo.atlassian.net"]


def test_connector_router_tenant_role_and_real_import_boundary():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.connectors import Connection, router
    from app.auth import issue_session
    from app.config import DemoUser, Settings

    settings = Settings(
        session_secret="test-session-secret-long-enough",
        demo_users={
            "admin": DemoUser(credential="admin-secret", tenant_id="tenant-demo", roles={"admin"}),
            "viewer": DemoUser(
                credential="viewer-secret", tenant_id="tenant-demo", roles={"viewer"}
            ),
        },
    )

    class Ingest:
        def __init__(self):
            self.calls = []

        def ingest(self, actor, **kwargs):
            self.calls.append((actor, kwargs))
            return 202, {
                "request_id": kwargs["request_id"],
                "source_id": "source-1",
                "operation_id": "op-1",
                "status_url": "/api/operations/op-1",
            }

    service = Ingest()
    adapter = jira(lambda _: httpx.Response(200, json={"issues": [{"id": "1", "fields": {}}]}))
    app = FastAPI()

    @app.middleware("http")
    async def request_id(request, call_next):
        request.state.request_id = "request-1"
        return await call_next(request)

    app.include_router(
        router(
            settings,
            service,
            {
                ("tenant-demo", "jira"): Connection(adapter),
                ("other-tenant", "hidden"): Connection(adapter),
            },
        )
    )
    with TestClient(app) as client:
        assert client.get("/api/connectors").status_code == 401
        client.cookies.set("promiseops_session", issue_session(settings, "viewer")[0])
        assert client.get("/api/connectors").status_code == 403
        client.cookies.set("promiseops_session", issue_session(settings, "admin")[0])
        assert [x["id"] for x in client.get("/api/connectors").json()["items"]] == ["jira"]
        assert client.get("/api/connectors/hidden/health").status_code == 404
        response = client.post(
            "/api/connectors/jira/import",
            json={"jql": "project = DEMO"},
            headers={"Idempotency-Key": "connector-test-0001"},
        )
        assert response.status_code == 202
        assert len(service.calls) == 1
        actor, payload = service.calls[0]
        assert actor.tenant_id == "tenant-demo"
        assert payload["access_label"] == "RESTRICTED"
        assert b'"issues"' in payload["raw"]
        assert payload["idempotency_key"] == "connector-test-0001"
