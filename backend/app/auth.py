"""Local demo sessions. Identity and tenant mapping come only from server configuration."""

import base64
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request

from app.config import Settings

SESSION_SECONDS = 3600


@dataclass(frozen=True)
class Actor:
    id: str
    tenant_id: str
    roles: frozenset[str]
    expires_at: int


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_session(settings: Settings, actor_id: str) -> tuple[str, int]:
    if settings.session_secret is None or actor_id not in settings.demo_users:
        raise ValueError("demo session is not configured")
    expires_at = int(time.time()) + SESSION_SECONDS
    body = json.dumps({"actor_id": actor_id, "exp": expires_at}, separators=(",", ":")).encode()
    signature = hmac.digest(settings.session_secret.get_secret_value().encode(), body, "sha256")
    return f"{_b64(body)}.{_b64(signature)}", expires_at


def authenticate(request: Request, settings: Settings) -> Actor:
    token = request.cookies.get("promiseops_session", "")
    if settings.session_secret is None or len(token) > 1024 or token.count(".") != 1:
        raise HTTPException(401)
    try:
        body64, signature64 = token.split(".")
        body, signature = _decode(body64), _decode(signature64)
        expected = hmac.digest(settings.session_secret.get_secret_value().encode(), body, "sha256")
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        data = json.loads(body)
        if set(data) != {"actor_id", "exp"} or type(data["exp"]) is not int:
            raise ValueError("invalid session")
        actor_id = data["actor_id"]
        if not isinstance(actor_id, str) or data["exp"] <= time.time():
            raise ValueError("expired session")
        user = settings.demo_users.get(actor_id)
        if user is None:
            raise ValueError("unknown actor")
        return Actor(actor_id, user.tenant_id, frozenset(user.roles), data["exp"])
    except ValueError, UnicodeDecodeError, json.JSONDecodeError, base64.binascii.Error:
        raise HTTPException(401) from None


def authenticate_credential(settings: Settings, credential: str) -> str | None:
    # Compare all configured secrets; do not reveal which actor failed.
    matches = [
        actor_id
        for actor_id, user in settings.demo_users.items()
        if hmac.compare_digest(user.credential.get_secret_value(), credential)
    ]
    return matches[0] if len(matches) == 1 else None


def require_role(actor: Actor, role: str) -> None:
    if role not in actor.roles:
        raise HTTPException(403)
