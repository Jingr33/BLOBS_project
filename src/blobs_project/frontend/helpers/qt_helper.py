from PyQt6.QtWidgets import QLabel, QWidget


class QtHelper:
    @staticmethod
    def make_label(text: str, object_name: str = "") -> QLabel:
        """Create a QLabel with an optional object name used by the stylesheet."""
        label = QLabel(text)
        if object_name:
            label.setObjectName(object_name)
        return label

    @staticmethod
    def set_style_name(widget: QWidget, name: str) -> None:
        """Give ``widget`` a new object name and re-apply the stylesheet to it."""
        widget.setObjectName(name)
        style = widget.style()
        if style is not None:
            style.unpolish(widget)
            style.polish(widget)
