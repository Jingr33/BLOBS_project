import os
from datetime import datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QTableWidgetItem

from blobs_project import config
from blobs_project.backend.events import EventEntry, EventSeverity
from blobs_project.frontend.widgets.alert_log_view import AlertLogView

# The application must outlive every standalone widget created in these tests.
_APP = QApplication.instance() or QApplication([])


def test_entries_are_rendered_with_time_and_severity_colour() -> None:
    view = AlertLogView()
    entries = (
        EventEntry(
            datetime(2026, 10, 21, 12, 0, 0), EventSeverity.FAULT, "emergency stop"
        ),
        EventEntry(datetime(2026, 10, 21, 12, 1, 0), EventSeverity.WARNING, "overflow"),
        EventEntry(datetime(2026, 10, 21, 12, 2, 0), EventSeverity.INFO, "running"),
    )

    view.set_entries(entries)

    assert view.table.rowCount() == 3
    assert cell(view, 0, 0).text() == "12:00:00"
    assert cell(view, 0, 1).text() == "emergency stop"
    assert cell(view, 0, 1).foreground().color().name() == config.RED
    assert cell(view, 1, 1).foreground().color().name() == config.ORANGE
    assert cell(view, 2, 1).foreground().color().name() == config.TEXT


def test_unchanged_entries_do_not_rebuild_the_rows() -> None:
    view = AlertLogView()
    entries = (
        EventEntry(datetime(2026, 10, 21, 12, 0, 0), EventSeverity.INFO, "started"),
    )

    view.set_entries(entries)
    shown = cell(view, 0, 1)
    view.set_entries(entries)

    assert cell(view, 0, 1) is shown


def cell(view: AlertLogView, row: int, column: int) -> QTableWidgetItem:
    item = view.table.item(row, column)
    assert item is not None
    return item
