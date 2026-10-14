import re
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DemoUser(BaseModel):
    credential: SecretStr
    tenant_id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")
    roles: set[Literal["viewer", "reviewer", "executor", "admin"]]


class PublicKeyConfig(BaseModel):
    tenant_id: str
    issuer_id: str
    key_id: str
    public_key_base64url: str
    trust: Literal["TRUSTED", "RETIRED", "COMPROMISED"] = "TRUSTED"


from app.connectors.registry import ConnectorConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="forbid", hide_input_in_errors=True)

    connectors: list[ConnectorConfig] = []
    app_env: Literal["development", "demo", "production"] = "development"
    demo_mode: bool = True
    falkordb_host: str = Field(default="127.0.0.1", min_length=1)
    falkordb_port: int = Field(default=6379, ge=1, le=65535)
    falkordb_password: SecretStr | None = None
    falkordb_tls: bool = False
    falkordb_graph: str = Field(default="company_demo", pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    tenant_graphs: dict[str, str] = {"tenant-demo": "company_demo"}
    falkordb_query_timeout_ms: int = Field(default=2000, ge=1, le=10000)
    falkordb_socket_timeout_seconds: float = Field(default=3, gt=0, le=15)
    frontend_origins: list[str] = ["http://localhost:3000"]
    debug_docs: bool = False
    demo_users: dict[str, DemoUser] = {}
    session_secret: SecretStr | None = None
    public_keys: list[PublicKeyConfig] = []
    source_storage_root: Path = Path("data/sources")
    signing_private_key_path: Path | None = None
    signing_key_id: str | None = None
    signing_issuer_id: str | None = None

    @model_validator(mode="after")
    def validate_deployment(self) -> Self:
        for tenant_id, graph_name in self.tenant_graphs.items():
            if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", tenant_id):
                raise ValueError("invalid configured tenant ID")
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", graph_name):
                raise ValueError("invalid configured graph name")
        if self.demo_users and not self.session_secret:
            raise ValueError("session_secret is required for demo users")
        if any(user.tenant_id not in self.tenant_graphs for user in self.demo_users.values()):
            raise ValueError("every demo user requires a configured tenant graph")
        signing = (
            self.signing_private_key_path,
            self.signing_key_id,
            self.signing_issuer_id,
        )
        if any(value is not None for value in signing) and any(value is None for value in signing):
            raise ValueError("signing key path, key ID and issuer ID must be configured together")
        for origin in self.frontend_origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path not in {"", "/"}
                or parsed.query
                or parsed.fragment
                or "*" in origin
            ):
                raise ValueError("frontend_origins must contain explicit HTTP(S) origins")
        if self.app_env == "production":
            # Identity, durable graph writes, and deployment gates are not implemented yet.
            raise ValueError("production is disabled until the mandatory acceptance gates pass")
        if self.falkordb_host not in {"localhost", "127.0.0.1", "::1", "falkordb"}:
            if not self.falkordb_tls or not self.falkordb_password:
                raise ValueError("remote FalkorDB requires TLS and authentication")
        return self
