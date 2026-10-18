from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
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
from blobs_project.frontend.actions import ActionId, ActionPlace, visible_actions
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
        layout.addLayout(self._build_pump_grid())
        layout.addWidget(self._tank2_control)
        layout.addWidget(self._build_mode_label())
        layout.addSpacing(6)
        self._regulation_button = self._build_button(
            tr("regulation.start_regulation"), "primary", self._toggle_regulation
        )
        self._stop_button = self._build_button(
            tr("regulation.emergency_stop"), "emergency", self._emergency_stop
        )
        run_row = QHBoxLayout()
        run_row.setSpacing(8)
        run_row.addWidget(self._regulation_button, 1)
        run_row.addWidget(self._stop_button, 1)
        layout.addLayout(run_row)
        layout.addSpacing(18)
        self._automatic_button = self._build_button(
            tr("regulation.start_automatic"), "primary", self._toggle_automatic
        )
        layout.addLayout(self._build_action_row())
        layout.addLayout(self._build_step_row())
        self._profile_label = QtHelper.make_label(
            tr("regulation.profile_missing"), "profile"
        )
        layout.addWidget(self._profile_label)
        self._alert_label = QtHelper.make_label("", "alert")
        self._alert_label.setWordWrap(True)
        self._alert_label.setVisible(False)
        layout.addWidget(self._alert_label)

        self._tank2_control.desired_changed.connect(self._set_desired_level)

    def _set_desired_level(self, value_cm: float) -> None:
        self._regulation_service.regulation_values.tank2_desired_cm = value_cm

    def _build_action_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        if ActionId.IMPORT_CSV in visible_actions(ActionPlace.REGULATION):
            import_button = QPushButton(tr("action.import_csv"))
            import_button.clicked.connect(
                lambda _checked=False: self.action_requested.emit(ActionId.IMPORT_CSV)
            )
            row.addWidget(import_button, 1)
        row.addWidget(self._automatic_button, 2)
        return row

    def _build_step_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QtHelper.make_caption(tr("regulation.step_duration")))
        self._step_spin = QDoubleSpinBox()
        self._step_spin.setRange(0.5, 60.0)
        self._step_spin.setDecimals(1)
        self._step_spin.setSingleStep(0.5)
        self._step_spin.setKeyboardTracking(False)
        self._step_spin.setValue(self._regulation_service.step_s / 60.0)
        self._step_spin.valueChanged.connect(
            lambda minutes: self._regulation_service.set_step_s(minutes * 60.0)
        )
        row.addWidget(self._step_spin)
        return row

    def _build_pump_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setVerticalSpacing(8)
        grid.setHorizontalSpacing(12)
        self._power_label = QtHelper.add_metric_row(grid, 0, tr("regulation.power"))
        self._voltage_label = QtHelper.add_metric_row(grid, 1, tr("regulation.voltage"))
        grid.setColumnStretch(1, 1)
        return grid

    def sync(self) -> None:
        regulation_service = self._regulation_service
        self._tank2_control.set_values(
            regulation_service.regulation_values.tank2_actual_cm,
            regulation_service.regulation_values.tank2_desired_cm,
            regulation_service.tank2_deviation_percent,
        )
        self._tank2_control.set_desired_editable(
            not regulation_service.self_driven_active
        )
        self._tank2_control.set_flow(regulation_service.regulation_values.flow_l_min)
        self._power_label.setText(
            f"{regulation_service.regulation_values.pump_power_w:.2f}"
        )
        self._set_voltage_label()

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
            self._automatic_button,
            regulation_service.self_driven_active,
            "regulation.start_automatic",
            "regulation.stop_automatic",
        )
        self._regulation_button.setEnabled(not regulation_service.self_driven_active)
        self._automatic_button.setEnabled(
            regulation_service.profile is not None
            and not regulation_service.regulation_active
        )
        self._step_spin.setEnabled(not regulation_service.self_driven_active)
        if not self._step_spin.hasFocus():
            self._step_spin.blockSignals(True)
            self._step_spin.setValue(regulation_service.step_s / 60.0)
            self._step_spin.blockSignals(False)
        self._set_profile_label(regulation_service.profile)
        self._set_alert_label()

    def _set_voltage_label(self) -> None:
        volts = self._regulation_service.regulation_values.pump_voltage_v
        if self._regulation_service.pump_state_uncertain:
            self._voltage_label.setText(tr("regulation.voltage_unknown", value=volts))
            self._voltage_label.setStyleSheet(f"color: {config.RED};")
        elif self._regulation_service.pump_at_limit:
            self._voltage_label.setText(tr("regulation.voltage_limit", value=volts))
            self._voltage_label.setStyleSheet(f"color: {config.ORANGE};")
        else:
            self._voltage_label.setText(f"{volts:.2f}")
            self._voltage_label.setStyleSheet("")

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

    def _set_profile_label(self, profile: CsvProfile | None) -> None:
        if profile is None:
            self._profile_label.setText(tr("regulation.profile_missing"))
            return
        n = profile.row_count
        step = self._regulation_service.profile_step
        if step is None:
            minutes, total = profile.step_s / 60.0, profile.duration_s / 60.0
            text = tr("regulation.profile_loaded", rows=n, step=minutes, total=total)
        else:
            level = profile.tank2_levels[step]
            text = tr("regulation.profile_step", step=step + 1, rows=n, level=level)
        self._profile_label.setText(text)

    def _toggle_regulation(self) -> None:
        self._regulation_service.toggle_regulation()
        self.sync()

    def _emergency_stop(self) -> None:
        self._regulation_service.emergency_stop()
        self.sync()

    def _toggle_automatic(self) -> None:
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
