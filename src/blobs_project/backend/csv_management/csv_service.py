from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Final

from blobs_project.backend.regulation import (
    CsvExporter,
    CsvProfile,
    CsvProfileError,
    ProfileLoader,
    Sample,
    SampleExportStatus,
)


class CsvService:
    PROFILE_TEMPLATE_HEADER: Final = "test content" # temporary string

    def load_profile(self, path: str | Path) -> CsvProfile | None:
        try:
            return ProfileLoader.load_profile(path)
        except CsvProfileError:
            return None

    def save_template(self, path: str | Path) -> bool:
        try:
            Path(path).write_text(f"{self.PROFILE_TEMPLATE_HEADER}\n", encoding="utf-8")
        except OSError:
            return False
        return True

    def export_samples(
        self, samples: Sequence[Sample], path: str | Path
    ) -> SampleExportStatus:
        try:
            exported = CsvExporter.export_samples_csv(samples, path)
        except OSError:
            return SampleExportStatus.FAILED
        if not exported:
            return SampleExportStatus.NO_SAMPLES
        return SampleExportStatus.WRITTEN
