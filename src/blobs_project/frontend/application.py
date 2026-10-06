import sys

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


class Application:
    @staticmethod
    def create_window() -> MainWindow:
        """Create the static monitoring window without starting Qt's event loop."""
        return MainWindow()

    @staticmethod
    def run() -> int:
        app = QApplication.instance() or QApplication(sys.argv)
        window = Application.create_window()
        window.show()
        return app.exec()
