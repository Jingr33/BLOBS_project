import sys

from PyQt6.QtWidgets import QApplication

from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.regulation import RegulationService

from .main_window import MainWindow


class Application:
    @staticmethod
    def create_window(
        regulation_service: RegulationService, csv_service: CsvService
    ) -> MainWindow:
        return MainWindow(regulation_service, csv_service)

    @staticmethod
    def run(regulation_service: RegulationService, csv_service: CsvService) -> int:
        app = QApplication.instance() or QApplication(sys.argv)
        window = Application.create_window(regulation_service, csv_service)
        window.show()
        return app.exec()
