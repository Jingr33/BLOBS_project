from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QWidget

from blobs_project.backend.regulation import (
    CsvProfile,
    ProfileRequiredError,
    RegulationService,
)
from blobs_project.frontend.helpers.qt_helper import QtHelper
from blobs_project.frontend.widgets.tare_prompt import TarePrompt
from blobs_project.translations import tr


class AutomaticControls(QWidget):
    """Profile driven regulation controls shown on the Settings tab."""

    status_changed = pyqtSignal(str)

    def __init__(self, regulation_service: RegulationService) -> None:
        super().__init__()
        self._regulation_service = regulation_service
        self._build_ui()
        self._tare_prompt = TarePrompt(regulation_service, self)
        self.sync()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self._automatic_button = QtHelper.make_button(
            tr("regulation.start_automatic"), "primary", self._toggle_automatic
        )
        layout.addWidget(self._automatic_button)

        self._profile_label = QtHelper.make_label(
            tr("regulation.profile_missing"), "profile"
        )
        layout.addWidget(self._profile_label)
        layout.addStretch()

    def sync(self) -> None:
        regulation_service = self._regulation_service
        QtHelper.set_run_button_state(
            self._automatic_button,
            regulation_service.self_driven_active,
            "regulation.start_automatic",
            "regulation.stop_automatic",
        )
        self._automatic_button.setEnabled(
            regulation_service.profile is not None
            and not regulation_service.regulation_active
        )
        self._set_profile_label(regulation_service.profile)

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

    def _toggle_automatic(self) -> None:
        regulation_service = self._regulation_service
        if (
            not regulation_service.self_driven_active
            and regulation_service.profile is not None
            and not self._tare_prompt.confirm()
        ):
            return
        try:
            self._regulation_service.toggle_self_driven()
        except ProfileRequiredError:
            self.status_changed.emit(tr("status.profile_required"))
            return
        self.sync()
