from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StepMetrics:
    """Response of the lower-tank level to one setpoint step.

    Times are in seconds from the step; ``None`` means not reached yet.
    """

    start_s: float
    from_cm: float
    to_cm: float
    rise_time_s: float | None
    peak_time_s: float | None
    overshoot_percent: float
    settling_time_s: float | None
