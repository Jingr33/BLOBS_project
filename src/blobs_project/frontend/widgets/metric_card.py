from __future__ import annotations

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from blobs_project.frontend.helpers.qt_helper import QtHelper


class MetricCard(QWidget):
    """A single process metric: caption on top, numeric value under it."""

    def __init__(self, caption: str) -> None:
        super().__init__()
        self._value_label = QtHelper.make_label("—", "metricValue")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(QtHelper.make_caption(caption))
        layout.addWidget(self._value_label)

    def set_value(self, text: str, color: str = "") -> None:
        """Show ``text``; an empty ``color`` keeps the basic text colour."""
        self._value_label.setText(text)
        self._value_label.setStyleSheet(f"color: {color};" if color else "")
