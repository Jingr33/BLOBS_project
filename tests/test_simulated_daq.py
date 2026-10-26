import pytest

from blobs_project import config
from blobs_project.backend.hardware import SimulatedDAQ, Tower, TowerCalibration


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def settle(volts: float, seconds: float = 600.0) -> float:
    """Return the level above the sensor zero [cm] after ``seconds`` at ``volts``."""
    clock = FakeClock()
    tower = Tower(SimulatedDAQ(clock=clock), TowerCalibration(offset_cm=0.0))
    tower.set_pump_voltage(volts)
    clock.t = seconds
    return tower.read_level_cm()


def test_empty_tank_reads_zero() -> None:
    """The simulated sensor reads 0 cm for an empty tank."""
    assert settle(0.0) == pytest.approx(0.0)


def test_pump_below_threshold_lifts_no_water() -> None:
    """Below 1.56 V the pump delivers nothing."""
    assert settle(1.5) == pytest.approx(0.0)


def test_steady_levels_match_the_measured_range() -> None:
    """Steady levels are close to the 7 Oct sweep (9.3 / 13.7 / 17.9 cm)."""
    assert settle(4.0) == pytest.approx(10.5, abs=1.5)
    assert settle(5.0) == pytest.approx(14.0, abs=2.0)
    assert settle(6.0) == pytest.approx(18.0, abs=2.5)


def test_level_rises_with_the_pump_voltage() -> None:
    """A higher pump voltage gives a higher steady level."""
    levels = [settle(u) for u in (3.0, 4.0, 5.0, 6.0, 7.0)]
    assert levels == sorted(levels)
    assert levels[-1] < config.TANK_LEVEL_MAX_CM
