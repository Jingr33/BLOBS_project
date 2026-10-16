from __future__ import annotations

from dataclasses import dataclass, replace

from blobs_project import config

from .csv_cells import is_number, parse_number, split_cells
from .csv_profile_error import CsvProfileError


@dataclass(frozen=True)
class CsvProfile:
    """Scenario of desired levels, each held for ``step_s`` seconds."""

    tank2_levels: tuple[float, ...]
    step_s: float = config.PROFILE_STEP_S

    @property
    def row_count(self) -> int:
        return len(self.tank2_levels)

    @property
    def duration_s(self) -> float:
        return self.row_count * self.step_s

    def with_step(self, step_s: float) -> CsvProfile:
        """Return the same levels, each held for ``step_s`` seconds."""
        return replace(self, step_s=step_s)

    @classmethod
    def from_text(cls, text: str) -> CsvProfile:
        tank2_values: list[float] = []
        skipped_header = False

        for line_number, line in enumerate(text.splitlines(), start=1):
            cells = split_cells(line)
            if not cells:
                continue
            if not all(is_number(cell) for cell in cells):
                if not tank2_values and not skipped_header:
                    skipped_header = True
                    continue
                raise CsvProfileError(
                    f"line {line_number}: expected numeric level values"
                )
            if len(cells) != 1:
                raise CsvProfileError(f"line {line_number}: expected 1 column")
            level = parse_number(cells[0])
            low, high = config.SETPOINT_MIN_CM, config.SETPOINT_MAX_CM
            if not low <= level <= high:
                raise CsvProfileError(
                    f"line {line_number}: level {level} cm is outside {low}-{high} cm"
                )
            tank2_values.append(level)

        if not tank2_values:
            raise CsvProfileError("profile contains no rows")
        return cls(tuple(tank2_values))

    def desired_at(self, elapsed_s: float) -> float:
        return self.tank2_levels[self.step_at(elapsed_s)]

    def step_at(self, elapsed_s: float) -> int:
        """Return the index of the step that is active at ``elapsed_s``."""
        index = int(elapsed_s / self.step_s) if elapsed_s > 0 else 0
        return min(index, self.row_count - 1)
