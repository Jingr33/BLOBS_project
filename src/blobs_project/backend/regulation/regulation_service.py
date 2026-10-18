from __future__ import annotations

import logging
import math
from collections.abc import Sequence

from blobs_project import config
from blobs_project.backend.dtos import RegulationValues, RunStatistics, Sample
from blobs_project.backend.hardware import HardwareError, SimulatedDAQ, Tower
from blobs_project.backend.statistics import StatisticsCalculator
from blobs_project.backend.timekeeping import Stopwatch

from .controllers import (
    ControllerError,
    MPCRegulationController,
    PIRegulationController,
    PlantParams,
    RegulationControllerBase,
)
from .measurement import LevelFilter, LevelObserver, ProcessModel
from .profile import CsvProfile, ProfileRequiredError, ProfileSchedule
from .recording import SampleLog
from .safety_guard import SafetyGuard

logger = logging.getLogger(__name__)


class RegulationService:
    """Run the level control loop on a ``Tower`` and keep its log and profile."""

    def __init__(
        self, ctrl: RegulationControllerBase | None = None, tower: Tower | None = None
    ) -> None:
        """Use ``ctrl`` (default MPC) on ``tower`` (default simulated)."""
        self._schedule = ProfileSchedule()
        self._safety = SafetyGuard()
        self._sample_log = SampleLog()
        self._stopwatch = Stopwatch(config.PROFILE_SAMPLE_INTERVAL_S)
        self._tower = tower or Tower(SimulatedDAQ())
        self._controller = ctrl or MPCRegulationController(
            PlantParams(u_max=self._tower.max_pump_voltage)
        )
        self._level_filter = LevelFilter(config.LEVEL_MEDIAN_SAMPLES)
        self._level_observer = LevelObserver(config.LEVEL_MEDIAN_SAMPLES)
        self._since_control_s = 0.0
        self._fault: str | None = None
        self._statistics = StatisticsCalculator.calculate(())
        self._pump_state_uncertain = False
        self._statistics_key: tuple[int, float] = (0, 0.0)
        self._regulation_active = False
        self._self_driven_active = False
        self._profile_finished = False
        self._chart_started = False
        self.regulation_values = RegulationValues.default()

    @property
    def profile(self) -> CsvProfile | None:
        return self._schedule.profile

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
    def statistics(self) -> RunStatistics:
        """Return the statistics of the current or last run."""
        samples = self._sample_log.samples
        key = (len(samples), samples[-1].time_s if samples else 0.0)
        if key != self._statistics_key:
            self._statistics = StatisticsCalculator.calculate(samples)
            self._statistics_key = key
        return self._statistics

    @property
    def pump_at_limit(self) -> bool:
        """Return whether a running controller output is at its lower or upper limit."""
        volts = self.regulation_values.pump_voltage_v
        return self.is_running and self._safety.at_pump_limit(volts)

    @property
    def overflow_warning(self) -> bool:
        """Return whether the level is high or projected to reach the warning level."""
        predicted = self._level_observer.predict(config.LEVEL_PREDICTION_HORIZON_S)
        return (
            self._safety.overflow_warning(self.regulation_values.tank2_actual_cm)
            or predicted is not None
            and predicted >= config.LEVEL_WARNING_CM
        )

    @property
    def pump_state_uncertain(self) -> bool:
        """Return whether a pump command failed and its physical state is unknown."""
        return self._pump_state_uncertain

    @property
    def predicted_level_cm(self) -> float | None:
        """Return the projected level over the configured prediction horizon."""
        return self._level_observer.predict(config.LEVEL_PREDICTION_HORIZON_S)

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
        if not self._self_driven_active:
            return None
        return self._schedule.remaining_s(self._stopwatch.elapsed_s)

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

    @property
    def step_s(self) -> float:
        """Return how long each profile level is held [s]."""
        return self._schedule.step_s

    @property
    def profile_step(self) -> int | None:
        """Return the 0-based profile step being run, or ``None``."""
        if not self._self_driven_active:
            return None
        return self._schedule.step_at(self._stopwatch.elapsed_s)

    def set_profile(self, profile: CsvProfile | None) -> None:
        self._schedule.set_profile(profile)

    def set_step_s(self, step_s: float) -> None:
        """Hold each profile level for ``step_s``; ignored while a profile runs."""
        if not self._self_driven_active:
            self._schedule.set_step_s(step_s)

    def load_history(self, samples: Sequence[Sample]) -> None:
        """Show a recorded run in the chart and statistics.

        Raises ``RuntimeError`` while a run is active.
        """
        if self.is_running:
            raise RuntimeError("stop the regulation before loading a run")
        self._sample_log.load(samples)
        self._chart_started = True
        self._profile_finished = False

    def toggle_regulation(self) -> None:
        if self._regulation_active:
            self._regulation_active = False
            self._stop_pump()
            return
        if not self._stop_pump():
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
        if self._schedule.profile is None:
            raise ProfileRequiredError("no profile imported")
        if not self._stop_pump():
            return
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
        self._level_observer.clear()
        return self._tower.tare(config.TARE_SAMPLES, config.TARE_INTERVAL_S)

    def force_reset(self) -> None:
        self._regulation_active = False
        self._self_driven_active = False
        self._profile_finished = False
        self._reset_run_state()
        self.regulation_values.tank2_desired_cm = 0.0
        self._stop_pump()

    def tick(self, dt_s: float) -> None:
        if dt_s <= 0:
            return
        self._since_control_s += dt_s
        due = self._since_control_s >= config.CONTROL_PERIOD_S
        if not self.is_running:
            self.regulation_values.reset_flow()
            if not self._pump_state_uncertain:
                self.regulation_values.reset_pump()
            if due:
                monitor_dt_s = self._since_control_s
                self._since_control_s = 0.0
                self._monitor_step(monitor_dt_s)
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
        if self._schedule.profile is not None and (
            self._self_driven_active or self._profile_finished
        ):
            return self._schedule.points()
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
        self._level_observer.clear()
        self._since_control_s = 0.0
        self._safety.reset()
        self._fault = None
        self.regulation_values.reset_flow()
        self.regulation_values.reset_energy()

    def _apply_profile_desired(self) -> None:
        desired_cm = self._schedule.desired_at(self._stopwatch.elapsed_s)
        if desired_cm is None:
            self._self_driven_active = False
            return
        self.regulation_values.tank2_desired_cm = desired_cm

    def _monitor_step(self, dt_s: float) -> None:
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
            self._level_observer.observe(level_cm, dt_s)

    def _control_step(self, dt_s: float) -> None:
        """Read the level, run the controller and drive the pump."""
        try:
            level_cm = self._level_filter(self._tower.read_level_cm())
            reason = self._safety.check_level(level_cm)
            if reason is not None:
                self._stop_on_fault(reason)
                return
            if not math.isfinite(level_cm):
                return
            self.regulation_values.tank2_actual_cm = level_cm
            self._level_observer.observe(level_cm, dt_s)
            desired = self.regulation_values.tank2_desired_cm
            desired_cm = self._safety.clamp_setpoint_cm(desired)
            volts = self._controller.compute(dt_s, desired_cm, level_cm)
            applied = self._tower.set_pump_voltage(volts)
            self._pump_state_uncertain = False
        except (ControllerError, HardwareError, ValueError) as e:
            self._stop_on_fault(f"tower error: {e}")
            return
        self.regulation_values.flow_l_min = ProcessModel.lower_outflow_l_min(level_cm)
        self.regulation_values.pump_power_w = ProcessModel.pump_power_w(applied)
        self.regulation_values.pump_voltage_v = applied

    def _stop_on_fault(self, reason: str) -> None:
        """Stop the run, the pump to 0 V, and remember ``reason``."""
        logger.error("regulation stopped: %s", reason)
        self._fault = reason
        self._regulation_active = False
        self._self_driven_active = False
        self._stop_pump()

    def _stop_pump(self) -> bool:
        """Set the pump to 0 V; report when its physical state cannot be confirmed."""
        try:
            self._tower.stop_pump()
        except HardwareError as e:
            self._pump_state_uncertain = True
            logger.exception("could not stop the pump")
            failure = f"pump off unconfirmed: {e}"
            self._fault = (
                f"{self._fault}; {failure}" if self._fault is not None else failure
            )
            self.regulation_values.reset_flow()
            return False
        self._pump_state_uncertain = False
        self.regulation_values.reset_flow()
        self.regulation_values.reset_pump()
        return True

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
            self.regulation_values.pump_voltage_v,
        )

    def _stop_profile_when_finished(self) -> None:
        if not self._self_driven_active:
            return
        if not self._schedule.finished(self._stopwatch.elapsed_s):
            return
        self._self_driven_active = False
        self._profile_finished = True
        self._stop_pump()
