from __future__ import annotations

from blobs_project import config

from .regulation_controller_base import RegulationControllerBase


class ProportionalController(RegulationControllerBase):
    def __init__(self, gain: float = config.LEVEL_RESPONSE_RATE) -> None:
        self._gain = gain

    def reset(self) -> None:
        pass

    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        step = min(1.0, dt_s * self._gain)
        return (desired_cm - actual_cm) * step
