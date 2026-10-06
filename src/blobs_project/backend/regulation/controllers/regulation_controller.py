from __future__ import annotations

from typing import Protocol


class RegulationController(Protocol):
    def reset(self) -> None:
        pass

    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        pass
