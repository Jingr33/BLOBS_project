from __future__ import annotations

from dataclasses import dataclass

from .... import configuration as config
from .csv_profile_error import CsvProfileError


@dataclass(frozen=True)
class CsvProfile:
    tank2_levels: tuple[float, ...]

    @property
    def row_count(self) -> int:
        return len(self.tank2_levels)

    @property
    def duration_s(self) -> float:
        return self.row_count * config.PROFILE_SAMPLE_INTERVAL_S

    @classmethod
    def from_text(cls, text: str) -> CsvProfile:
        tank2_values: list[float] = []
        skipped_header = False

        for line_number, line in enumerate(text.splitlines(), start=1):
            cells = cls._split_cells(line)
            if not cells:
                continue
            if not all(cls._is_number(cell) for cell in cells):
                if not tank2_values and not skipped_header:
                    skipped_header = True
                    continue
                raise CsvProfileError(
                    f"line {line_number}: expected numeric level values"
                )
            if len(cells) != 1:
                raise CsvProfileError(f"line {line_number}: expected 1 column")
            tank2_values.append(float(cells[0]))

        if not tank2_values:
            raise CsvProfileError("profile contains no rows")
        return cls(tuple(tank2_values))

    def desired_at(self, elapsed_s: float) -> float:
        if elapsed_s <= 0:
            index = 0
        else:
            index = int(elapsed_s / config.PROFILE_SAMPLE_INTERVAL_S)
        index = min(index, self.row_count - 1)
        return self.tank2_levels[index]

    @staticmethod
    def _split_cells(line: str) -> list[str]:
        normalized = line.strip().replace(";", ",").replace("\t", ",")
        return [cell.strip() for cell in normalized.split(",") if cell.strip()]

    @staticmethod
    def _is_number(cell: str) -> bool:
        try:
            float(cell)
        except ValueError:
            return False
        return True
