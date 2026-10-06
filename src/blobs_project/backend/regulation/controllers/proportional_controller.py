from __future__ import annotations

from .... import configuration as config


class ProportionalController:
    def __init__(self, gain: float = config.LEVEL_RESPONSE_RATE) -> None:
        self._gain = gain

    def reset(self) -> None:
        pass

    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        step = min(1.0, dt_s * self._gain)
        return (desired_cm - actual_cm) * step
