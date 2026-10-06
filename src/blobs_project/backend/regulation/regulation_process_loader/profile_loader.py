from __future__ import annotations

from pathlib import Path

from .csv_profile import CsvProfile
from .csv_profile_error import CsvProfileError


class ProfileLoader:
    @staticmethod
    def load_profile(path: str | Path) -> CsvProfile:
        try:
            text = Path(path).read_text(encoding="utf-8-sig")
        except OSError as error:
            raise CsvProfileError(str(error)) from error
        return CsvProfile.from_text(text)
