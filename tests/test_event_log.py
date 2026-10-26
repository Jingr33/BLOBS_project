from datetime import datetime

from blobs_project.backend.events import EventLog, EventSeverity


def test_entries_are_kept_in_order_with_wall_clock_time() -> None:
    log = EventLog()

    first = log.append(EventSeverity.INFO, "regulation started")
    second = log.append(EventSeverity.FAULT, "emergency stop")

    entries = log.entries
    assert [entry.message for entry in entries] == [
        "regulation started",
        "emergency stop",
    ]
    assert entries[0].severity is EventSeverity.INFO
    assert entries[1].severity is EventSeverity.FAULT
    assert entries[0].occurred_at <= entries[1].occurred_at
    assert isinstance(first.occurred_at, datetime)
    assert second.message == "emergency stop"


def test_log_drops_the_oldest_entries_beyond_the_limit() -> None:
    log = EventLog(limit=2)

    for index in range(3):
        log.append(EventSeverity.INFO, f"event {index}")

    assert [entry.message for entry in log.entries] == ["event 1", "event 2"]


def test_clear_empties_the_log() -> None:
    log = EventLog()
    log.append(EventSeverity.WARNING, "overflow")

    log.clear()

    assert log.entries == ()
