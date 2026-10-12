from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="forbid", hide_input_in_errors=True)

    app_env: Literal["development", "demo", "production"] = "development"
    demo_mode: bool = True
    falkordb_host: str = Field(default="127.0.0.1", min_length=1)
    falkordb_port: int = Field(default=6379, ge=1, le=65535)
    falkordb_password: SecretStr | None = None
    falkordb_tls: bool = False
    falkordb_graph: str = Field(default="company_demo", pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    falkordb_query_timeout_ms: int = Field(default=2000, ge=1, le=10000)
    falkordb_socket_timeout_seconds: float = Field(default=3, gt=0, le=15)
    frontend_origins: list[str] = ["http://localhost:3000"]
    debug_docs: bool = False

    @model_validator(mode="after")
    def validate_deployment(self) -> Self:
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
