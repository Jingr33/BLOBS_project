from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QLabel, QWidget


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
    def set_style_name(widget: QWidget, name: str) -> None:
        """Give ``widget`` a new object name and re-apply the stylesheet to it."""
        widget.setObjectName(name)
        style = widget.style()
        if style is not None:
            style.unpolish(widget)
            style.polish(widget)
