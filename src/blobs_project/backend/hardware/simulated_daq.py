"""Simulated left tower behind the ``DAQ_base`` interface, for running without the card.

The plant is a two-tank cascade with the parameters identified from the
7 Oct 2026 measurements.
"""

import math
import random
import time
from collections.abc import Callable
from dataclasses import dataclass

from blobs_project import config

from .DAQ_base import DAQ_base

Clock = Callable[[], float]

GRAVITY_M_S2 = 9.81


@dataclass(frozen=True)
class PlantParams:
    """Identified plant parameters (SI units)."""

    S: float = math.pi * 0.05**2 / 4.0  # tank cross-section [m^2]
    H: float = 0.28  # tank height [m]; water above it overflows
    c_H: float = 1.47327e-05  # outflow coefficient, upper tank
    c_L: float = 1.11327e-05  # outflow coefficient, lower tank
    r_pump: float = 1.06558e-05  # gain of the pump's power-law characteristic
    s_pump: float = 0.455031  # exponent of the power-law characteristic
    u0_pump: float = 1.56  # voltage above which the pump starts delivering water
    noise_m: float = 0.0  # standard deviation of the sensor noise [m]


def outflow(h: float, c: float) -> float:
    """Return the outflow [m^3/s] at level ``h`` [m] with outflow coefficient ``c``."""
    return c * math.sqrt(2.0 * GRAVITY_M_S2 * max(h, 0.0))


def pump_flow(u: float, p: PlantParams) -> float:
    """Return the pump flow [m^3/s] at control voltage ``u``."""
    if u <= p.u0_pump:
        return 0.0
    return p.r_pump * (u - p.u0_pump) ** p.s_pump


class SimulatedDAQ(DAQ_base):
    """Two-tank cascade driven by the pump output and read by the level input.

    The plant advances in real time by ``clock``.
    """

    STEP_S = 0.05

    def __init__(
        self, params: PlantParams = PlantParams(), clock: Clock = time.monotonic
    ) -> None:
        """Start with both tanks empty and the pump at 0 V."""
        self.params = params
        self.h_upper_m = 0.0
        self.h_lower_m = 0.0
        self._clock = clock
        self._u = 0.0
        self._last_s = clock()

    def open(self) -> None:
        """Restart the plant clock so time spent closed is not simulated."""
        self._last_s = self._clock()

    def close(self) -> None:
        """Nothing to release."""

    def read_voltage(self, channel: str) -> float:
        """Return the level sensor voltage of the lower tank on ``channel``."""
        self._advance()
        h_m = self.h_lower_m + random.gauss(0.0, self.params.noise_m)
        return config.TOWER_LEVEL_ZERO_V + h_m * 100.0 / config.TOWER_LEVEL_CM_PER_V

    def write_voltage(self, channel: str, value: float) -> None:
        """Set the pump control voltage to ``value``."""
        self._advance()
        self._u = value

    def _advance(self) -> None:
        """Integrate the plant up to the current clock time."""
        now = self._clock()
        remaining, self._last_s = now - self._last_s, now
        while remaining > 0:
            dt = min(self.STEP_S, remaining)
            self._step(dt)
            remaining -= dt

    def _step(self, dt: float) -> None:
        """Advance both tanks by ``dt`` seconds (explicit Euler)."""
        p = self.params
        q_upper = outflow(self.h_upper_m, p.c_H)
        q_lower = outflow(self.h_lower_m, p.c_L)
        self.h_upper_m += (pump_flow(self._u, p) - q_upper) * dt / p.S
        self.h_lower_m += (q_upper - q_lower) * dt / p.S
        self.h_upper_m = min(max(self.h_upper_m, 0.0), p.H)
        self.h_lower_m = min(max(self.h_lower_m, 0.0), p.H)
