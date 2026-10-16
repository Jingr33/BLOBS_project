"""Statistics of one regulation run, computed from its recorded samples."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING

from blobs_project import config

if TYPE_CHECKING:
    from blobs_project.backend.regulation.sample_log import Sample


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


@dataclass(frozen=True)
class RunStatistics:
    """Energy, efficiency and step responses of one run."""

    duration_s: float
    energy_wh: float
    mean_power_w: float
    efficiency_percent: float | None
    steps: tuple[StepMetrics, ...]


def run_statistics(samples: Sequence[Sample]) -> RunStatistics:
    """Return the statistics of the run recorded in ``samples``."""
    if len(samples) < 2:
        return RunStatistics(0.0, 0.0, 0.0, None, ())
    duration_s = samples[-1].time_s - samples[0].time_s
    energy_wh = energy_wh_of(samples)
    mean_power_w = energy_wh * 3600.0 / duration_s if duration_s > 0 else 0.0
    steps = tuple(step_metrics(samples))
    return RunStatistics(
        duration_s, energy_wh, mean_power_w, efficiency_percent(samples), steps
    )


def energy_wh_of(samples: Sequence[Sample]) -> float:
    """Return the pump energy [Wh] as the trapezoidal integral of its power."""
    joules = sum(
        (b.time_s - a.time_s) * (a.pump_power_w + b.pump_power_w) / 2.0
        for a, b in pairwise(samples)
    )
    return joules / 3600.0


def efficiency_percent(samples: Sequence[Sample]) -> float | None:
    """Return the % of time the level was within tolerance of the setpoint.

    The first ``EFFICIENCY_SKIP_S`` after the start and after each setpoint change
    are not counted; ``None`` if no time is left to count.
    """
    counted_s = within_s = 0.0
    change_s = samples[0].time_s if samples else 0.0
    for a, b in pairwise(samples):
        if abs(b.tank2_desired_cm - a.tank2_desired_cm) >= config.STEP_MIN_CM:
            change_s = b.time_s
        if b.time_s - change_s < config.EFFICIENCY_SKIP_S:
            continue
        dt_s = b.time_s - a.time_s
        counted_s += dt_s
        if abs(b.tank2_actual_cm - b.tank2_desired_cm) <= config.EFFICIENCY_TOL_CM:
            within_s += dt_s
    return within_s / counted_s * 100.0 if counted_s > 0 else None


def step_metrics(samples: Sequence[Sample]) -> list[StepMetrics]:
    """Return the metrics of the run start and of every later setpoint step."""
    starts = [0] + [
        i
        for i in range(1, len(samples))
        if abs(samples[i].tank2_desired_cm - samples[i - 1].tank2_desired_cm)
        >= config.STEP_MIN_CM
    ]
    ends = starts[1:] + [len(samples)]
    metrics = (_step(samples[start:end]) for start, end in zip(starts, ends))
    return [m for m in metrics if m is not None]


def _step(part: Sequence[Sample]) -> StepMetrics | None:
    """Return the metrics of one step, or ``None`` if it is too small.

    The response ``ys`` is normalised: 0 at the start level, 1 at the setpoint.
    """
    first = part[0]
    from_cm, to_cm = first.tank2_actual_cm, first.tank2_desired_cm
    size_cm = to_cm - from_cm
    if abs(size_cm) < config.STEP_MIN_CM:
        return None
    times = [s.time_s - first.time_s for s in part]
    ys = [(s.tank2_actual_cm - from_cm) / size_cm for s in part]

    t10 = next((t for t, y in zip(times, ys) if y >= 0.1), None)
    t90 = next((t for t, y in zip(times, ys) if y >= 0.9), None)
    rise_s = t90 - t10 if t10 is not None and t90 is not None else None

    peak = max(range(len(ys)), key=ys.__getitem__)
    overshot = (ys[peak] - 1.0) * abs(size_cm) > config.OVERSHOOT_MIN_CM
    overshoot = (ys[peak] - 1.0) * 100.0 if overshot else 0.0
    peak_s = times[peak] if overshot else None

    min_band = config.SETTLING_BAND_MIN_CM / abs(size_cm)
    band = max(config.SETTLING_BAND_PERCENT / 100.0, min_band)
    outside = [i for i, y in enumerate(ys) if abs(y - 1.0) > band]
    settled = not outside or outside[-1] < len(ys) - 1
    settle_s = times[outside[-1] + 1] if outside and settled else None

    return StepMetrics(
        first.time_s, from_cm, to_cm, rise_s, peak_s, overshoot, settle_s
    )
