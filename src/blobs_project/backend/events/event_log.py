from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from blobs_project import config


class EventSeverity(Enum):
    """Operator-facing severity of a logged run event."""

    INFO = "info"
    WARNING = "warning"
    FAULT = "fault"


@dataclass(frozen=True)
class EventEntry:
    """One logged event: wall-clock time, severity and the shown message."""

    occurred_at: datetime
    severity: EventSeverity
    message: str


class EventLog:
    """Bounded wall-clock log of run events shown on the Alerts tab."""

    def __init__(self, limit: int = config.EVENT_LOG_LIMIT) -> None:
        self._limit = limit
        self._entries: list[EventEntry] = []

    @property
    def entries(self) -> tuple[EventEntry, ...]:
        """Return the logged entries in the order they happened."""
        return tuple(self._entries)

    def append(self, severity: EventSeverity, message: str) -> EventEntry:
        """Log ``message`` and return the stored entry."""
        entry = EventEntry(datetime.now(), severity, message)
        self._entries.append(entry)
        if len(self._entries) > self._limit:
            del self._entries[: len(self._entries) - self._limit]
        return entry

    def clear(self) -> None:
        """Forget every logged entry."""
        self._entries.clear()
