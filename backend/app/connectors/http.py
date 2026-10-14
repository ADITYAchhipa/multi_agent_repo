"""Bounded, redacted HTTP transport. Ambiguous mutations are never retried."""

import time
from collections.abc import Callable
from urllib.parse import urlsplit

import httpx


class ConnectorError(Exception):
    def __init__(self, code: str, status: int | None = None):
        self.code = code
        self.status = status
        super().__init__(code)


class VendorHTTP:
    def __init__(self, client: httpx.Client | None = None, *, sleep: Callable = time.sleep):
        self.client = client or httpx.Client(timeout=20, follow_redirects=False)
        self.sleep = sleep

    def request(self, method: str, url: str, *, retry_safe: bool = False, **kwargs):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.fragment:
            raise ConnectorError("INVALID_VENDOR_URL")
        attempts = 3 if retry_safe else 1
        for attempt in range(attempts):
            try:
                with self.client.stream(method, url, follow_redirects=False, **kwargs) as streamed:
                    content = bytearray()
                    for chunk in streamed.iter_bytes():
                        content.extend(chunk)
                        if len(content) > 20 * 1024 * 1024:
                            raise ConnectorError("RESPONSE_TOO_LARGE")
                    response = httpx.Response(
                        streamed.status_code, headers=streamed.headers, content=bytes(content)
                    )
            except httpx.TransportError:
                if attempt + 1 == attempts:
                    raise ConnectorError("TRANSPORT_FAILURE") from None
                self.sleep(2**attempt)
                continue
            if response.status_code in {429, 502, 503, 504} and attempt + 1 < attempts:
                try:
                    delay = float(response.headers.get("Retry-After", 2**attempt))
                except ValueError:
                    delay = 2**attempt
                self.sleep(max(0, min(delay, 5)))
                continue
            if not 200 <= response.status_code < 300:
                raise ConnectorError("VENDOR_HTTP_ERROR", response.status_code)
            if len(response.content) > 20 * 1024 * 1024:
                raise ConnectorError("RESPONSE_TOO_LARGE")
            return response
        raise ConnectorError("TRANSPORT_FAILURE")

    @staticmethod
    def json(response):
        try:
            data = response.json()
        except ValueError:
            raise ConnectorError("INVALID_VENDOR_RESPONSE") from None
        if not isinstance(data, dict):
            raise ConnectorError("INVALID_VENDOR_RESPONSE")
        return data
