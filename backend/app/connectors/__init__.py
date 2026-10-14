"""Real vendor clients; configuration and authorization belong to the calling service."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Connection:
    client: Any
    organizer_id: str | None = None
    meeting_id: str | None = None
