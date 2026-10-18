from __future__ import annotations

from pathlib import Path

from blobs_project.backend.regulation.csv_error import CsvError

from .csv_profile import CsvProfile


class ProfileLoader:
    @staticmethod
    def load_profile(path: Path) -> CsvProfile:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as error:
            raise CsvError(str(error)) from error
        return CsvProfile.from_text(text)
