from __future__ import annotations

import csv
import io
import math
from collections.abc import Sequence

from blobs_project.backend.dtos import Sample
from blobs_project.backend.regulation.csv_error import CsvError

from .run_column import RunColumn


class RunCsv:
    """Recorded regulation run as a CSV file that can be imported again."""

    @staticmethod
    def is_run(text: str) -> bool:
        """Return whether ``text`` is a recorded run rather than a profile."""
        rows = csv.reader(text.splitlines(), strict=True)
        try:
            header = next(
                (row for row in rows if any(cell.strip() for cell in row)), []
            )
        except csv.Error as error:
            raise CsvError(
                f"line {rows.line_num}: invalid CSV syntax: {error}"
            ) from error
        return RunColumn.TIME_S.value in (cell.strip() for cell in header)

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
        rows = csv.reader(text.splitlines(), strict=True)
        try:
            header = next(
                (row for row in rows if any(cell.strip() for cell in row)), []
            )
            header = [cell.strip() for cell in header]
            missing = [column.value for column in RunColumn if column not in header]
            if missing:
                raise CsvError(
                    "recorded run header is missing required column(s): "
                    + ", ".join(missing)
                )
            column_indices = {
                column: header.index(column.value) for column in RunColumn
            }
            samples: list[Sample] = []
            for row in rows:
                line_number = rows.line_num
                if not row or not any(cell.strip() for cell in row):
                    continue
                if len(row) != len(header):
                    raise CsvError(
                        f"line {line_number}: expected {len(header)} columns, "
                        f"found {len(row)}"
                    )
                values: dict[RunColumn, float] = {}
                for column, index in column_indices.items():
                    cell = row[index].strip()
                    try:
                        value = float(cell)
                    except ValueError as error:
                        raise CsvError(
                            f"line {line_number}: {column.value} value {cell!r} "
                            "is not a number"
                        ) from error
                    if not math.isfinite(value):
                        raise CsvError(
                            f"line {line_number}: {column.value} value {cell!r} "
                            "must be finite"
                        )
                    values[column] = value
                samples.append(
                    Sample(
                        time_s=values[RunColumn.TIME_S],
                        tank2_desired_cm=values[RunColumn.DESIRED_CM],
                        tank2_actual_cm=values[RunColumn.ACTUAL_CM],
                        flow_l_min=values[RunColumn.FLOW_L_MIN],
                        pump_power_w=values[RunColumn.PUMP_POWER_W],
                        pump_voltage_v=values[RunColumn.PUMP_VOLTAGE_V],
                    )
                )
        except csv.Error as error:
            raise CsvError(
                f"line {rows.line_num}: invalid CSV syntax: {error}"
            ) from error
        if not samples:
            raise CsvError("recorded run contains no sample rows")
        return tuple(samples)
