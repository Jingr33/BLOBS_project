import os
import time
from collections.abc import Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton

from blobs_project import Application
from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.regulation import RegulationService
from blobs_project.frontend.frames import (
    FooterFrame,
    HeaderFrame,
    RegulationFrame,
    VisualizationFrame,
)
from blobs_project.frontend.widgets.trend_preview import TrendPreview


def _wait_until(condition: Callable[[], bool], timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    app = QApplication.instance()
    while time.monotonic() < deadline:
        if condition():
            return True
        if app is not None:
            app.processEvents()
        time.sleep(0.02)
    return bool(condition())


def test_application_creates_monitoring_window() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())

    assert window.windowTitle() == "BLOBS // Process Control"
    assert window.minimumSize().width() == 1040
    window.close()
    app.processEvents()


def test_main_window_composes_separate_frames() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())

    assert window.findChild(HeaderFrame) is not None
    assert window.findChild(RegulationFrame) is not None
    assert window.findChild(VisualizationFrame) is not None
    assert window.findChild(FooterFrame) is not None
    window.close()
    app.processEvents()


def test_header_offers_export_csv_before_force_reset() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    header = window.findChild(HeaderFrame)
    assert header is not None

    labels = [button.text() for button in header.findChildren(QPushButton)]

    assert labels == [
        "Export CSV data",
        "Force reset",
        "Download CSV template",
        "Tare",
    ]

    window.close()
    app.processEvents()


def test_visualization_frame_switches_between_pages() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    frame = window.findChild(VisualizationFrame)
    assert frame is not None

    assert frame.current_page == 0

    chart_button = frame.findChildren(QPushButton)[1]
    chart_button.click()

    assert frame.current_page == 1
    assert chart_button.objectName() == "navActive"
    assert frame.findChildren(QPushButton)[0].objectName() == "nav"
    assert len(frame.findChildren(QPushButton)) == 3

    window.close()
    app.processEvents()


def test_header_displays_the_blobs_logo() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    header = window.findChild(HeaderFrame)
    assert header is not None

    logo = header.findChild(QLabel, "logo")
    assert logo is not None
    assert logo.pixmap() is not None
    assert not logo.pixmap().isNull()

    window.close()
    app.processEvents()


def test_regulation_frame_offers_regulation_import_and_automatic() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    frame = window.findChild(RegulationFrame)
    assert frame is not None

    labels = [button.text() for button in frame.findChildren(QPushButton)]

    assert labels == [
        "Start regulation",
        "EMERGENCY STOP",
        "Import CSV data",
        "Start automatic regulation",
    ]

    window.close()
    app.processEvents()


def test_import_and_automatic_buttons_share_one_row() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    window.show()
    app.processEvents()
    frame = window.findChild(RegulationFrame)
    assert frame is not None

    buttons = {button.text(): button for button in frame.findChildren(QPushButton)}
    import_button = buttons["Import CSV data"]
    automatic_button = buttons["Start automatic regulation"]

    assert import_button.y() == automatic_button.y()
    assert automatic_button.x() > import_button.x()

    window.close()
    app.processEvents()


def test_regulation_toggle_switches_between_start_and_stop() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    frame = window.findChild(RegulationFrame)
    assert frame is not None

    buttons = frame.findChildren(QPushButton)
    regulation = buttons[0]
    automatic = buttons[3]
    assert regulation.text() == "Start regulation"
    assert regulation.objectName() == "primary"
    assert automatic.text() == "Start automatic regulation"
    assert automatic.objectName() == "primary"

    regulation.click()
    assert regulation.text() == "Stop regulation"
    assert regulation.objectName() == "danger"

    regulation.click()
    assert regulation.text() == "Start regulation"
    assert regulation.objectName() == "primary"

    automatic.click()
    assert automatic.text() == "Start automatic regulation"
    assert automatic.objectName() == "primary"

    window.close()
    app.processEvents()


def _window_parts() -> tuple[
    QCoreApplication,
    QMainWindow,
    HeaderFrame,
    RegulationFrame,
    FooterFrame,
    TrendPreview,
]:
    app = QApplication.instance() or QApplication([])
    window = Application.create_window(RegulationService(), CsvService())
    window.show()
    app.processEvents()
    header = window.findChild(HeaderFrame)
    frame = window.findChild(RegulationFrame)
    footer = window.findChild(FooterFrame)
    preview = window.findChild(TrendPreview)
    assert header is not None and frame is not None
    assert footer is not None and preview is not None
    return app, window, header, frame, footer, preview


def test_force_reset_stops_regulation_and_clears_the_chart() -> None:
    app, window, header, frame, footer, preview = _window_parts()
    reset_button = next(
        button
        for button in header.findChildren(QPushButton)
        if button.text() == "Force reset"
    )
    regulation = frame.findChildren(QPushButton)[0]
    regulation.click()
    assert regulation.text() == "Stop regulation"

    reset_button.click()
    app.processEvents()

    assert regulation.text() == "Start regulation"
    assert footer.time_label.text() == "no regulation is running"
    assert "Regulation reset" in footer.status_label.text()

    window.close()
    app.processEvents()


def test_footer_shows_the_regulation_time_while_running() -> None:
    app, window, _, frame, footer, _ = _window_parts()
    regulation = frame.findChildren(QPushButton)[0]
    assert footer.time_label.text() == "no regulation is running"

    regulation.click()
    assert _wait_until(lambda: footer.time_label.text().startswith("Regulation:"))
    assert footer.time_label.text() != "no regulation is running"

    regulation.click()
    assert _wait_until(lambda: footer.time_label.text() == "no regulation is running")

    window.close()
    app.processEvents()
