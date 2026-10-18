from __future__ import annotations

from dataclasses import dataclass

from .step_metrics import StepMetrics


@dataclass(frozen=True)
class RunStatistics:
    """Energy, efficiency and step responses of one run."""

    duration_s: float
    energy_wh: float
    mean_power_w: float
    efficiency_percent: float | None
    steps: tuple[StepMetrics, ...]
