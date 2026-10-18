import math

import numpy as np
import pytest

from blobs_project import config
from blobs_project.backend.hardware import HardwareError, MockDAQ, Tower
from blobs_project.backend.regulation import (
    KalmanFilter,
    MPCRegulationController,
    PIController,
    PIRegulationController,
    PlantParams,
    RegulationControllerBase,
    RegulationService,
    get_discrete_model,
)


class _RecordingController(RegulationControllerBase):
    def __init__(self, volts: float = 5.0) -> None:
        self.calls: list[tuple[float, float, float]] = []
        self.reset_count = 0
        self.volts = volts

    def reset(self) -> None:
        self.reset_count += 1

    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        self.calls.append((dt_s, desired_cm, actual_cm))
        return self.volts


class _FailingDAQ(MockDAQ):
    def read_voltage(self, channel: str) -> float:
        raise HardwareError("card unplugged")


def make_service(
    controller: RegulationControllerBase, daq: MockDAQ
) -> RegulationService:
    """Return a service on a mocked tower whose sensor reads 10 cm."""
    above_zero_cm = 10.0 - config.TOWER_LEVEL_OFFSET_CM
    level_v = config.TOWER_LEVEL_ZERO_V + above_zero_cm / config.TOWER_LEVEL_CM_PER_V
    daq.set_input_voltage(config.TOWER_LEVEL_CHANNEL, level_v)
    return RegulationService(controller, Tower(daq))


def test_pi_output_is_proportional_plus_integral() -> None:
    """The PI returns Kp*e + Ki*integral(e) inside the limits."""
    pi = PIController(46.8, 1.28, 0.0, 7.5)

    u = pi.compute(0.10, 0.08, 0.5)

    assert u == pytest.approx(46.8 * 0.02 + 1.28 * 0.02 * 0.5)


def test_pi_stays_within_limits() -> None:
    """The output is clamped to [min_out, max_out]."""
    pi = PIController(46.8, 1.28, 1.5, 7.5)

    assert pi.compute(0.30, 0.0, 0.5) == 7.5
    assert pi.compute(0.0, 0.30, 0.5) == 1.5


def test_pi_nan_measurement_gives_min_output_and_keeps_integral() -> None:
    """An invalid sample never drives the pump and does not poison the integral."""
    pi = PIController(46.8, 1.28, 1.5, 7.5)
    pi.compute(0.10, 0.08, 0.5)
    integral = pi.integral

    assert pi.compute(0.10, math.nan, 0.5) == 1.5
    assert pi.integral == integral
    assert math.isfinite(pi.compute(0.10, 0.10, 0.5))


def test_pi_integral_does_not_wind_up_while_saturated() -> None:
    """While the output is saturated by the error, the integral does not grow."""
    pi = PIController(46.8, 1.28, 0.0, 7.5)

    for _ in range(100):
        pi.compute(0.30, 0.0, 0.5)

    assert pi.integral == 0.0


def test_pi_integral_can_unwind_while_saturated() -> None:
    """A saturated output still lets an opposite error reduce the integral."""
    pi = PIController(46.8, 1.28, 0.0, 7.5)
    pi.integral = 10.0

    pi.compute(0.09, 0.10, 0.5)

    assert pi.integral < 10.0


def test_adapter_converts_cm_to_metres() -> None:
    """The adapter feeds the PI with metres and returns its voltage."""
    adapter = PIRegulationController(PIController(46.8, 1.28, 0.0, 7.5))

    assert adapter.compute(0.5, 10.0, 8.0) == pytest.approx(46.8 * 0.02 + 1.28 * 0.01)


def test_discrete_plant_model_has_finite_stable_state_matrices() -> None:
    Ad, Bd, Cd, h_upper_eq, u_eq = get_discrete_model(
        PlantParams(), target_h_L_m=0.1, sample_period_s=config.CONTROL_PERIOD_S
    )

    assert Ad.shape == (2, 2)
    assert Bd.shape == (2, 1)
    assert Cd.tolist() == [[0.0, 1.0]]
    assert math.isfinite(h_upper_eq) and 0 < h_upper_eq < PlantParams().H
    assert 0 <= u_eq <= config.TOWER_PUMP_MAX_V
    assert all(math.isfinite(float(value)) for value in Ad.flat)
    assert all(math.isfinite(float(value)) for value in Bd.flat)


@pytest.mark.parametrize("target_m", [0.0, -0.1, 0.28, math.nan, math.inf])
def test_discrete_plant_model_rejects_invalid_targets(target_m: float) -> None:
    with pytest.raises(ValueError):
        get_discrete_model(PlantParams(), target_m, config.CONTROL_PERIOD_S)


def test_kalman_observer_estimates_the_unmeasured_upper_tank() -> None:
    params = PlantParams()
    Ad, Bd, Cd, h_upper_eq, u_eq = get_discrete_model(params, 0.1, 0.5)
    equilibrium = np.asarray([[h_upper_eq], [0.1]])
    observer = KalmanFilter(
        Ad,
        Bd,
        Cd,
        np.diag([1e-8, 1e-8]),
        np.asarray([[1e-8]]),
        equilibrium,
        u_eq,
        params.H,
    )
    deviation = np.asarray([[0.01], [0.0]])
    estimate = equilibrium.flatten()
    for _ in range(60):
        deviation = Ad @ deviation
        measurement = float((equilibrium + deviation)[1, 0])
        estimate = observer.update(u_eq, measurement)

    assert estimate[0] == pytest.approx(h_upper_eq + deviation[0, 0], abs=0.002)


def test_mpc_command_respects_voltage_and_slew_constraints() -> None:
    controller = MPCRegulationController()

    command = controller.compute(0.5, 20.0, 10.0)

    assert 0.0 <= command <= config.TOWER_PUMP_MAX_V
    assert command <= config.MPC_RATE_LIMIT_V_S * 0.5

    next_command = controller.compute(0.5, 20.0, 10.0)
    assert abs(next_command - command) <= config.MPC_RATE_LIMIT_V_S * 0.5


def test_mpc_resets_its_output_and_accepts_a_changed_target() -> None:
    controller = MPCRegulationController()
    controller.compute(0.5, 20.0, 10.0)
    controller.reset()

    command = controller.compute(0.5, 12.0, 10.0)

    assert 0.0 <= command <= config.MPC_RATE_LIMIT_V_S * 0.5


def test_service_drives_the_pump_with_the_controller_output() -> None:
    """Each control period reads the tower, runs the controller and writes the pump."""
    controller, daq = _RecordingController(5.0), MockDAQ()
    service = make_service(controller, daq)
    service.regulation_values.tank2_desired_cm = 12.0

    service.toggle_regulation()
    for _ in range(5):
        service.tick(0.1)

    assert controller.reset_count == 1
    assert len(controller.calls) == 1
    dt_s, desired_cm, actual_cm = controller.calls[0]
    assert dt_s == pytest.approx(config.CONTROL_PERIOD_S)
    assert (desired_cm, actual_cm) == (12.0, pytest.approx(10.0))
    assert daq.get_output_voltage(config.TOWER_PUMP_CHANNEL) == 5.0
    assert service.regulation_values.tank2_actual_cm == pytest.approx(10.0)


def test_service_stops_the_pump_when_regulation_is_switched_off() -> None:
    """Switching regulation off sets the pump to 0 V."""
    daq = MockDAQ()
    service = make_service(_RecordingController(5.0), daq)
    service.toggle_regulation()
    for _ in range(5):
        service.tick(0.1)

    service.toggle_regulation()

    assert daq.get_output_voltage(config.TOWER_PUMP_CHANNEL) == 0.0


def test_service_stops_on_hardware_error() -> None:
    """A failing read stops the run, the pump and records the fault."""
    daq = _FailingDAQ()
    service = RegulationService(_RecordingController(5.0), Tower(daq))
    service.toggle_regulation()

    for _ in range(5):
        service.tick(0.1)

    assert not service.is_running
    assert service.fault is not None and "card unplugged" in service.fault
    assert daq.get_output_voltage(config.TOWER_PUMP_CHANNEL) == 0.0


def test_service_reports_a_simulated_tower() -> None:
    """The default tower is simulated, a tower on a DAQ card is not."""
    assert RegulationService().simulated
    assert not make_service(_RecordingController(), MockDAQ()).simulated


def test_service_stops_after_repeated_invalid_readings() -> None:
    """Several NaN readings in a row stop the run."""
    daq = MockDAQ()
    service = make_service(_RecordingController(5.0), daq)
    daq.set_input_voltage(config.TOWER_LEVEL_CHANNEL, math.nan)
    service.toggle_regulation()

    for _ in range(5 * config.MAX_INVALID_SAMPLES):
        service.tick(0.1)

    assert not service.is_running
    assert service.fault is not None


def test_service_records_the_pump_voltage() -> None:
    """The applied pump voltage is shown and stored with every sample."""
    service = make_service(_RecordingController(5.0), MockDAQ())
    service.toggle_regulation()

    for _ in range(25):
        service.tick(0.1)

    assert service.regulation_values.pump_voltage_v == 5.0
    assert service.sample_log.samples[-1].pump_voltage_v == 5.0
    assert not service.pump_at_limit


def test_service_reports_the_output_at_its_limit() -> None:
    """An output clamped to the pump maximum is reported as at the limit."""
    service = make_service(_RecordingController(9.0), MockDAQ())
    service.toggle_regulation()

    for _ in range(5):
        service.tick(0.1)

    assert service.regulation_values.pump_voltage_v == config.TOWER_PUMP_MAX_V
    assert service.pump_at_limit

    service.toggle_regulation()

    assert service.regulation_values.pump_voltage_v == 0.0
    assert not service.pump_at_limit
