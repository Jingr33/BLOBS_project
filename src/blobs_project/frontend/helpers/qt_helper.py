from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget

from blobs_project.translations import tr


class QtHelper:
    @staticmethod
    def make_label(text: str, object_name: str = "") -> QLabel:
        """Create a QLabel with an optional object name used by the stylesheet."""
        label = QLabel(text)
        if object_name:
            label.setObjectName(object_name)
        return label

    @staticmethod
    def make_caption(text: str) -> QLabel:
        """Create a muted caption label for a metric row."""
        return QtHelper.make_label(text, "muted")

    @staticmethod
    def add_metric_row(grid: QGridLayout, row: int, caption: str) -> QLabel:
        """Add a caption and a right aligned value label and return the value."""
        grid.addWidget(QtHelper.make_caption(caption), row, 0)
        value = QLabel("—")
        value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(value, row, 1)
        return value

    @staticmethod
    def make_button(
        text: str, object_name: str, slot: Callable[[], None]
    ) -> QPushButton:
        """Create a button with an optional object name used by the stylesheet."""
        button = QPushButton(text)
        if object_name:
            button.setObjectName(object_name)
        button.clicked.connect(slot)
        return button

    @staticmethod
    def set_run_button_state(
        button: QPushButton, active: bool, start_key: str, stop_key: str
    ) -> None:
        """Switch a start/stop toggle between its running and idle captions."""
        button.setText(tr(stop_key if active else start_key))
        QtHelper.set_style_name(button, "running" if active else "primary")

    @staticmethod
    def set_style_name(widget: QWidget, name: str) -> None:
        """Give ``widget`` a new object name and re-apply the stylesheet to it."""
        widget.setObjectName(name)
        style = widget.style()
        if style is not None:
            style.unpolish(widget)
            style.polish(widget)
