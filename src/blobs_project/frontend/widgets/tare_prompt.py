from PyQt6.QtWidgets import QMessageBox, QWidget

from blobs_project.backend.hardware import HardwareError
from blobs_project.backend.regulation import RegulationService
from blobs_project.translations import tr


class TarePrompt(QMessageBox):
    """Dialog offering to zero the level sensor before a run starts."""

    def __init__(
        self, regulation_service: RegulationService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._regulation_service = regulation_service
        self.setIcon(QMessageBox.Icon.Question)
        self.setWindowTitle(tr("dialog.tare_title"))
        self.setText(tr("dialog.tare_question"))
        self.setStandardButtons(
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel
        )
        self.setDefaultButton(QMessageBox.StandardButton.No)

    def confirm(self) -> bool:
        """Ask, tare on Yes, and return whether the run should start."""
        answer = QMessageBox.StandardButton(self.exec())
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer != QMessageBox.StandardButton.Yes:
            return True
        try:
            self._regulation_service.tare()
        except HardwareError as error:
            QMessageBox.warning(
                self, tr("dialog.tare_title"), tr("status.tare_failed", reason=error)
            )
            return False
        return True
