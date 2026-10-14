"""Microsoft Graph application-authenticated meeting transcripts."""

import time
from urllib.parse import quote, urlsplit

from pydantic import BaseModel, SecretStr

from app.connectors.http import ConnectorError, VendorHTTP


class TeamsCredentials(BaseModel):
    directory_id: str
    client_id: str
    client_secret: SecretStr


class TeamsClient:
    ROOT = "https://graph.microsoft.com/v1.0"

    def __init__(self, credentials: TeamsCredentials, http: VendorHTTP | None = None):
        self.credentials = credentials
        self.http = http or VendorHTTP()
        self._token = None
        self._expires_at = 0

    def _headers(self):
        if self._expires_at <= time.time():
            response = self.http.request(
                "POST",
                "https://login.microsoftonline.com/"
                + quote(self.credentials.directory_id, safe="")
                + "/oauth2/v2.0/token",
                retry_safe=True,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.credentials.client_id,
                    "client_secret": self.credentials.client_secret.get_secret_value(),
                    "scope": "https://graph.microsoft.com/.default",
                },
            )
            data = self.http.json(response)
            if not isinstance(data.get("access_token"), str):
                raise ConnectorError("INVALID_TOKEN_RESPONSE")
            try:
                lifetime = int(data.get("expires_in", 300))
            except ValueError, TypeError:
                raise ConnectorError("INVALID_TOKEN_RESPONSE") from None
            self._token = data["access_token"]
            self._expires_at = time.time() + max(0, lifetime - 60)
        return {"Authorization": f"Bearer {self._token}"}

    def _meeting(self, organizer_id: str, meeting_id: str):
        return f"{self.ROOT}/users/{quote(organizer_id, safe='')}/onlineMeetings/" + quote(
            meeting_id, safe=""
        )

    def transcripts(self, organizer_id: str, meeting_id: str) -> list[dict]:
        url = self._meeting(organizer_id, meeting_id) + "/transcripts"
        records = []
        seen = set()
        for _ in range(20):
            parsed = urlsplit(url)
            if (
                parsed.scheme != "https"
                or parsed.netloc != "graph.microsoft.com"
                or not parsed.path.startswith("/v1.0/")
                or url in seen
            ):
                raise ConnectorError("INVALID_PAGINATION")
            seen.add(url)
            data = self.http.json(
                self.http.request("GET", url, headers=self._headers(), retry_safe=True)
            )
            values = data.get("value")
            if not isinstance(values, list) or any(
                not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in values
            ):
                raise ConnectorError("INVALID_VENDOR_RESPONSE")
            records.extend(values)
            url = data.get("@odata.nextLink")
            if not url:
                return records
            if not isinstance(url, str):
                raise ConnectorError("INVALID_PAGINATION")
        raise ConnectorError("PAGINATION_LIMIT")

    def transcript(self, organizer_id: str, meeting_id: str, transcript_id: str) -> bytes:
        url = self._meeting(organizer_id, meeting_id)
        url += "/transcripts/" + quote(transcript_id, safe="") + "/content"
        response = self.http.request(
            "GET", url, headers={**self._headers(), "Accept": "text/vtt"}, retry_safe=True
        )
        try:
            text = response.content.decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError:
            raise ConnectorError("INVALID_TRANSCRIPT_ENCODING") from None
        if not text.lstrip().startswith("WEBVTT"):
            raise ConnectorError("INVALID_TRANSCRIPT_FORMAT")
        return text.encode("utf-8")
