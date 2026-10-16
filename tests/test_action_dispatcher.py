import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QWidget

from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.regulation import RegulationService
from blobs_project.frontend.actions import ActionDispatcher, ActionId

_APP = QApplication.instance() or QApplication([])


def test_force_reset_action_stops_the_running_regulation() -> None:
    regulation_service = RegulationService()
    regulation_service.toggle_regulation()
    dispatcher = ActionDispatcher(regulation_service, CsvService())

    message = dispatcher.execute(ActionId.FORCE_RESET, QWidget())

    assert message == "Regulation reset"
    assert not regulation_service.regulation_active
