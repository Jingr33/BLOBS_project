from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtWidgets import QFileDialog, QWidget

from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.regulation import RegulationService
from blobs_project.translations import tr

from .action_id import ActionId
from .csv_actions import CsvActions


class ActionDispatcher:
    def __init__(
        self, regulation_service: RegulationService, csv_service: CsvService
    ) -> None:
        self._regulation_service = regulation_service
        self._csv_service = csv_service
        self._handlers: dict[ActionId, Callable[[QWidget], str | None]] = {
            ActionId.FORCE_RESET: self._force_reset,
            ActionId.IMPORT_CSV: self._import_csv,
            ActionId.EXPORT_CSV: self._export_csv,
            ActionId.DOWNLOAD_CSV_TEMPLATE: self._download_template,
        }

    def execute(self, action_id: ActionId, parent: QWidget) -> str | None:
        handler = self._handlers.get(action_id)
        if handler is None:
            return None
        return handler(parent)

    def _force_reset(self, parent: QWidget) -> str | None:
        self._regulation_service.force_reset()
        return tr("status.force_reset")

    def _import_csv(self, parent: QWidget) -> str | None:
        return CsvActions.import_csv(
            parent, self._csv_service, self._regulation_service
        )

    def _export_csv(self, parent: QWidget) -> str | None:
        return CsvActions.export_csv(
            parent, self._csv_service, self._regulation_service
        )

    def _download_template(self, parent: QWidget) -> str | None:
        path, _ = QFileDialog.getSaveFileName(
            parent,
            tr("dialog.template_title"),
            "profile_template.csv",
            tr("dialog.csv_filter"),
        )
        if not path:
            return None
        if not self._csv_service.save_template(path):
            return tr("status.export_failed")
        return tr("status.template_saved")
