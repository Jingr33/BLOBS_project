from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
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
    SampleExportStatus,
)
from blobs_project.frontend.helpers.qt_helper import QtHelper
from blobs_project.frontend.widgets.tank_control import TankControl
from blobs_project.translations import tr


class RegulationFrame(QFrame):
    status_changed = pyqtSignal(str)

    def __init__(self, service: RegulationService) -> None:
        super().__init__()
        self._service = service
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
        layout.addWidget(self._build_mode_label())
        layout.addSpacing(6)
        self._regulation_button = self._build_button(
            tr("regulation.start_regulation"), "primary", self._toggle_regulation
        )
        layout.addWidget(self._regulation_button)
        layout.addSpacing(18)
        layout.addLayout(self._build_csv_row())
        self._self_driven_button = self._build_button(
            tr("regulation.start_self_driven"), "primary", self._toggle_self_driven
        )
        layout.addWidget(self._self_driven_button)
        self._profile_label = QtHelper.make_label(
            tr("regulation.profile_missing"), "profile"
        )
        layout.addWidget(self._profile_label)

        self._tank2_control.desired_changed.connect(self._service.set_desired_tank2)

    def _build_csv_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        self._import_button = self._build_button(
            tr("regulation.import_csv"), "", self._import_csv
        )
        row.addWidget(self._import_button)
        self._export_button = self._build_button(
            tr("regulation.export_csv"), "", self._export_csv
        )
        row.addWidget(self._export_button)
        return row

    def sync(self) -> None:
        service = self._service
        self._tank2_control.set_values(
            service.tank2_actual_cm,
            service.tank2_desired_cm,
            service.tank2_deviation_percent,
        )
        self._tank2_control.set_desired_editable(not service.self_driven_active)

        mode_key = (
            "regulation.desired_levels_profile"
            if service.self_driven_active
            else "regulation.desired_levels_manual"
        )
        self._mode_label.setText(tr(mode_key))
        self._set_button_state(
            self._regulation_button,
            service.regulation_active,
            "regulation.start_regulation",
            "regulation.stop_regulation",
        )
        self._set_button_state(
            self._self_driven_button,
            service.self_driven_active,
            "regulation.start_self_driven",
            "regulation.stop_self_driven",
        )
        self._regulation_button.setEnabled(not service.self_driven_active)
        self._self_driven_button.setEnabled(
            service.profile is not None and not service.regulation_active
        )
        self._set_profile_label(service.profile)

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
        self._service.toggle_regulation()
        self.sync()

    def _toggle_self_driven(self) -> None:
        try:
            self._service.toggle_self_driven()
        except ProfileRequiredError:
            self.status_changed.emit(tr("status.profile_required"))
            return
        self.sync()

    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.import_title"), "", tr("dialog.csv_filter")
        )
        if not path:
            return
        profile = self._service.import_profile(path)
        if profile is None:
            self.status_changed.emit(tr("status.profile_invalid"))
            return
        self.status_changed.emit(
            tr(
                "status.profile_loaded",
                rows=profile.row_count,
                duration=profile.duration_s,
            )
        )
        self.sync()

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("dialog.export_title"), "samples.csv", tr("dialog.csv_filter")
        )
        if not path:
            return
        status = self._service.export_samples(path)
        if status is SampleExportStatus.FAILED:
            self.status_changed.emit(tr("status.export_failed"))
        elif status is SampleExportStatus.NO_SAMPLES:
            self.status_changed.emit(tr("status.export_missing"))
        else:
            self.status_changed.emit(tr("status.export_ready"))

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
