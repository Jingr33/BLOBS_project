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
        self.status_label = QLabel(self._status_text(tr("status.ready")))
        self.status_label.setStyleSheet(f"color: {config.GREEN}; font-weight: 700;")
        layout.addWidget(self.status_label)
        layout.addStretch()
        self.time_label = QLabel(tr("footer.no_regulation"))
        self.time_label.setObjectName("muted")
        layout.addWidget(self.time_label)

    def set_status(self, text: str) -> None:
        self.status_label.setText(self._status_text(text))

    def set_regulation_time(self, elapsed_s: float | None) -> None:
        if elapsed_s is None:
            text = tr("footer.no_regulation")
        else:
            minutes = int(elapsed_s // 60)
            seconds = elapsed_s - minutes * 60
            text = tr("footer.regulation_time", time=f"{minutes:02d}:{seconds:04.1f}")
        self.time_label.setText(text)

    @staticmethod
    def _status_text(text: str) -> str:
        return f"●  {text}"
