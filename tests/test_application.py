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
from blobs_project.frontend.widgets.alert_log_view import AlertLogView
from blobs_project.frontend.widgets.clock_widget import ClockWidget
from blobs_project.frontend.widgets.metric_card import MetricCard
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


def test_header_offers_tare_and_emergency_stop_with_the_clock_in_the_corner() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    window.show()
    app.processEvents()
    header = window.findChild(HeaderFrame)
    assert header is not None

    labels = [button.text() for button in header.findChildren(QPushButton)]

    assert labels == ["Tare", "EMERGENCY STOP"]

    clock = header.findChild(ClockWidget)
    emergency = header.findChild(QPushButton, "emergency")
    assert clock is not None and emergency is not None
    assert clock.x() > emergency.x()

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
    nav_buttons = [
        button
        for button in frame.findChildren(QPushButton)
        if button.objectName() in ("nav", "navActive")
    ]
    assert [button.text() for button in nav_buttons] == [
        "Overview",
        "Chart",
        "Statistics",
        "Alerts",
        "Regulation",
        "Settings",
    ]

    window.close()
    app.processEvents()


def test_header_has_no_logo_and_window_uses_the_logo_icon() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    header = window.findChild(HeaderFrame)
    assert header is not None

    assert header.findChild(QLabel, "logo") is None

    icon = window.windowIcon()
    assert not icon.isNull()
    assert not icon.pixmap(64, 64).isNull()

    window.close()
    app.processEvents()


def test_regulation_frame_offers_regulation_and_automatic() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    frame = window.findChild(RegulationFrame)
    assert frame is not None

    labels = [button.text() for button in frame.findChildren(QPushButton)]

    assert labels == ["Start regulation", "Start automatic regulation"]

    window.close()
    app.processEvents()


def test_settings_tab_offers_csv_management() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    frame = window.findChild(VisualizationFrame)
    assert frame is not None

    settings_button = frame.findChildren(QPushButton)[5]
    assert settings_button.text() == "Settings"
    settings_button.click()

    labels = [button.text() for button in frame.findChildren(QPushButton)]

    assert frame.current_page == 5
    assert labels[-3:] == [
        "Export CSV data",
        "Import CSV data",
        "Download CSV template",
    ]

    window.close()
    app.processEvents()


def test_overview_shows_unified_metrics_and_a_small_chart() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    frame = window.findChild(VisualizationFrame)
    assert frame is not None

    captions = [label.text() for label in frame.findChildren(QLabel)]
    for caption in (
        "Pump power [W]",
        "Pump voltage [V]",
        "Actual height [cm]",
        "Flow [L/min]",
    ):
        assert caption in captions
    assert len(frame.findChildren(MetricCard)) == 4
    assert len(frame.findChildren(TrendPreview)) == 2

    window.close()
    app.processEvents()


def test_regulation_frame_is_a_tab_reachable_from_navigation() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    window.show()
    app.processEvents()
    frame = window.findChild(VisualizationFrame)
    regulation = window.findChild(RegulationFrame)
    assert frame is not None and regulation is not None

    assert not regulation.isVisible()

    regulation_button = frame.findChildren(QPushButton)[4]
    assert regulation_button.text() == "Regulation"
    regulation_button.click()
    app.processEvents()

    assert frame.current_page == 4
    assert regulation.isVisible()

    frame.findChildren(QPushButton)[0].click()
    app.processEvents()

    assert not regulation.isVisible()

    window.close()
    app.processEvents()


def test_switching_tabs_does_not_change_the_run() -> None:
    app = QApplication.instance() or QApplication([])

    regulation_service = RegulationService()
    window = Application.create_window(regulation_service, CsvService())
    window.show()
    app.processEvents()
    frame = window.findChild(VisualizationFrame)
    regulation_frame = window.findChild(RegulationFrame)
    assert frame is not None and regulation_frame is not None

    regulation = regulation_frame.findChildren(QPushButton)[0]
    regulation.click()
    assert regulation_service.regulation_active

    frame.findChildren(QPushButton)[0].click()
    app.processEvents()
    assert regulation_service.regulation_active

    frame.findChildren(QPushButton)[4].click()
    app.processEvents()
    assert regulation_service.regulation_active
    assert regulation.text() == "Stop regulation"

    window.close()
    app.processEvents()


def test_regulation_toggle_switches_between_start_and_stop() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    frame = window.findChild(RegulationFrame)
    assert frame is not None

    buttons = frame.findChildren(QPushButton)
    regulation = buttons[0]
    automatic = buttons[1]
    assert regulation.text() == "Start regulation"
    assert regulation.objectName() == "primary"
    assert automatic.text() == "Start automatic regulation"
    assert automatic.objectName() == "primary"

    regulation.click()
    assert regulation.text() == "Stop regulation"
    assert regulation.objectName() == "running"

    regulation.click()
    assert regulation.text() == "Start regulation"
    assert regulation.objectName() == "primary"

    automatic.click()
    assert automatic.text() == "Start automatic regulation"
    assert automatic.objectName() == "primary"

    window.close()
    app.processEvents()


def test_emergency_stop_is_logged_to_the_alerts_tab() -> None:
    app = QApplication.instance() or QApplication([])

    window = Application.create_window(RegulationService(), CsvService())
    header = window.findChild(HeaderFrame)
    alerts = window.findChild(AlertLogView)
    assert header is not None and alerts is not None

    emergency = header.findChild(QPushButton, "emergency")
    assert emergency is not None
    emergency.click()
    app.processEvents()

    assert alerts.table.rowCount() == 1
    message = alerts.table.item(0, 1)
    assert message is not None
    assert message.text() == "Regulation stopped: emergency stop"

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
