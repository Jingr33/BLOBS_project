"""Recorded regulation run as a CSV file that can be imported again."""

from __future__ import annotations

from collections.abc import Sequence

from blobs_project.backend.regulation.sample_log import Sample

from .csv_cells import parse_number, split_cells
from .csv_profile_error import CsvProfileError

RUN_COLUMNS = (
    "time_s",
    "desired_cm",
    "actual_cm",
    "pump_voltage_v",
    "pump_power_w",
    "flow_l_min",
)
_ALIASES = {"tank2_actual_cm": "actual_cm", "tank2_desired_cm": "desired_cm"}


def run_to_text(samples: Sequence[Sample]) -> str:
    """Return ``samples`` as ``;``-separated CSV with a decimal comma (Czech Excel)."""
    lines = [";".join(RUN_COLUMNS)]
    for s in samples:
        values = (
            f"{s.time_s:.1f}",
            f"{s.tank2_desired_cm:.2f}",
            f"{s.tank2_actual_cm:.2f}",
            f"{s.pump_voltage_v:.3f}",
            f"{s.pump_power_w:.3f}",
            f"{s.flow_l_min:.3f}",
        )
        lines.append(";".join(values).replace(".", ","))
    return "\n".join(lines) + "\n"


def is_run_text(text: str) -> bool:
    """Return whether ``text`` is a recorded run (its header has ``time_s``)."""
    first = next((line for line in text.splitlines() if line.strip()), "")
    return "time_s" in split_cells(first)


def run_from_text(text: str) -> tuple[Sample, ...]:
    """Return the samples of a recorded run.

    Only ``time_s`` and ``actual_cm`` are required; a missing setpoint is the level
    itself and other missing columns are 0. Raises ``CsvProfileError`` if invalid.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise CsvProfileError("file is empty")
    header = [_ALIASES.get(name, name) for name in split_cells(lines[0])]
    if "time_s" not in header or "actual_cm" not in header:
        raise CsvProfileError("header needs time_s and actual_cm columns")
    samples = []
    for line_number, line in enumerate(lines[1:], start=2):
        cells = split_cells(line)
        if len(cells) != len(header):
            raise CsvProfileError(f"line {line_number}: expected {len(header)} columns")
        try:
            row = dict(zip(header, map(parse_number, cells)))
        except ValueError as error:
            raise CsvProfileError(f"line {line_number}: {error}") from error
        actual = row["actual_cm"]
        desired = row.get("desired_cm", actual)
        flow, power, volts = (
            row.get(name, 0.0)
            for name in ("flow_l_min", "pump_power_w", "pump_voltage_v")
        )
        samples.append(Sample(row["time_s"], desired, actual, flow, power, volts))
    if not samples:
        raise CsvProfileError("run contains no samples")
    return tuple(samples)
