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
            reason = error.strerror or str(error)
            raise CsvError(f"could not read file: {reason}") from error
        except UnicodeError as error:
            raise CsvError(f"file is not valid UTF-8 text: {error}") from error
        return CsvProfile.from_text(text)
