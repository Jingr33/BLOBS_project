from PyQt6.QtCore import QDate, QTime, QTimer
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from blobs_project import config
from blobs_project.frontend.helpers.qt_helper import QtHelper


class ClockWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._time_label = QtHelper.make_label("", "clockTime")
        self._date_label = QtHelper.make_label("", "clockDate")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._time_label)
        layout.addWidget(self._date_label)
        self._timer = QTimer(self)
        self._timer.setInterval(config.CLOCK_INTERVAL_MS)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()
        self._refresh()

    def _refresh(self) -> None:
        self._time_label.setText(QTime.currentTime().toString("HH:mm:ss"))
        self._date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))
