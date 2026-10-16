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
from blobs_project.backend.regulation.regulation_process_loader import (
    is_run_text,
    run_from_text,
)
from blobs_project.backend.statistics import run_statistics, statistics_to_text


class CsvService:
    PROFILE_TEMPLATE: Final = "hladina_cm\n10\n15\n12,5\n8\n"

    def load_profile(self, path: str | Path) -> CsvProfile | None:
        try:
            return ProfileLoader.load_profile(path)
        except CsvProfileError:
            return None

    def load(self, path: str | Path) -> CsvProfile | tuple[Sample, ...] | None:
        """Return a scenario profile or a recorded run, ``None`` if invalid."""
        try:
            text = Path(path).read_text(encoding="utf-8-sig")
            if is_run_text(text):
                return run_from_text(text)
            return CsvProfile.from_text(text)
        except (OSError, CsvProfileError):
            return None

    def save_template(self, path: str | Path) -> bool:
        try:
            Path(path).write_text(self.PROFILE_TEMPLATE, encoding="utf-8")
        except OSError:
            return False
        return True

    def export_samples(
        self, samples: Sequence[Sample], path: str | Path
    ) -> SampleExportStatus:
        """Write ``samples`` to ``path`` and their statistics next to it."""
        try:
            exported = CsvExporter.export_samples_csv(samples, path)
            if exported:
                text = statistics_to_text(run_statistics(samples))
                self.statistics_path(path).write_text(text, encoding="utf-8")
        except OSError:
            return SampleExportStatus.FAILED
        if not exported:
            return SampleExportStatus.NO_SAMPLES
        return SampleExportStatus.WRITTEN

    @staticmethod
    def statistics_path(path: str | Path) -> Path:
        """Return the statistics path, ``run.csv`` -> ``run_statistics.csv``."""
        path = Path(path)
        return path.with_name(f"{path.stem}_statistics{path.suffix or '.csv'}")
