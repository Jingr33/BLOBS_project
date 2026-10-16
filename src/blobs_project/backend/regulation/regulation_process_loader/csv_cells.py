"""Cell splitting and number parsing shared by the CSV readers."""

from __future__ import annotations

import re

_DECIMAL_COMMA = re.compile(r"-?\d+,\d+")


def split_cells(line: str) -> list[str]:
    """Split ``line`` on ``;``, a tab or ``,``; a single ``d,d`` is one number.

    Czech Excel saves ``;``-separated files with a decimal comma, so a lone
    ``12,5`` is read as 12.5, not as two cells.
    """
    line = line.strip()
    for separator in (";", "\t"):
        if separator in line:
            return [cell.strip() for cell in line.split(separator) if cell.strip()]
    if _DECIMAL_COMMA.fullmatch(line):
        return [line]
    return [cell.strip() for cell in line.split(",") if cell.strip()]


def parse_number(cell: str) -> float:
    """Return ``cell`` as a float, accepting a decimal comma.

    Raises ``ValueError`` if it is not a number.
    """
    return float(cell.replace(",", "."))


def is_number(cell: str) -> bool:
    """Return whether ``cell`` is a number."""
    try:
        parse_number(cell)
    except ValueError:
        return False
    return True
