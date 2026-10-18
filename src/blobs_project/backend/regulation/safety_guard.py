from __future__ import annotations

import math

from blobs_project import config


class SafetyGuard:
    """Setpoint limits and the checks that stop a run on a bad level."""

    def __init__(self) -> None:
        self._invalid_samples = 0

    def reset(self) -> None:
        """Forget invalid readings of the previous run."""
        self._invalid_samples = 0

    def check_level(self, level_cm: float) -> str | None:
        """Return why the run must stop at ``level_cm``, or ``None``.

        A non-finite level is an invalid reading; only several in a row stop it.
        """
        if not math.isfinite(level_cm):
            self._invalid_samples += 1
            if self._invalid_samples >= config.MAX_INVALID_SAMPLES:
                return f"{self._invalid_samples} invalid level readings"
            return None
        self._invalid_samples = 0
        if level_cm >= config.LEVEL_TRIP_CM:
            return f"level {level_cm:.1f} cm reached {config.LEVEL_TRIP_CM} cm"
        return None

    @staticmethod
    def clamp_setpoint_cm(level_cm: float) -> float:
        """Return ``level_cm`` limited to the allowed setpoint range."""
        return min(max(level_cm, config.SETPOINT_MIN_CM), config.SETPOINT_MAX_CM)

    @staticmethod
    def overflow_warning(level_cm: float) -> bool:
        """Return whether ``level_cm`` is close to overflowing the lower tank."""
        return level_cm >= config.LEVEL_WARNING_CM

    @staticmethod
    def at_pump_limit(volts: float) -> bool:
        """Return whether the controller output ``volts`` is at a limit."""
        return volts <= config.PI_MIN_V or volts >= config.TOWER_PUMP_MAX_V
