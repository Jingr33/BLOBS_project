from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel

from blobs_project import config
from blobs_project.translations import tr


class FooterFrame(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("panel")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(16)
        self.status_label = QLabel(self._status_text(tr("status.ready")))
        self.set_status(tr("status.ready"))
        layout.addWidget(self.status_label)
        layout.addStretch()
        self.time_label = QLabel(tr("footer.no_regulation"))
        self.time_label.setObjectName("muted")
        layout.addWidget(self.time_label)
        self.remaining_label = QLabel()
        self.remaining_label.setObjectName("muted")
        self.remaining_label.setVisible(False)
        layout.addWidget(self.remaining_label)

    def set_status(self, text: str, alert: bool = False) -> None:
        self.status_label.setText(self._status_text(text))
        color = config.RED if alert else config.GREEN
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 700;")

    def set_regulation_time(self, elapsed_s: float | None) -> None:
        if elapsed_s is None:
            self.time_label.setText(tr("footer.no_regulation"))
        else:
            self.time_label.setText(
                tr("footer.regulation_time", time=self._format_time(elapsed_s))
            )

    def set_remaining_time(self, remaining_s: float | None) -> None:
        if remaining_s is None:
            self.remaining_label.clear()
            self.remaining_label.setVisible(False)
            return
        self.remaining_label.setText(
            tr("footer.remaining_time", time=self._format_time(remaining_s))
        )
        self.remaining_label.setVisible(True)

    @staticmethod
    def _format_time(seconds: float) -> str:
        minutes = int(seconds // 60)
        rest = seconds - minutes * 60
        return f"{minutes:02d}:{rest:04.1f}"

    @staticmethod
    def _status_text(text: str) -> str:
        return f"●  {text}"
