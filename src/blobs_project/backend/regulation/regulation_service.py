from __future__ import annotations

from pathlib import Path

from blobs_project import config
from blobs_project.backend.timekeeping import Stopwatch

from .controllers import ProportionalController, RegulationControllerBase
from .profile_required_error import ProfileRequiredError
from .regulation_process_loader import (
    CsvExporter,
    CsvProfile,
    CsvProfileError,
    ProfileLoader,
)
from .sample_export_status import SampleExportStatus
from .sample_log import SampleLog


class RegulationService:
    def __init__(self, controller: RegulationControllerBase | None = None) -> None:
        self._profile: CsvProfile | None = None
        self._sample_log = SampleLog()
        self._stopwatch = Stopwatch(config.PROFILE_SAMPLE_INTERVAL_S)
        self._controller: RegulationControllerBase = (
            controller if controller is not None else ProportionalController()
        )
        self._regulation_active = False
        self._self_driven_active = False
        self._profile_finished = False
        self._tank2_desired_cm = config.TANK_DESIRED_LEVEL_CM
        self._tank2_actual_cm = config.TANK_ACTUAL_LEVEL_CM
        self._chart_started = False

    @property
    def profile(self) -> CsvProfile | None:
        return self._profile

    @property
    def sample_log(self) -> SampleLog:
        return self._sample_log

    @property
    def regulation_active(self) -> bool:
        return self._regulation_active

    @property
    def self_driven_active(self) -> bool:
        return self._self_driven_active

    @property
    def is_running(self) -> bool:
        return self._regulation_active or self._self_driven_active

    @property
    def profile_finished(self) -> bool:
        return self._profile_finished

    @property
    def chart_started(self) -> bool:
        return self._chart_started

    @property
    def elapsed_s(self) -> float:
        return self._stopwatch.elapsed_s

    @property
    def tank2_actual_cm(self) -> float:
        return self._tank2_actual_cm

    @property
    def tank2_desired_cm(self) -> float:
        return self._tank2_desired_cm

    @property
    def tank2_deviation_percent(self) -> float:
        if self._tank2_desired_cm <= 0:
            return 0.0
        return (
            (self._tank2_actual_cm - self._tank2_desired_cm)
            / self._tank2_desired_cm
            * 100.0
        )

    def set_desired_tank2(self, value_cm: float) -> None:
        self._tank2_desired_cm = self._clamp(value_cm)

    def set_profile(self, profile: CsvProfile | None) -> None:
        self._profile = profile

    def import_profile(self, path: str | Path) -> CsvProfile | None:
        try:
            profile = ProfileLoader.load_profile(path)
        except CsvProfileError:
            return None
        self._profile = profile
        return profile

    def export_samples(self, path: str | Path) -> SampleExportStatus:
        try:
            exported = CsvExporter.export_samples_csv(self._sample_log.samples, path)
        except OSError:
            return SampleExportStatus.FAILED
        if not exported:
            return SampleExportStatus.NO_SAMPLES
        return SampleExportStatus.WRITTEN

    def toggle_regulation(self) -> None:
        if self._regulation_active:
            self._regulation_active = False
            return
        self._self_driven_active = False
        self._profile_finished = False
        self._reset_run_state()
        self._regulation_active = True

    def toggle_self_driven(self) -> None:
        if self._self_driven_active:
            self._self_driven_active = False
            return
        if self._profile is None:
            raise ProfileRequiredError("no profile imported")
        self._regulation_active = False
        self._profile_finished = False
        self._reset_run_state()
        self._self_driven_active = True

    def force_reset(self) -> None:
        self._regulation_active = False
        self._self_driven_active = False
        self._profile_finished = False
        self._reset_run_state()
        self._tank2_desired_cm = 0.0

    def tick(self, dt_s: float) -> None:
        if not self.is_running or dt_s <= 0:
            return
        self._stopwatch.advance(dt_s)
        if self._self_driven_active:
            self._apply_profile_desired()
        self._advance_level(dt_s)
        self._record_sample()
        self._stop_profile_when_finished()

    def trend_points(self) -> list[tuple[float, float]]:
        return self._sample_log.trend_points()

    def desired_trend_points(self) -> list[tuple[float, float]]:
        return self._sample_log.desired_trend_points()

    def _reset_run_state(self) -> None:
        self._stopwatch.start()
        self._chart_started = True
        self._sample_log.clear()
        self._controller.reset()

    def _apply_profile_desired(self) -> None:
        if self._profile is None:
            self._self_driven_active = False
            return
        self._tank2_desired_cm = self._profile.desired_at(self._stopwatch.elapsed_s)

    def _advance_level(self, dt_s: float) -> None:
        change = self._controller.compute(
            dt_s, self._tank2_desired_cm, self._tank2_actual_cm
        )
        self._tank2_actual_cm = self._clamp(self._tank2_actual_cm + change)

    def _record_sample(self) -> None:
        if not self._stopwatch.sample_due:
            return
        self._stopwatch.mark()
        self._sample_log.append(
            self._stopwatch.elapsed_s,
            self._tank2_desired_cm,
            self._tank2_actual_cm,
        )

    def _stop_profile_when_finished(self) -> None:
        if self._profile is None:
            self._self_driven_active = False
            return
        if self._stopwatch.elapsed_s < self._profile.duration_s:
            return
        self._self_driven_active = False
        self._profile_finished = True

    @staticmethod
    def _clamp(value_cm: float) -> float:
        return max(0.0, min(config.TANK_LEVEL_MAX_CM, value_cm))
