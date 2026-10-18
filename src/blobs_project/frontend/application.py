import sys

from PyQt6.QtWidgets import QApplication

from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.regulation import RegulationService

from .assets import logo_icon
from .main_window import MainWindow


class Application:
    @staticmethod
    def create_window(
        regulation_service: RegulationService, csv_service: CsvService
    ) -> MainWindow:
        window = MainWindow(regulation_service, csv_service)
        window.setWindowIcon(logo_icon())
        return window

    @staticmethod
    def run(regulation_service: RegulationService, csv_service: CsvService) -> int:
        app = QApplication.instance()
        if not isinstance(app, QApplication):
            app = QApplication(sys.argv)
        app.setWindowIcon(logo_icon())
        window = Application.create_window(regulation_service, csv_service)
        window.show()
        return app.exec()
