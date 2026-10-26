from PyQt6.QtWidgets import QMessageBox, QWidget

from blobs_project.backend.hardware import HardwareError
from blobs_project.backend.regulation import RegulationService
from blobs_project.translations import tr


class TarePrompt:
    @staticmethod
    def offer(parent: QWidget, regulation_service: RegulationService) -> bool:
        """Offer to zero the level sensor before a run; return whether to start."""
        answer = QMessageBox.question(
            parent,
            tr("dialog.tare_title"),
            tr("dialog.tare_question"),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer != QMessageBox.StandardButton.Yes:
            return True
        try:
            regulation_service.tare()
        except HardwareError as error:
            QMessageBox.warning(
                parent, tr("dialog.tare_title"), tr("status.tare_failed", reason=error)
            )
            return False
        return True
