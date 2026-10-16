from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from blobs_project.backend.regulation.sample_log import Sample

from .csv_run import run_to_text


class CsvExporter:
    @staticmethod
    def export_samples_csv(samples: Sequence[Sample], path: str | Path) -> bool:
        if not samples:
            return False
        Path(path).write_text(run_to_text(samples), encoding="utf-8")
        return True
