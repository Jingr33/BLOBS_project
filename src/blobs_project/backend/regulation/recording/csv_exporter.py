from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from blobs_project.backend.dtos import Sample

from .run_csv import RunCsv


class CsvExporter:
    @staticmethod
    def export_samples(samples: Sequence[Sample], path: Path) -> bool:
        if not samples:
            return False
        path.write_text(RunCsv.to_text(samples), encoding="utf-8")
        return True
