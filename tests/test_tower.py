"""Tests for the ``Tower`` plant interface over ``MockDAQ``."""

from typing import Any

import pytest

from blobs_project import config
from blobs_project.backend import HardwareError, MockDAQ, Tower, TowerCalibration


class _FailingWriteDAQ(MockDAQ):
    """Mock DAQ whose analog writes raise once ``fail_writes`` is set."""

    def __init__(self) -> None:
        """Start with writes working."""
        super().__init__()
        self.fail_writes = False

    def write_voltage(self, channel: str, value: float) -> None:
        """Raise ``HardwareError`` if ``fail_writes``, else record ``value``."""
        if self.fail_writes:
            raise HardwareError("write failed")
        super().write_voltage(channel, value)


def make_tower(daq: MockDAQ | None = None, **kw: Any) -> tuple[Tower, MockDAQ]:
    """Return a ``Tower`` over ``daq`` (a new ``MockDAQ`` if None) and the DAQ."""
    daq = daq if daq is not None else MockDAQ()
    kw.setdefault("offset_cm", 0.0)
    return Tower(daq, TowerCalibration(**kw)), daq


def test_level_conversion() -> None:
    """With the default gain 3.255 V on ai0 is 3 V above the zero."""
    tower, daq = make_tower()
    daq.set_input_voltage("ai0", 3.255)

    assert tower.read_level_cm() == pytest.approx(3.0 * config.TOWER_LEVEL_CM_PER_V)


def test_level_is_measured_from_the_tank_bottom() -> None:
    """``offset_cm`` is added to the level above the sensor zero."""
    tower, daq = make_tower(cm_per_v=2.0, zero_v=1.0, offset_cm=1.35)
    daq.set_input_voltage("ai0", 2.0)

    assert tower.read_level_cm() == pytest.approx(3.35)


def test_custom_calibration() -> None:
    """``cm_per_v`` and ``zero_v`` from the constructor are used."""
    tower, daq = make_tower(cm_per_v=2.0, zero_v=1.0)
    daq.set_input_voltage("ai0", 2.0)

    assert tower.read_level_cm() == pytest.approx(2.0)


def test_pump_clamped_high() -> None:
    """A request above 7.5 V applies 7.5 V on ao1."""
    tower, daq = make_tower()

    assert tower.set_pump_voltage(9.0) == 7.5
    assert daq.get_output_voltage("ao1") == 7.5
    assert tower.pump_voltage == 7.5


def test_pump_clamped_low() -> None:
    """A negative request applies 0 V."""
    tower, _ = make_tower()

    assert tower.set_pump_voltage(-1.0) == 0.0


def test_pump_nan_rejected() -> None:
    """NaN raises ``ValueError`` and leaves the output unchanged."""
    tower, daq = make_tower()
    tower.set_pump_voltage(3.0)

    with pytest.raises(ValueError):
        tower.set_pump_voltage(float("nan"))
    assert daq.get_output_voltage("ao1") == 3.0


def test_stop_pump() -> None:
    """``stop_pump`` sets ao1 to 0 V."""
    tower, daq = make_tower()
    tower.set_pump_voltage(5.0)

    tower.stop_pump()

    assert daq.get_output_voltage("ao1") == 0.0


def test_tare_averages() -> None:
    """``tare`` averages raw ai0, sleeps between samples and sets the zero."""
    tower, daq = make_tower()
    daq.set_input_voltage("ai0", 0.24)
    sleeps: list[float] = []

    zero = tower.tare(samples=4, interval_s=0.1, sleep=sleeps.append)

    assert zero == pytest.approx(0.24)
    assert tower.zero_v == pytest.approx(0.24)
    assert sleeps == [0.1] * 3
    assert tower.read_level_cm() == pytest.approx(0.0)


def test_tare_rejects_zero_samples() -> None:
    """``tare`` needs at least one sample."""
    tower, _ = make_tower()

    with pytest.raises(ValueError):
        tower.tare(samples=0)


def test_context_manager_lifecycle() -> None:
    """``with`` opens the DAQ at 0 V and closes it with the pump off."""
    tower, daq = make_tower()
    daq.write_voltage("ao1", 5.0)

    with tower:
        assert daq.is_open
        assert daq.get_output_voltage("ao1") == 0.0
        tower.set_pump_voltage(4.0)

    assert daq.get_output_voltage("ao1") == 0.0
    assert not daq.is_open


def test_exception_in_with_stops_pump() -> None:
    """Ctrl+C inside ``with`` still stops the pump and closes the DAQ."""
    tower, daq = make_tower()

    with pytest.raises(KeyboardInterrupt):
        with tower:
            tower.set_pump_voltage(5.0)
            raise KeyboardInterrupt

    assert daq.get_output_voltage("ao1") == 0.0
    assert not daq.is_open


def test_close_closes_daq_when_pump_write_fails() -> None:
    """If stopping the pump fails, ``close`` still closes the DAQ and raises."""
    daq = _FailingWriteDAQ()
    tower, _ = make_tower(daq)
    tower.open()
    daq.fail_writes = True

    with pytest.raises(HardwareError):
        tower.close()
    assert not daq.is_open


def test_failed_write_keeps_pump_voltage() -> None:
    """A failed write leaves ``pump_voltage`` at the last applied value."""
    daq = _FailingWriteDAQ()
    tower, _ = make_tower(daq)
    tower.set_pump_voltage(3.0)
    daq.fail_writes = True

    with pytest.raises(HardwareError):
        tower.set_pump_voltage(5.0)
    assert tower.pump_voltage == 3.0


def test_pump_inf_rejected() -> None:
    """Infinity raises ``ValueError`` instead of running the pump at the cap."""
    tower, daq = make_tower()
    tower.set_pump_voltage(3.0)

    with pytest.raises(ValueError):
        tower.set_pump_voltage(float("inf"))
    assert daq.get_output_voltage("ao1") == 3.0


def test_open_closes_daq_when_pump_write_fails() -> None:
    """If the 0 V write in ``open`` fails, the DAQ is closed again."""
    daq = _FailingWriteDAQ()
    daq.fail_writes = True
    tower, _ = make_tower(daq)

    with pytest.raises(HardwareError):
        tower.open()
    assert not daq.is_open


def test_close_error_does_not_replace_interrupt() -> None:
    """Ctrl+C inside ``with`` propagates even if stopping the pump fails."""
    daq = _FailingWriteDAQ()
    tower, _ = make_tower(daq)

    with pytest.raises(KeyboardInterrupt):
        with tower:
            daq.fail_writes = True
            raise KeyboardInterrupt
    assert not daq.is_open
