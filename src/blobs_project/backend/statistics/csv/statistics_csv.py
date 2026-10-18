from __future__ import annotations

import csv
import io

from blobs_project.backend.dtos import RunStatistics

from .step_column import StepColumn
from .summary_column import SummaryColumn


class StatisticsCsv:
    @staticmethod
    def to_text(statistics: RunStatistics) -> str:
        """Return the run summary and the step table, separated by an empty row."""
        s, cell = statistics, StatisticsCsv._cell
        out = io.StringIO()
        summary = csv.DictWriter(out, list(SummaryColumn), lineterminator="\n")
        summary.writeheader()
        summary.writerow(
            {
                SummaryColumn.RUN_TIME_S: cell(s.duration_s, 1),
                SummaryColumn.ENERGY_WH: cell(s.energy_wh, 3),
                SummaryColumn.MEAN_POWER_W: cell(s.mean_power_w, 2),
                SummaryColumn.WITHIN_1MM_PERCENT: cell(s.efficiency_percent, 1),
            }
        )
        out.write("\n")
        steps = csv.DictWriter(out, list(StepColumn), lineterminator="\n")
        steps.writeheader()
        for step in s.steps:
            steps.writerow(
                {
                    StepColumn.STEP_START_S: cell(step.start_s, 0),
                    StepColumn.FROM_CM: cell(step.from_cm, 2),
                    StepColumn.TO_CM: cell(step.to_cm, 2),
                    StepColumn.RISE_S: cell(step.rise_time_s, 0),
                    StepColumn.PEAK_S: cell(step.peak_time_s, 0),
                    StepColumn.OVERSHOOT_PERCENT: cell(step.overshoot_percent, 1),
                    StepColumn.SETTLING_S: cell(step.settling_time_s, 0),
                }
            )
        return out.getvalue()

    @staticmethod
    def _cell(value: float | None, digits: int) -> str:
        """Return ``value`` with ``digits`` decimals; ``None`` is an empty cell."""
        return "" if value is None else f"{value:.{digits}f}"
