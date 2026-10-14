"""Explicit tenant-owned server configuration; no request-supplied credentials."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.connectors import Connection
from app.connectors.jira import JiraClient, JiraCredentials
from app.connectors.teams import TeamsClient, TeamsCredentials


class ConnectorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    tenant_id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")
    id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")
    kind: Literal["TEAMS", "JIRA"]
    teams: TeamsCredentials | None = None
    jira: JiraCredentials | None = None
    organizer_id: str | None = None
    meeting_id: str | None = None

    @model_validator(mode="after")
    def matching_credentials(self):
        if self.kind == "TEAMS" and (self.teams is None or self.jira is not None):
            raise ValueError("Teams connection requires only Teams credentials")
        if self.kind == "JIRA" and (self.jira is None or self.teams is not None):
            raise ValueError("Jira connection requires only Jira credentials")
        return self


def registry_from_config(raw: list[ConnectorConfig | dict]):
    registry = {}
    for value in raw:
        item = ConnectorConfig.model_validate(value)
        key = (item.tenant_id, item.id)
        if key in registry:
            raise ValueError("duplicate tenant connector ID")
        client = TeamsClient(item.teams) if item.kind == "TEAMS" else JiraClient(item.jira)
        registry[key] = Connection(client, item.organizer_id, item.meeting_id)
    return registry


def build_registry(settings):
    if any(item.tenant_id not in settings.tenant_graphs for item in settings.connectors):
        raise ValueError("connector tenant must have a configured graph")
    return registry_from_config(settings.connectors)
