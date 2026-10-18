from __future__ import annotations

import csv
import io
from collections.abc import Sequence

from blobs_project.backend.dtos import Sample
from blobs_project.backend.regulation.csv_error import CsvError

from .run_column import RunColumn


class RunCsv:
    """Recorded regulation run as a CSV file that can be imported again."""

    @staticmethod
    def is_run(text: str) -> bool:
        """Return whether ``text`` is a recorded run rather than a profile."""
        header = next(csv.reader(line for line in text.splitlines() if line), [])
        return RunColumn.TIME_S in header

    @staticmethod
    def to_text(samples: Sequence[Sample]) -> str:
        """Return ``samples`` as CSV with a header of ``RunColumn`` names."""
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=list(RunColumn), lineterminator="\n")
        writer.writeheader()
        for s in samples:
            writer.writerow(
                {
                    RunColumn.TIME_S: f"{s.time_s:.1f}",
                    RunColumn.DESIRED_CM: f"{s.tank2_desired_cm:.2f}",
                    RunColumn.ACTUAL_CM: f"{s.tank2_actual_cm:.2f}",
                    RunColumn.PUMP_VOLTAGE_V: f"{s.pump_voltage_v:.3f}",
                    RunColumn.PUMP_POWER_W: f"{s.pump_power_w:.3f}",
                    RunColumn.FLOW_L_MIN: f"{s.flow_l_min:.3f}",
                }
            )
        return out.getvalue()

    @staticmethod
    def from_text(text: str) -> tuple[Sample, ...]:
        """Return the samples of a recorded run; ``CsvError`` if invalid."""
        try:
            samples = tuple(
                Sample(
                    time_s=float(row[RunColumn.TIME_S]),
                    tank2_desired_cm=float(row[RunColumn.DESIRED_CM]),
                    tank2_actual_cm=float(row[RunColumn.ACTUAL_CM]),
                    flow_l_min=float(row[RunColumn.FLOW_L_MIN]),
                    pump_power_w=float(row[RunColumn.PUMP_POWER_W]),
                    pump_voltage_v=float(row[RunColumn.PUMP_VOLTAGE_V]),
                )
                for row in csv.DictReader(text.splitlines())
            )
        except (KeyError, TypeError, ValueError) as error:
            raise CsvError(f"invalid run: {error}") from error
        if not samples:
            raise CsvError("run contains no samples")
        return samples
