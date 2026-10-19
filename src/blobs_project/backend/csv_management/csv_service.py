from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Final

from blobs_project import config
from blobs_project.backend.dtos import Sample
from blobs_project.backend.regulation import (
    CsvError,
    CsvExporter,
    CsvProfile,
    ProfileLoader,
    RunCsv,
    SampleExportStatus,
)
from blobs_project.backend.statistics import StatisticsCalculator, StatisticsCsv


class CsvService:
    PROFILE_TEMPLATE: Final = (
        "# BLOBS desired-level profile CSV\n"
        "# One desired lower-tank level in cm per row; use a single column.\n"
        f"# Values must be numeric and between {config.SETPOINT_MIN_CM:g} and "
        f"{config.SETPOINT_MAX_CM:g} cm, inclusive.\n"
        "# Blank lines and lines beginning with # are ignored.\n"
        "# A column header is optional. The application sets the step duration.\n"
        "hladina_cm\n"
        "10\n"
        "15\n"
        "12.5\n"
        "8\n"
    )

    def load_profile(self, path: Path) -> CsvProfile | None:
        try:
            return ProfileLoader.load_profile(path)
        except CsvError:
            return None

    def load(self, path: Path) -> CsvProfile | tuple[Sample, ...] | None:
        """Return a profile or a recorded run, ``None`` if invalid."""
        try:
            return self.load_or_raise(path)
        except CsvError:
            return None

    def load_or_raise(self, path: Path) -> CsvProfile | tuple[Sample, ...]:
        """Load a profile or recorded run, raising ``CsvError`` with details."""
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as error:
            reason = error.strerror or str(error)
            raise CsvError(f"could not read file: {reason}") from error
        except UnicodeError as error:
            raise CsvError(f"file is not valid UTF-8 text: {error}") from error
        if RunCsv.is_run(text):
            return RunCsv.from_text(text)
        return CsvProfile.from_text(text)

    def save_template(self, path: Path) -> bool:
        try:
            path.write_text(self.PROFILE_TEMPLATE, encoding="utf-8")
        except OSError:
            return False
        return True

    def export_samples(
        self, samples: Sequence[Sample], path: Path
    ) -> SampleExportStatus:
        """Write ``samples`` to ``path`` and their statistics next to it."""
        try:
            exported = CsvExporter.export_samples(samples, path)
            if exported:
                statistics = StatisticsCalculator.calculate(samples)
                text = StatisticsCsv.to_text(statistics)
                self.statistics_path(path).write_text(text, encoding="utf-8")
        except OSError:
            return SampleExportStatus.FAILED
        if not exported:
            return SampleExportStatus.NO_SAMPLES
        return SampleExportStatus.WRITTEN

    @staticmethod
    def statistics_path(path: Path) -> Path:
        """Return the statistics path, ``run.csv`` -> ``run_statistics.csv``."""
        return path.with_name(f"{path.stem}_statistics{path.suffix or '.csv'}")
