from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from blobs_project import config
from blobs_project.backend.regulation import (
    CsvProfile,
    ProfileRequiredError,
    RegulationService,
)
from blobs_project.frontend.actions import (
    ActionPlace,
    visible_actions,
)
from blobs_project.frontend.helpers.qt_helper import QtHelper
from blobs_project.frontend.widgets.tank_control import TankControl
from blobs_project.translations import tr


class RegulationFrame(QFrame):
    action_requested = pyqtSignal(object)
    status_changed = pyqtSignal(str)

    def __init__(self, regulation_service: RegulationService) -> None:
        super().__init__()
        self._regulation_service = regulation_service
        self.setObjectName("regulation")
        self._tank2_control = TankControl(
            tr("tank.lower_label"), config.TANK_LOWER_COLOR
        )
        self._build_ui()
        self.sync()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(12)
        layout.addWidget(
            QtHelper.make_label(tr("regulation.section_title"), "sectionTitle")
        )
        layout.addWidget(self._tank2_control)
        layout.addLayout(self._build_metrics_grid())
        layout.addWidget(self._build_mode_label())
        layout.addSpacing(6)
        self._regulation_button = self._build_button(
            tr("regulation.start_regulation"), "primary", self._toggle_regulation
        )
        layout.addWidget(self._regulation_button)
        layout.addSpacing(18)
        layout.addLayout(self._build_action_row())
        self._self_driven_button = self._build_button(
            tr("regulation.start_self_driven"), "primary", self._toggle_self_driven
        )
        layout.addWidget(self._self_driven_button)
        self._profile_label = QtHelper.make_label(
            tr("regulation.profile_missing"), "profile"
        )
        layout.addWidget(self._profile_label)

        self._tank2_control.desired_changed.connect(self._set_desired_level)

    def _set_desired_level(self, value_cm: float) -> None:
        self._regulation_service.regulation_values.tank2_desired_cm = value_cm

    def _build_action_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        for action_id in visible_actions(ActionPlace.REGULATION):
            button = QPushButton(tr(f"action.{action_id.value}"))
            button.clicked.connect(
                lambda _checked=False, action_id=action_id: self.action_requested.emit(
                    action_id
                )
            )
            row.addWidget(button)
        return row

    def _build_metrics_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setVerticalSpacing(8)
        grid.setHorizontalSpacing(12)
        grid.addWidget(self._metric_caption(tr("regulation.flow")), 0, 0)
        self._flow_label = self._metric_value()
        grid.addWidget(self._flow_label, 0, 1)
        grid.addWidget(self._metric_caption(tr("regulation.power")), 1, 0)
        self._power_label = self._metric_value()
        grid.addWidget(self._power_label, 1, 1)
        grid.setColumnStretch(1, 1)
        return grid

    @staticmethod
    def _metric_caption(text: str) -> QLabel:
        caption = QLabel(text)
        caption.setObjectName("muted")
        return caption

    @staticmethod
    def _metric_value() -> QLabel:
        value = QLabel("—")
        value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return value

    def sync(self) -> None:
        regulation_service = self._regulation_service
        self._tank2_control.set_values(
            regulation_service.regulation_values.tank2_actual_cm,
            regulation_service.regulation_values.tank2_desired_cm,
            regulation_service.tank2_deviation_percent,
        )
        self._tank2_control.set_desired_editable(not regulation_service.self_driven_active)
        self._flow_label.setText(f"{regulation_service.regulation_values.flow_l_min:.1f}")
        self._power_label.setText(f"{regulation_service.regulation_values.pump_power_w:.2f}")

        mode_key = (
            "regulation.desired_levels_profile"
            if regulation_service.self_driven_active
            else "regulation.desired_levels_manual"
        )
        self._mode_label.setText(tr(mode_key))
        self._set_button_state(
            self._regulation_button,
            regulation_service.regulation_active,
            "regulation.start_regulation",
            "regulation.stop_regulation",
        )
        self._set_button_state(
            self._self_driven_button,
            regulation_service.self_driven_active,
            "regulation.start_self_driven",
            "regulation.stop_self_driven",
        )
        self._regulation_button.setEnabled(not regulation_service.self_driven_active)
        self._self_driven_button.setEnabled(
            regulation_service.profile is not None and not regulation_service.regulation_active
        )
        self._set_profile_label(regulation_service.profile)

    def _set_profile_label(self, profile: CsvProfile | None) -> None:
        if profile is None:
            self._profile_label.setText(tr("regulation.profile_missing"))
            return
        self._profile_label.setText(
            tr(
                "regulation.profile_loaded",
                rows=profile.row_count,
                duration=profile.duration_s,
            )
        )

    def _toggle_regulation(self) -> None:
        self._regulation_service.toggle_regulation()
        self.sync()

    def _toggle_self_driven(self) -> None:
        try:
            self._regulation_service.toggle_self_driven()
        except ProfileRequiredError:
            self.status_changed.emit(tr("status.profile_required"))
            return
        self.sync()

    @staticmethod
    def _build_button(
        text: str, object_name: str, slot: Callable[[], None]
    ) -> QPushButton:
        button = QPushButton(text)
        if object_name:
            button.setObjectName(object_name)
        button.clicked.connect(slot)
        return button

    @staticmethod
    def _set_button_state(
        button: QPushButton, active: bool, start_key: str, stop_key: str
    ) -> None:
        button.setText(tr(stop_key if active else start_key))
        QtHelper.set_style_name(button, "danger" if active else "primary")

    def _build_mode_label(self) -> QLabel:
        self._mode_label = QtHelper.make_label(
            tr("regulation.desired_levels_manual"), "muted"
        )
        self._mode_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        return self._mode_label
