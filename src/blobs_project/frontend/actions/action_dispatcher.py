from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QWidget

from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.hardware import HardwareError
from blobs_project.backend.regulation import (
    CsvError,
    CsvProfile,
    RegulationService,
    SampleExportStatus,
)
from blobs_project.translations import tr

from .action_id import ActionId


class ActionDispatcher:
    def __init__(
        self, regulation_service: RegulationService, csv_service: CsvService
    ) -> None:
        self._regulation_service = regulation_service
        self._csv_service = csv_service
        self._handlers: dict[ActionId, Callable[[QWidget], str | None]] = {
            ActionId.IMPORT_CSV: self._import_csv,
            ActionId.EXPORT_CSV: self._export_csv,
            ActionId.DOWNLOAD_CSV_TEMPLATE: self._download_template,
            ActionId.TARE: self._tare,
        }

    def execute(self, action_id: ActionId, parent: QWidget) -> str | None:
        handler = self._handlers.get(action_id)
        if handler is None:
            return None
        return handler(parent)

    def _tare(self, parent: QWidget) -> str | None:
        try:
            zero_v = self._regulation_service.tare()
        except RuntimeError:
            return tr("status.tare_running")
        except HardwareError as error:
            return tr("status.tare_failed", reason=error)
        return tr("status.tare_done", zero=zero_v)

    def _import_csv(self, parent: QWidget) -> str | None:
        path, _ = QFileDialog.getOpenFileName(
            parent, tr("dialog.import_title"), "", tr("dialog.csv_filter")
        )
        if not path:
            return None
        try:
            loaded = self._csv_service.load_or_raise(Path(path))
        except CsvError as error:
            return tr("status.profile_invalid", reason=error)
        if isinstance(loaded, CsvProfile):
            self._regulation_service.set_profile(loaded)
            return tr("status.profile_loaded", rows=loaded.row_count)
        try:
            self._regulation_service.load_history(loaded)
        except RuntimeError:
            return tr("status.history_running")
        minutes = (loaded[-1].time_s - loaded[0].time_s) / 60.0
        return tr("status.history_loaded", minutes=minutes)

    def _export_csv(self, parent: QWidget) -> str | None:
        path, _ = QFileDialog.getSaveFileName(
            parent, tr("dialog.export_title"), "samples.csv", tr("dialog.csv_filter")
        )
        if not path:
            return None
        status = self._csv_service.export_samples(
            self._regulation_service.sample_log.samples, Path(path)
        )
        if status is SampleExportStatus.FAILED:
            return tr("status.export_failed")
        if status is SampleExportStatus.NO_SAMPLES:
            return tr("status.export_missing")
        return tr("status.export_ready")

    def _download_template(self, parent: QWidget) -> str | None:
        path, _ = QFileDialog.getSaveFileName(
            parent,
            tr("dialog.template_title"),
            "profile_template.csv",
            tr("dialog.csv_filter"),
        )
        if not path:
            return None
        if not self._csv_service.save_template(Path(path)):
            return tr("status.export_failed")
        return tr("status.template_saved")
