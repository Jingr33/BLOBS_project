from __future__ import annotations

import csv
from dataclasses import dataclass, replace

from blobs_project import config
from blobs_project.backend.regulation.csv_error import CsvError


@dataclass(frozen=True)
class CsvProfile:
    """Profile of desired levels, each held for ``step_s`` seconds."""

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

        rows = csv.reader(text.splitlines())
        for line_number, row in enumerate(rows, start=1):
            cells = [cell.strip() for cell in row if cell.strip()]
            if not cells:
                continue
            if not all(cls._is_number(cell) for cell in cells):
                if not tank2_values and not skipped_header:
                    skipped_header = True
                    continue
                raise CsvError(f"line {line_number}: expected numeric level values")
            if len(cells) != 1:
                raise CsvError(f"line {line_number}: expected 1 column")
            level = float(cells[0])
            low, high = config.SETPOINT_MIN_CM, config.SETPOINT_MAX_CM
            if not low <= level <= high:
                raise CsvError(
                    f"line {line_number}: level {level} cm is outside {low}-{high} cm"
                )
            tank2_values.append(level)

        if not tank2_values:
            raise CsvError("profile contains no rows")
        return cls(tuple(tank2_values))

    def desired_at(self, elapsed_s: float) -> float:
        return self.tank2_levels[self.step_at(elapsed_s)]

    def points(self) -> list[tuple[float, float]]:
        """Return the desired level over the whole profile as chart points."""
        points = []
        for index, level in enumerate(self.tank2_levels):
            points += [(index * self.step_s, level), ((index + 1) * self.step_s, level)]
        return points

    def step_at(self, elapsed_s: float) -> int:
        """Return the index of the step that is active at ``elapsed_s``."""
        index = int(elapsed_s / self.step_s) if elapsed_s > 0 else 0
        return min(index, self.row_count - 1)

    @staticmethod
    def _is_number(cell: str) -> bool:
        try:
            float(cell)
        except ValueError:
            return False
        return True
