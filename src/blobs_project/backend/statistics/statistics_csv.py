"""Run statistics as a CSV file for Excel (``;`` and decimal comma)."""

from __future__ import annotations

from .run_statistics import RunStatistics

SUMMARY_COLUMNS = ("run_time_s", "energy_wh", "mean_power_w", "within_1mm_percent")
STEP_COLUMNS = (
    "step_start_s",
    "from_cm",
    "to_cm",
    "rise_s",
    "peak_s",
    "overshoot_percent",
    "settling_s",
)


def statistics_to_text(statistics: RunStatistics) -> str:
    """Return the run summary and the step table, separated by an empty line."""
    s = statistics
    summary = (s.duration_s, s.energy_wh, s.mean_power_w, s.efficiency_percent)
    lines = [";".join(SUMMARY_COLUMNS), _row(summary, (1, 3, 2, 1)), ""]
    lines.append(";".join(STEP_COLUMNS))
    for step in s.steps:
        values = (
            step.start_s,
            step.from_cm,
            step.to_cm,
            step.rise_time_s,
            step.peak_time_s,
            step.overshoot_percent,
            step.settling_time_s,
        )
        lines.append(_row(values, (0, 2, 2, 0, 0, 1, 0)))
    return "\n".join(lines) + "\n"


def _row(values: tuple[float | None, ...], decimals: tuple[int, ...]) -> str:
    """Join ``values`` with ``;`` and a decimal comma; ``None`` is an empty cell."""
    cells = ("" if v is None else f"{v:.{d}f}" for v, d in zip(values, decimals))
    return ";".join(cells).replace(".", ",")
