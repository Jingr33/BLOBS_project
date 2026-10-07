from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from blobs_project.backend.regulation.sample_log import Sample


class CsvExporter:
    @staticmethod
    def export_samples_csv(samples: Sequence[Sample], path: str | Path) -> bool:
        if not samples:
            return False
        lines = ["time_s,tank2_actual_cm"]
        lines.extend(
            f"{sample.time_s:.1f},{sample.tank2_actual_cm:.2f}" for sample in samples
        )
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True
