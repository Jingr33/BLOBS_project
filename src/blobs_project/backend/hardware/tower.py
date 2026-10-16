"""The left tower as a plant: lower-tank level in cm and pump voltage."""

import logging
import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

from blobs_project import config

from .DAQ_base import DAQ_base
from .hardware_error import HardwareError

logger = logging.getLogger(__name__)

Sleep = Callable[[float], None]


@dataclass(frozen=True)
class TowerCalibration:
    """Channel mapping, sensor calibration and pump cap of one tower."""

    level_channel: str = config.TOWER_LEVEL_CHANNEL
    pump_channel: str = config.TOWER_PUMP_CHANNEL
    cm_per_v: float = config.TOWER_LEVEL_CM_PER_V
    zero_v: float = config.TOWER_LEVEL_ZERO_V
    offset_cm: float = config.TOWER_LEVEL_OFFSET_CM
    max_pump_v: float = config.TOWER_PUMP_MAX_V


class Tower:
    """Calibrated, safe access to one tower through any ``DAQ_base``.

    The pump is clamped to ``[0, cal.max_pump_v]`` and set to 0 V on open and close.
    """

    def __init__(
        self, daq: DAQ_base, cal: TowerCalibration = TowerCalibration()
    ) -> None:
        """Wrap ``daq`` with the channels and calibration in ``cal``."""
        self._daq = daq
        self._cal = cal
        self._zero_v = cal.zero_v
        self._pump_voltage = 0.0

    @property
    def daq(self) -> DAQ_base:
        """Return the DAQ the tower reads and writes through."""
        return self._daq

    @property
    def pump_voltage(self) -> float:
        """Return the last pump voltage that was actually written."""
        return self._pump_voltage

    @property
    def zero_v(self) -> float:
        """Return the sensor voltage that reads as 0 cm."""
        return self._zero_v

    def open(self) -> None:
        """Open the DAQ and set the pump to 0 V; close the DAQ again if that fails."""
        self._daq.open()
        try:
            self.stop_pump()
        except BaseException:
            self._daq.close()
            raise

    def close(self) -> None:
        """Set the pump to 0 V, then close the DAQ even if that write fails."""
        try:
            self.stop_pump()
        finally:
            self._daq.close()

    def __enter__(self) -> Self:
        """Open the tower and return it."""
        self.open()
        return self

    def __exit__(self, _type: object, exc: BaseException | None, _tb: object) -> None:
        """Close the tower on any exit; a close failure never hides ``exc``."""
        if exc is None:
            self.close()
            return
        try:
            self.close()
        except HardwareError:
            logger.exception("closing the tower failed while handling %r", exc)

    def read_level_cm(self) -> float:
        """Return the lower-tank level in cm above the tank bottom."""
        level_cm = (self.read_level_v() - self._zero_v) * self._cal.cm_per_v
        return level_cm + self._cal.offset_cm

    def set_pump_voltage(self, volts: float) -> float:
        """Clamp ``volts`` to the safe range, write it and return the applied value.

        Raises ``ValueError`` if not finite, ``HardwareError`` if the write fails.
        """
        if not math.isfinite(volts):
            raise ValueError(f"pump voltage must be finite, got {volts}")
        applied = min(max(volts, 0.0), self._cal.max_pump_v)
        self._daq.write_voltage(self._cal.pump_channel, applied)
        self._pump_voltage = applied
        return applied

    def stop_pump(self) -> None:
        """Set the pump to 0 V."""
        self.set_pump_voltage(0.0)

    def tare(
        self, samples: int = 20, interval_s: float = 0.5, sleep: Sleep = time.sleep
    ) -> float:
        """Average ``samples`` readings of the empty tank and return the new zero.

        Raises ``ValueError`` if ``samples`` is below 1.
        """
        if samples < 1:
            raise ValueError("samples must be >= 1")
        total = 0.0
        for i in range(samples):
            if i:
                sleep(interval_s)
            total += self.read_level_v()
        self._zero_v = total / samples
        return self._zero_v

    def read_level_v(self) -> float:
        """Return the raw level sensor voltage (what ``tare`` averages)."""
        return self._daq.read_voltage(self._cal.level_channel)
