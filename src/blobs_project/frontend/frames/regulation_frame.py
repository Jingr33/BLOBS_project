from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from blobs_project import config
from blobs_project.backend.regulation import RegulationService
from blobs_project.frontend.helpers.qt_helper import QtHelper
from blobs_project.frontend.widgets.tank_control import TankControl
from blobs_project.frontend.widgets.tare_prompt import TarePrompt
from blobs_project.translations import tr


class RegulationFrame(QFrame):
    """Manual regulation controls shown above the diagrams on Overview."""

    def __init__(self, regulation_service: RegulationService) -> None:
        super().__init__()
        self._regulation_service = regulation_service
        self.setObjectName("regulation")
        self._tank2_control = TankControl(
            tr("tank.lower_label"), config.TANK_LOWER_COLOR
        )
        self._build_ui()
        self._tare_prompt = TarePrompt(regulation_service, self)
        self.sync()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(16)
        self._regulation_button = QtHelper.make_button(
            tr("regulation.start_regulation"), "primary", self._toggle_regulation
        )
        row.addWidget(self._regulation_button)
        row.addWidget(self._tank2_control)
        row.addStretch()
        self._mode_label = QtHelper.make_label(
            tr("regulation.desired_levels_manual"), "mode"
        )
        self._mode_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        row.addWidget(self._mode_label)
        layout.addLayout(row)

        self._alert_label = QtHelper.make_label("", "alert")
        self._alert_label.setWordWrap(True)
        self._alert_label.setVisible(False)
        layout.addWidget(self._alert_label)

        self._tank2_control.desired_changed.connect(self._set_desired_level)

    def _set_desired_level(self, value_cm: float) -> None:
        self._regulation_service.regulation_values.tank2_desired_cm = value_cm

    def sync(self) -> None:
        regulation_service = self._regulation_service
        self._tank2_control.set_values(
            regulation_service.regulation_values.tank2_desired_cm,
            regulation_service.tank2_deviation_percent,
        )
        self._tank2_control.set_desired_editable(
            not regulation_service.self_driven_active
        )

        mode_key = (
            "regulation.desired_levels_profile"
            if regulation_service.self_driven_active
            else "regulation.desired_levels_manual"
        )
        self._mode_label.setText(tr(mode_key))
        QtHelper.set_run_button_state(
            self._regulation_button,
            regulation_service.regulation_active,
            "regulation.start_regulation",
            "regulation.stop_regulation",
        )
        self._regulation_button.setEnabled(not regulation_service.self_driven_active)
        self._set_alert_label()

    def _set_alert_label(self) -> None:
        fault = self._regulation_service.fault
        if fault is not None:
            text = tr("regulation.fault", reason=fault)
        elif self._regulation_service.overflow_warning:
            predicted = self._regulation_service.predicted_level_cm
            current = self._regulation_service.regulation_values.tank2_actual_cm
            level = max(current, predicted if predicted is not None else current)
            text = tr("regulation.overflow_warning", level=level)
        else:
            text = ""
        self._alert_label.setText(text)
        self._alert_label.setVisible(bool(text))

    def _toggle_regulation(self) -> None:
        if (
            not self._regulation_service.regulation_active
            and not self._tare_prompt.confirm()
        ):
            return
        self._regulation_service.toggle_regulation()
        self.sync()
