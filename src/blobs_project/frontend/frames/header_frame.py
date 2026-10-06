from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ... import configuration as config
from ...translations import tr
from ..actions import (
    ActionId,
    ActionPlace,
    visible_actions,
)
from ..assets import LOGO_PATH


class HeaderFrame(QFrame):
    status_changed = pyqtSignal(str)
    force_reset_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._logo_label())
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_box.addWidget(self._label(tr("header.eyebrow"), "eyebrow"))
        title_box.addWidget(self._label(tr("header.title"), "title"))
        title_box.setContentsMargins(30, 0, 0, 0)
        layout.addLayout(title_box)
        layout.addStretch()
        self._add_actions(layout)

    def _add_actions(self, layout: QHBoxLayout) -> None:
        for action_id in visible_actions(ActionPlace.TOOLBAR):
            button = QPushButton(self._action_label(action_id))
            button.setObjectName("small")
            button.clicked.connect(
                lambda _checked=False, action_id=action_id: self._handle_action(
                    action_id
                )
            )
            layout.addWidget(button)

    def _handle_action(self, action_id: ActionId) -> None:
        if action_id is ActionId.FORCE_RESET:
            self.force_reset_requested.emit()
            self._emit_status(tr("status.force_reset"))
            return
        self._emit_status(self._action_status(action_id))

    @staticmethod
    def _logo_label() -> QLabel:
        label = QLabel()
        label.setObjectName("logo")
        pixmap = QPixmap(str(LOGO_PATH))
        if not pixmap.isNull():
            label.setPixmap(
                pixmap.scaledToHeight(
                    config.LOGO_HEIGHT, Qt.TransformationMode.SmoothTransformation
                )
            )
        return label

    @staticmethod
    def _action_label(action_id: ActionId) -> str:
        return tr(f"action.{action_id.value}")

    @classmethod
    def _action_status(cls, action_id: ActionId) -> str:
        return tr("status.action_selected", label=cls._action_label(action_id))

    def _emit_status(self, text: str) -> None:
        self.status_changed.emit(text)

    @staticmethod
    def _label(text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        return label
