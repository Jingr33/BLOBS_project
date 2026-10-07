import sys

from PyQt6.QtWidgets import QApplication

from blobs_project.backend.regulation import RegulationService

from .main_window import MainWindow


class Application:
    @staticmethod
    def create_window(service: RegulationService) -> MainWindow:
        return MainWindow(service)

    @staticmethod
    def run(service: RegulationService) -> int:
        app = QApplication.instance() or QApplication(sys.argv)
        window = Application.create_window(service)
        window.show()
        return app.exec()
