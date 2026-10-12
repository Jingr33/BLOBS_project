from __future__ import annotations

from PyQt6.QtWidgets import QFileDialog, QWidget

from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.regulation import RegulationService, SampleExportStatus
from blobs_project.translations import tr


class CsvActions:
    @staticmethod
    def import_csv(
        parent: QWidget,
        csv_service: CsvService,
        regulation_service: RegulationService,
    ) -> str | None:
        path, _ = QFileDialog.getOpenFileName(
            parent, tr("dialog.import_title"), "", tr("dialog.csv_filter")
        )
        if not path:
            return None
        profile = csv_service.load_profile(path)
        if profile is None:
            return tr("status.profile_invalid")
        regulation_service.set_profile(profile)
        return tr(
            "status.profile_loaded",
            rows=profile.row_count,
            duration=profile.duration_s,
        )

    @staticmethod
    def export_csv(
        parent: QWidget,
        csv_service: CsvService,
        regulation_service: RegulationService,
    ) -> str | None:
        path, _ = QFileDialog.getSaveFileName(
            parent, tr("dialog.export_title"), "samples.csv", tr("dialog.csv_filter")
        )
        if not path:
            return None
        status = csv_service.export_samples(regulation_service.sample_log.samples, path)
        if status is SampleExportStatus.FAILED:
            return tr("status.export_failed")
        if status is SampleExportStatus.NO_SAMPLES:
            return tr("status.export_missing")
        return tr("status.export_ready")
