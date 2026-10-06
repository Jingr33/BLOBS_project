import os
import time
from collections.abc import Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton

from blobs_project import Application
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

    window = Application.create_window()

    assert window.windowTitle() == "BLOBS // Process Control"
    assert window.minimumSize().width() == 1040
    window.close()
    app.processEvents()


def test_main_window_composes_separate_frames() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window()

    assert window.findChild(HeaderFrame) is not None
    assert window.findChild(RegulationFrame) is not None
    assert window.findChild(VisualizationFrame) is not None
    assert window.findChild(FooterFrame) is not None
    window.close()
    app.processEvents()


def test_header_shows_only_the_force_reset_action() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window()
    header = window.findChild(HeaderFrame)
    assert header is not None

    labels = [button.text() for button in header.findChildren(QPushButton)]

    assert labels == ["Force reset"]

    window.close()
    app.processEvents()


def test_visualization_frame_switches_between_pages() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window()
    frame = window.findChild(VisualizationFrame)
    assert frame is not None

    assert frame.current_page == 0

    chart_button = frame.findChildren(QPushButton)[1]
    chart_button.click()

    assert frame.current_page == 1
    assert chart_button.objectName() == "navActive"
    assert frame.findChildren(QPushButton)[0].objectName() == "nav"

    window.close()
    app.processEvents()


def test_header_displays_the_blobs_logo() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window()
    header = window.findChild(HeaderFrame)
    assert header is not None

    logo = header.findChild(QLabel, "logo")
    assert logo is not None
    assert logo.pixmap() is not None
    assert not logo.pixmap().isNull()

    window.close()
    app.processEvents()


def test_regulation_frame_offers_regulation_and_csv_actions() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window()
    frame = window.findChild(RegulationFrame)
    assert frame is not None

    labels = [button.text() for button in frame.findChildren(QPushButton)]

    assert labels == [
        "Start regulation",
        "Import CSV data",
        "Export CSV data",
        "Start self-driven regulation",
    ]

    window.close()
    app.processEvents()


def test_import_and_export_buttons_share_one_row() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window()
    window.show()
    app.processEvents()
    frame = window.findChild(RegulationFrame)
    assert frame is not None

    buttons = {button.text(): button for button in frame.findChildren(QPushButton)}
    import_button = buttons["Import CSV data"]
    export_button = buttons["Export CSV data"]

    assert import_button.y() == export_button.y()
    assert export_button.x() > import_button.x()

    window.close()
    app.processEvents()


def test_regulation_toggle_switches_between_start_and_stop() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window()
    frame = window.findChild(RegulationFrame)
    assert frame is not None

    buttons = frame.findChildren(QPushButton)
    regulation = buttons[0]
    self_driven = buttons[3]
    assert regulation.text() == "Start regulation"
    assert regulation.objectName() == "primary"
    assert self_driven.text() == "Start self-driven regulation"
    assert self_driven.objectName() == "primary"

    regulation.click()
    assert regulation.text() == "Stop regulation"
    assert regulation.objectName() == "danger"

    regulation.click()
    assert regulation.text() == "Start regulation"
    assert regulation.objectName() == "primary"

    self_driven.click()
    assert self_driven.text() == "Start self-driven regulation"
    assert self_driven.objectName() == "primary"

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
    window = Application.create_window()
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
