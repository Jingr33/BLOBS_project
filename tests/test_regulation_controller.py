import math

import pytest

from blobs_project import config
from blobs_project.backend.hardware import HardwareError, MockDAQ, Tower
from blobs_project.backend.regulation import (
    PIController,
    PIRegulationController,
    RegulationControllerBase,
    RegulationService,
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
    level_v = config.TOWER_LEVEL_ZERO_V + 10.0 / config.TOWER_LEVEL_CM_PER_V
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
