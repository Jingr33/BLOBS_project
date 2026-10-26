from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QVBoxLayout

from blobs_project.frontend.actions import ActionId, ActionPlace, visible_actions
from blobs_project.frontend.helpers.qt_helper import QtHelper
from blobs_project.frontend.widgets.clock_widget import ClockWidget
from blobs_project.translations import tr


class HeaderFrame(QFrame):
    action_requested = pyqtSignal(object)
    emergency_stop_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_box.addWidget(QtHelper.make_label(tr("header.eyebrow"), "eyebrow"))
        title_box.addWidget(QtHelper.make_label(tr("header.title"), "title"))
        title_box.setContentsMargins(5, 0, 0, 0)
        layout.addLayout(title_box)
        layout.addStretch()
        self._add_actions(layout)
        self._add_emergency_stop_button(layout)
        layout.addWidget(ClockWidget())

    def _add_actions(self, layout: QHBoxLayout) -> None:
        for action_id in visible_actions(ActionPlace.HEADER):
            self._add_action_button(layout, action_id)

    def _add_action_button(self, layout: QHBoxLayout, action_id: ActionId) -> None:
        button = QPushButton(tr(f"action.{action_id.value}"))
        button.setObjectName("small")
        button.clicked.connect(
            lambda _checked=False, action_id=action_id: self.action_requested.emit(
                action_id
            )
        )
        layout.addWidget(button)

    def _add_emergency_stop_button(self, layout: QHBoxLayout) -> None:
        button = QPushButton(tr("regulation.emergency_stop"))
        button.setObjectName("emergency")
        button.clicked.connect(self.emergency_stop_requested.emit)
        layout.addWidget(button)
