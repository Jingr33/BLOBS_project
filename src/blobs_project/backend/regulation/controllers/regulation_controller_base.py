from __future__ import annotations

from abc import ABC, abstractmethod


class RegulationControllerBase(ABC):
    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        pass
