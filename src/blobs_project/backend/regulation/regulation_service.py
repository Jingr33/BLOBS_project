from __future__ import annotations

from blobs_project import config
from blobs_project.backend.dtos.regulation_values import RegulationValues
from blobs_project.backend.timekeeping import Stopwatch

from .controllers import ProportionalController, RegulationControllerBase
from .profile_required_error import ProfileRequiredError
from .regulation_process_loader import CsvProfile
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
        self._chart_started = False
        self.regulation_values = RegulationValues.default()

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
    def remaining_s(self) -> float | None:
        if not self._self_driven_active or self._profile is None:
            return None
        return max(0.0, self._profile.duration_s - self._stopwatch.elapsed_s)

    @property
    def tank2_deviation_percent(self) -> float:
        if self.regulation_values.tank2_desired_cm <= 0:
            return 0.0
        return (
            (
                self.regulation_values.tank2_actual_cm
                - self.regulation_values.tank2_desired_cm
            )
            / self.regulation_values.tank2_desired_cm
            * 100.0
        )

    def set_profile(self, profile: CsvProfile | None) -> None:
        self._profile = profile

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
        self.regulation_values.tank2_desired_cm = 0.0

    def tick(self, dt_s: float) -> None:
        if not self.is_running or dt_s <= 0:
            self.regulation_values.reset_flow()
            self.regulation_values.reset_pump()
            return
        self._stopwatch.advance(dt_s)
        if self._self_driven_active:
            self._apply_profile_desired()
        self._advance_level(dt_s)
        self.regulation_values.total_energy_wh += (
            self.regulation_values.pump_power_w * dt_s / 3600.0
        )
        self._record_sample()
        self._stop_profile_when_finished()

    def trend_points(self) -> list[tuple[float, float]]:
        return self._sample_log.trend_points()

    def desired_trend_points(self) -> list[tuple[float, float]]:
        if self._profile is not None and (
            self._self_driven_active or self._profile_finished
        ):
            return self._full_profile_points()
        return self._sample_log.desired_trend_points()

    def flow_trend_points(self) -> list[tuple[float, float]]:
        return self._sample_log.flow_trend_points()

    def pump_power_trend_points(self) -> list[tuple[float, float]]:
        return self._sample_log.pump_power_trend_points()

    def _reset_run_state(self) -> None:
        self._stopwatch.start()
        self._chart_started = True
        self._sample_log.clear()
        self._controller.reset()
        self.regulation_values.reset_flow()
        self.regulation_values.reset_pump()
        self.regulation_values.reset_energy()

    def _apply_profile_desired(self) -> None:
        if self._profile is None:
            self._self_driven_active = False
            return
        self.regulation_values.tank2_desired_cm = self._profile.desired_at(
            self._stopwatch.elapsed_s
        )

    def _advance_level(self, dt_s: float) -> None:
        change = self._controller.compute(
            dt_s,
            self.regulation_values.tank2_desired_cm,
            self.regulation_values.tank2_actual_cm,
        )
        previous_cm = self.regulation_values.tank2_actual_cm
        self.regulation_values.tank2_actual_cm = (
            self.regulation_values.tank2_actual_cm + change
        )
        self._update_flow_and_power(dt_s, previous_cm)

    def _update_flow_and_power(self, dt_s: float, previous_cm: float) -> None:
        delta_cm = self.regulation_values.tank2_actual_cm - previous_cm
        flow_cm3_s = delta_cm / dt_s * config.TANK_CROSS_SECTION_CM2
        self.regulation_values.flow_l_min = flow_cm3_s * config.L_MIN_PER_CM3_S
        if self.regulation_values.flow_l_min <= 0.0:
            self.regulation_values.reset_pump()
            return
        head_m = self.regulation_values.tank2_actual_cm / 100.0
        flow_m3_s = self.regulation_values.flow_l_min / 60000.0
        self.regulation_values.pump_power_w = (
            config.WATER_DENSITY_KG_M3
            * config.GRAVITY_M_S2
            * head_m
            * flow_m3_s
            / config.PUMP_EFFICIENCY
        )

    def _full_profile_points(self) -> list[tuple[float, float]]:
        if self._profile is None:
            return []
        interval = config.PROFILE_SAMPLE_INTERVAL_S
        steps = int(round(self._profile.duration_s / interval))
        return [
            (step * interval, self._profile.desired_at(step * interval))
            for step in range(steps + 1)
        ]

    def _record_sample(self) -> None:
        if not self._stopwatch.sample_due:
            return
        self._stopwatch.mark()
        self._sample_log.append(
            self._stopwatch.elapsed_s,
            self.regulation_values.tank2_desired_cm,
            self.regulation_values.tank2_actual_cm,
            self.regulation_values.flow_l_min,
            self.regulation_values.pump_power_w,
        )

    def _stop_profile_when_finished(self) -> None:
        if self._profile is None:
            self._self_driven_active = False
            return
        if self._stopwatch.elapsed_s < self._profile.duration_s:
            return
        self._self_driven_active = False
        self._profile_finished = True
