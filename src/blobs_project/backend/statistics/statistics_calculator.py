"""Statistics of one regulation run, computed from its recorded samples."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise

from blobs_project import config
from blobs_project.backend.dtos import RunStatistics, Sample, StepMetrics


class StatisticsCalculator:
    @staticmethod
    def calculate(samples: Sequence[Sample]) -> RunStatistics:
        """Return the statistics of the run recorded in ``samples``."""
        if len(samples) < 2:
            return RunStatistics(0.0, 0.0, 0.0, None, ())
        duration_s = samples[-1].time_s - samples[0].time_s
        energy_wh = StatisticsCalculator._energy_wh(samples)
        mean_power_w = energy_wh * 3600.0 / duration_s if duration_s > 0 else 0.0
        efficiency = StatisticsCalculator._efficiency_percent(samples)
        steps = tuple(StatisticsCalculator._step_metrics(samples))
        return RunStatistics(duration_s, energy_wh, mean_power_w, efficiency, steps)

    @staticmethod
    def _energy_wh(samples: Sequence[Sample]) -> float:
        """Return the pump energy [Wh] as the integral of its power."""
        joules = sum(
            (b.time_s - a.time_s) * (a.pump_power_w + b.pump_power_w) / 2.0
            for a, b in pairwise(samples)
        )
        return joules / 3600.0

    @staticmethod
    def _efficiency_percent(samples: Sequence[Sample]) -> float | None:
        """Return the % of time the level was within tolerance of the setpoint.

        The first ``EFFICIENCY_SKIP_S`` after the start and after each setpoint
        change are not counted; ``None`` if no time is left to count.
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
            error_cm = abs(b.tank2_actual_cm - b.tank2_desired_cm)
            if error_cm <= config.EFFICIENCY_TOL_CM:
                within_s += dt_s
        return within_s / counted_s * 100.0 if counted_s > 0 else None

    @staticmethod
    def _step_metrics(samples: Sequence[Sample]) -> list[StepMetrics]:
        """Return the metrics of the run start and of every later setpoint step."""
        starts = [0] + [
            i
            for i in range(1, len(samples))
            if abs(samples[i].tank2_desired_cm - samples[i - 1].tank2_desired_cm)
            >= config.STEP_MIN_CM
        ]
        ends = starts[1:] + [len(samples)]
        parts = (samples[start:end] for start, end in zip(starts, ends))
        metrics = (StatisticsCalculator._step(part) for part in parts)
        return [m for m in metrics if m is not None]

    @staticmethod
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
