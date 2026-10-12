import pytest
from pydantic import ValidationError

from app.config import Settings


def test_secret_redaction():
    settings = Settings(falkordb_password="secret-canary")
    assert "secret-canary" not in repr(settings)
    assert "secret-canary" not in settings.model_dump_json()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"app_env": "production"},
        {"falkordb_port": 0},
        {"falkordb_query_timeout_ms": 0},
        {"falkordb_host": "remote.example"},
        {"frontend_origins": ["*"]},
        {"frontend_origins": ["https://user:secret@web.example"]},
        {"frontend_origins": ["http://web.example/path"]},
        {"falkordb_graph": "other; DELETE n"},
    ],
)
def test_invalid_configuration(kwargs):
    with pytest.raises(ValidationError):
        Settings(**kwargs)


def test_environment_parsing(monkeypatch):
    monkeypatch.setenv("FALKORDB_PORT", "16379")
    monkeypatch.setenv("FRONTEND_ORIGINS", '["http://localhost:3001"]')
    settings = Settings()
    assert settings.falkordb_port == 16379
    assert settings.frontend_origins == ["http://localhost:3001"]
