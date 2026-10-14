"""Jira Cloud reads and explicit update/read-back primitive for approved actions."""

from urllib.parse import quote, urlsplit

import httpx
from pydantic import BaseModel, SecretStr, model_validator

from app.connectors.http import ConnectorError, VendorHTTP


class JiraCredentials(BaseModel):
    base_url: str
    email: str | None = None
    api_token: SecretStr | None = None
    oauth_token: SecretStr | None = None

    @model_validator(mode="after")
    def configuration(self):
        parsed = urlsplit(self.base_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Jira base URL must be a configured HTTPS origin or OAuth gateway")
        if bool(self.oauth_token) == bool(self.email and self.api_token):
            raise ValueError("Configure exactly one Jira authentication method")
        return self


class JiraClient:
    FIELDS = ["summary", "status", "assignee", "duedate", "updated", "timetracking"]
    UPDATE_FIELDS = {"summary", "assignee", "duedate", "timetracking"}

    def __init__(self, credentials: JiraCredentials, http: VendorHTTP | None = None):
        self.credentials = credentials
        self.http = http or VendorHTTP()

    def _request(self, method, path, *, retry_safe=False, **kwargs):
        auth = None
        headers = {"Accept": "application/json"}
        if self.credentials.oauth_token:
            headers["Authorization"] = "Bearer " + self.credentials.oauth_token.get_secret_value()
        else:
            auth = httpx.BasicAuth(
                self.credentials.email, self.credentials.api_token.get_secret_value()
            )
        return self.http.request(
            method,
            self.credentials.base_url.rstrip("/") + "/rest/api/3/" + path,
            headers=headers,
            auth=auth,
            retry_safe=retry_safe,
            **kwargs,
        )

    def health(self):
        self._request("GET", "myself", retry_safe=True)

    def issue(self, issue_id: str) -> dict:
        data = self.http.json(
            self._request(
                "GET",
                "issue/" + quote(issue_id, safe=""),
                retry_safe=True,
                params={"fields": ",".join(self.FIELDS)},
            )
        )
        if not isinstance(data.get("id"), str) or not isinstance(data.get("fields"), dict):
            raise ConnectorError("INVALID_VENDOR_RESPONSE")
        return data

    def search(self, jql: str) -> list[dict]:
        if not 1 <= len(jql) <= 4000:
            raise ConnectorError("INVALID_JQL")
        records, seen = [], set()
        token = None
        for _ in range(20):
            body = {"jql": jql, "maxResults": 100, "fields": self.FIELDS}
            if token:
                body["nextPageToken"] = token
            data = self.http.json(self._request("POST", "search/jql", retry_safe=True, json=body))
            issues = data.get("issues")
            if not isinstance(issues, list) or any(
                not isinstance(issue, dict)
                or not isinstance(issue.get("fields"), dict)
                or not isinstance(issue.get("id"), str)
                for issue in issues
            ):
                raise ConnectorError("INVALID_VENDOR_RESPONSE")
            records.extend(issues)
            token = data.get("nextPageToken")
            if not token:
                return records
            if not isinstance(token, str) or token in seen:
                raise ConnectorError("INVALID_PAGINATION")
            seen.add(token)
        raise ConnectorError("PAGINATION_LIMIT")

    def update_and_readback(self, issue_id: str, fields: dict) -> dict:
        """Caller MUST enforce durable approval; no external idempotency is implied."""
        if not fields or set(fields) - self.UPDATE_FIELDS:
            raise ConnectorError("UNSUPPORTED_UPDATE_FIELDS")
        self._request("PUT", "issue/" + quote(issue_id, safe=""), json={"fields": fields})
        observed = self.issue(issue_id)
        mismatches = []
        for key, expected in fields.items():
            actual = observed["fields"].get(key)
            if key == "assignee" and isinstance(expected, dict):
                actual = {"accountId": (actual or {}).get("accountId")}
            if actual != expected:
                mismatches.append(key)
        return {
            "mode": "LIVE",
            "external_reference": observed.get("key", issue_id),
            "observed": observed,
            "reconciled": not mismatches,
            "mismatched_fields": mismatches,
        }
