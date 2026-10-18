from __future__ import annotations

from abc import ABC, abstractmethod


class ControllerError(Exception):
    """A controller model or solver failure that must stop regulation."""


class RegulationControllerBase(ABC):
    """Level controller: turns the desired and measured level into a pump voltage."""

    @abstractmethod
    def reset(self) -> None:
        """Forget the state of the previous run."""
        pass

    @abstractmethod
    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        """Return the pump voltage after ``dt_s`` seconds of control."""
        pass
