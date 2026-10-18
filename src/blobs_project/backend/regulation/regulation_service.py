from __future__ import annotations

import logging
import math

from blobs_project import config
from blobs_project.backend.dtos.regulation_values import RegulationValues
from blobs_project.backend.hardware import HardwareError, SimulatedDAQ, Tower
from blobs_project.backend.timekeeping import Stopwatch

from .controllers import PIRegulationController, RegulationControllerBase
from .level_filter import LevelFilter
from .profile_required_error import ProfileRequiredError
from .regulation_process_loader import CsvProfile
from .sample_log import SampleLog

logger = logging.getLogger(__name__)


def pump_power_w(u: float) -> float:
    """Return the estimated pump power [W] at control voltage ``u``."""
    (i0, i1), (v0, v1) = config.PUMP_CURRENT_A, config.PUMP_VOLTAGE_V
    return (v0 + v1 * u) * (i0 + i1 * u)


def lower_outflow_l_min(level_cm: float) -> float:
    """Return the lower-tank outflow [l/min]; in steady state it equals the inflow."""
    h_m = max(level_cm, 0.0) / 100.0
    q_m3_s = config.LOWER_OUTFLOW_COEFF_M2 * math.sqrt(2.0 * config.GRAVITY_M_S2 * h_m)
    return q_m3_s * 60000.0


def clamp_setpoint_cm(level_cm: float) -> float:
    """Return ``level_cm`` limited to the allowed setpoint range."""
    return min(max(level_cm, config.SETPOINT_MIN_CM), config.SETPOINT_MAX_CM)


class RegulationService:
    """Run the level control loop on a ``Tower`` and keep its log and profile."""

    def __init__(
        self, ctrl: RegulationControllerBase | None = None, tower: Tower | None = None
    ) -> None:
        """Use ``ctrl`` (default PI) on ``tower`` (default simulated)."""
        self._profile: CsvProfile | None = None
        self._sample_log = SampleLog()
        self._stopwatch = Stopwatch(config.PROFILE_SAMPLE_INTERVAL_S)
        self._controller = ctrl or PIRegulationController()
        self._tower = tower or Tower(SimulatedDAQ())
        self._level_filter = LevelFilter(config.LEVEL_MEDIAN_SAMPLES)
        self._since_control_s = 0.0
        self._invalid_samples = 0
        self._fault: str | None = None
        self._regulation_active = False
        self._self_driven_active = False
        self._profile_finished = False
        self._chart_started = False
        self.regulation_values = RegulationValues.default()

    @property
    def profile(self) -> CsvProfile | None:
        return self._profile

    @property
    def tower(self) -> Tower:
        return self._tower

    @property
    def simulated(self) -> bool:
        """Return whether the tower is the simulated plant, not the NI card."""
        return isinstance(self._tower.daq, SimulatedDAQ)

    @property
    def fault(self) -> str | None:
        """Return why the last run was stopped by the service, or ``None``."""
        return self._fault

    @property
    def overflow_warning(self) -> bool:
        """Return whether the lower tank is close to overflowing."""
        return self.regulation_values.tank2_actual_cm >= config.LEVEL_WARNING_CM

    def open(self) -> None:
        """Open the tower; the pump starts at 0 V."""
        self._tower.open()

    def close(self) -> None:
        """Stop any run and close the tower with the pump at 0 V."""
        self._regulation_active = False
        self._self_driven_active = False
        self._tower.close()

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
            self._stop_pump()
            return
        self._self_driven_active = False
        self._profile_finished = False
        self._reset_run_state()
        self._regulation_active = True

    def toggle_self_driven(self) -> None:
        if self._self_driven_active:
            self._self_driven_active = False
            self._stop_pump()
            return
        if self._profile is None:
            raise ProfileRequiredError("no profile imported")
        self._regulation_active = False
        self._profile_finished = False
        self._reset_run_state()
        self._self_driven_active = True

    def emergency_stop(self) -> None:
        """Stop any run and the pump at once."""
        self._stop_on_fault("emergency stop")

    def tare(self) -> float:
        """Zero the level sensor on the empty tank and return the new zero [V].

        Raises ``RuntimeError`` while a run is active, ``HardwareError`` if the
        card fails.
        """
        if self.is_running:
            raise RuntimeError("stop the regulation before taring")
        self._level_filter.clear()
        return self._tower.tare(config.TARE_SAMPLES, config.TARE_INTERVAL_S)

    def tick(self, dt_s: float) -> None:
        if dt_s <= 0:
            return
        self._since_control_s += dt_s
        due = self._since_control_s >= config.CONTROL_PERIOD_S
        if not self.is_running:
            self.regulation_values.reset_flow()
            self.regulation_values.reset_pump()
            if due:
                self._since_control_s = 0.0
                self._monitor_step()
            return
        self._stopwatch.advance(dt_s)
        if self._self_driven_active:
            self._apply_profile_desired()
        if due:
            self._control_step(self._since_control_s)
            self._since_control_s = 0.0
            if not self.is_running:
                return
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
        self._level_filter.clear()
        self._since_control_s = 0.0
        self._invalid_samples = 0
        self._fault = None
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

    def _monitor_step(self) -> None:
        """Read the level while no run is active; a lost card is reported once."""
        try:
            level_cm = self._level_filter(self._tower.read_level_cm())
        except HardwareError as e:
            if self._fault is None:
                logger.error("level reading failed: %s", e)
                self._fault = f"tower error: {e}"
            return
        if math.isfinite(level_cm):
            self.regulation_values.tank2_actual_cm = level_cm

    def _control_step(self, dt_s: float) -> None:
        """Read the level, run the controller and drive the pump."""
        try:
            level_cm = self._level_filter(self._tower.read_level_cm())
            if not math.isfinite(level_cm):
                self._invalid_samples += 1
                if self._invalid_samples >= config.MAX_INVALID_SAMPLES:
                    self._stop_on_fault(
                        f"{self._invalid_samples} invalid level readings"
                    )
                return
            self._invalid_samples = 0
            self.regulation_values.tank2_actual_cm = level_cm
            if level_cm >= config.LEVEL_TRIP_CM:
                limit = config.LEVEL_TRIP_CM
                self._stop_on_fault(f"level {level_cm:.1f} cm reached {limit} cm")
                return
            desired_cm = clamp_setpoint_cm(self.regulation_values.tank2_desired_cm)
            volts = self._controller.compute(dt_s, desired_cm, level_cm)
            applied = self._tower.set_pump_voltage(volts)
        except (HardwareError, ValueError) as e:
            self._stop_on_fault(f"tower error: {e}")
            return
        self.regulation_values.flow_l_min = lower_outflow_l_min(level_cm)
        self.regulation_values.pump_power_w = pump_power_w(applied)

    def _stop_on_fault(self, reason: str) -> None:
        """Stop the run, the pump to 0 V, and remember ``reason``."""
        logger.error("regulation stopped: %s", reason)
        self._fault = reason
        self._regulation_active = False
        self._self_driven_active = False
        self._stop_pump()

    def _stop_pump(self) -> None:
        """Set the pump to 0 V; a failing write is logged, never raised."""
        try:
            self._tower.stop_pump()
        except HardwareError:
            logger.exception("could not stop the pump")
        self.regulation_values.reset_flow()
        self.regulation_values.reset_pump()

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
        if not self._self_driven_active:
            return
        if self._profile is None:
            self._self_driven_active = False
            self._stop_pump()
            return
        if self._stopwatch.elapsed_s < self._profile.duration_s:
            return
        self._self_driven_active = False
        self._profile_finished = True
        self._stop_pump()
