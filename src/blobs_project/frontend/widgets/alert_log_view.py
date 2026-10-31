from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from blobs_project import config
from blobs_project.backend.events import EventEntry, EventSeverity
from blobs_project.frontend.helpers.qt_helper import QtHelper
from blobs_project.translations import tr

SEVERITY_COLORS: dict[EventSeverity, str] = {
    EventSeverity.INFO: config.TEXT,
    EventSeverity.WARNING: config.STATE_WARNING,
    EventSeverity.FAULT: config.STATE_ALARM,
}


class AlertLogView(QWidget):
    """Event log table: time and severity-coloured message of every event."""

    def __init__(self) -> None:
        super().__init__()
        self._entries: tuple[EventEntry, ...] = ()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        title_container = QWidget()
        title_container.setObjectName("alertTitle")
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(12, 8, 12, 0)
        title_layout.addWidget(QtHelper.make_label(tr("alerts.title"), "muted"))
        layout.addWidget(title_container)
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels([tr("alerts.time"), tr("alerts.message")])
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        rows, columns = self._table.verticalHeader(), self._table.horizontalHeader()
        if rows is not None and columns is not None:
            rows.setVisible(False)
            columns.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table, 1)

    @property
    def table(self) -> QTableWidget:
        return self._table

    def set_entries(self, entries: tuple[EventEntry, ...]) -> None:
        """Show ``entries``; nothing is redrawn if they did not change."""
        if entries == self._entries:
            return
        self._entries = entries
        self._table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            time_item = QTableWidgetItem(entry.occurred_at.strftime("%H:%M:%S"))
            message_item = QTableWidgetItem(entry.message)
            message_item.setForeground(QColor(SEVERITY_COLORS[entry.severity]))
            self._table.setItem(row, 0, time_item)
            self._table.setItem(row, 1, message_item)
        self._table.scrollToBottom()
