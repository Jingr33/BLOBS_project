from __future__ import annotations

import csv
import math
from dataclasses import dataclass, replace
from typing import ClassVar

from blobs_project import config
from blobs_project.backend.regulation.csv_error import CsvError


@dataclass(frozen=True)
class CsvProfile:
    """Profile of desired levels, each held for ``step_s`` seconds."""

    _HEADERS: ClassVar[frozenset[str]] = frozenset(
        {
            "hladina_cm",
            "level",
            "level_cm",
            "level [cm]",
            "desired_cm",
            "desired_level_cm",
            "tank2_level_cm",
        }
    )

    tank2_levels: tuple[float, ...]
    step_s: float = config.PROFILE_STEP_S

    def __post_init__(self) -> None:
        if not self.tank2_levels:
            raise ValueError("profile must contain at least one level")
        if not math.isfinite(self.step_s) or self.step_s <= 0:
            raise ValueError("profile step duration must be finite and positive")
        low, high = config.SETPOINT_MIN_CM, config.SETPOINT_MAX_CM
        if any(
            not math.isfinite(level) or not low <= level <= high
            for level in self.tank2_levels
        ):
            raise ValueError(
                f"profile levels must be finite and between {low:g}-{high:g} cm"
            )

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
        step_s = config.PROFILE_STEP_S
        duration_seen = False

        rows = csv.reader(text.splitlines(), strict=True)
        try:
            for row in rows:
                line_number = rows.line_num
                cells = [cell.strip() for cell in row]
                if not cells or not any(cells):
                    continue
                if cells[0].startswith("#"):
                    comment = cells[0][1:].strip()
                    if comment.casefold().startswith("step_duration_min"):
                        key, separator, value = comment.partition("=")
                        if (
                            key.strip().casefold() != "step_duration_min"
                            or not separator
                        ):
                            raise CsvError(
                                f"line {line_number}: expected "
                                "# step_duration_min=<minutes>"
                            )
                        if duration_seen:
                            raise CsvError(
                                f"line {line_number}: step_duration_min is specified "
                                "more than once"
                            )
                        duration_seen = True
                        value = value.strip()
                        if not cls._is_number(value):
                            raise CsvError(
                                f"line {line_number}: step_duration_min value "
                                f"{value!r} is not a number"
                            )
                        duration_min = float(value)
                        if not math.isfinite(duration_min):
                            raise CsvError(
                                f"line {line_number}: step_duration_min must be finite"
                            )
                        low = config.PROFILE_MIN_STEP_S / 60.0
                        high = config.PROFILE_MAX_STEP_S / 60.0
                        if not low <= duration_min <= high:
                            raise CsvError(
                                f"line {line_number}: step_duration_min "
                                f"{duration_min:g} is outside the allowed range "
                                f"{low:g}-{high:g} minutes"
                            )
                        step_s = duration_min * 60.0
                    continue
                if len(cells) != 1:
                    raise CsvError(
                        f"line {line_number}: expected 1 column with one level in cm; "
                        f"found {len(cells)}"
                    )
                cell = cells[0]
                if not cls._is_number(cell):
                    if not tank2_values and not skipped_header:
                        if cell.casefold() not in cls._HEADERS:
                            raise CsvError(
                                f"line {line_number}: unrecognized profile header "
                                f"or level {cell!r}; expected a numeric level in cm"
                            )
                        skipped_header = True
                        continue
                    raise CsvError(
                        f"line {line_number}: level {cell!r} is not a number"
                    )
                level = float(cell)
                if not math.isfinite(level):
                    raise CsvError(
                        f"line {line_number}: level {cell!r} must be a finite number"
                    )
                low, high = config.SETPOINT_MIN_CM, config.SETPOINT_MAX_CM
                if not low <= level <= high:
                    raise CsvError(
                        f"line {line_number}: level {level:g} cm is outside "
                        f"the allowed range {low:g}-{high:g} cm"
                    )
                tank2_values.append(level)
        except csv.Error as error:
            raise CsvError(
                f"line {rows.line_num}: invalid CSV syntax: {error}"
            ) from error

        if not tank2_values:
            raise CsvError(
                "profile contains no numeric levels; add one desired level in cm "
                "per row"
            )
        return cls(tuple(tank2_values), step_s=step_s)

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
