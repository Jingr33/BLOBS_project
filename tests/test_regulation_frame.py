import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel, QPushButton

from blobs_project.backend.regulation import ProfileLoader, RegulationService
from blobs_project.frontend.frames.regulation_frame import RegulationFrame

# The application must outlive every standalone frame created in these tests.
_APP = QApplication.instance() or QApplication([])


def _frame(regulation_service: RegulationService) -> RegulationFrame:
    frame = RegulationFrame(regulation_service)
    frame.show()
    _APP.processEvents()
    return frame


def _regulation_button(frame: RegulationFrame) -> QPushButton:
    button = frame.findChild(QPushButton)
    assert button is not None
    return button


def _mode_label(frame: RegulationFrame) -> QLabel:
    label = frame.findChild(QLabel, "mode")
    assert label is not None
    return label


def test_start_button_toggles_the_manual_regulation() -> None:
    regulation_service = RegulationService()
    frame = _frame(regulation_service)
    button = _regulation_button(frame)

    assert button.text() == "Start regulation"
    assert button.objectName() == "primary"

    button.click()
    assert regulation_service.regulation_active
    assert button.text() == "Stop regulation"
    assert button.objectName() == "running"

    button.click()
    assert not regulation_service.regulation_active
    assert button.text() == "Start regulation"
    assert button.objectName() == "primary"


def test_mode_label_reports_the_desired_level_source(tmp_path: Path) -> None:
    regulation_service = RegulationService()
    frame = _frame(regulation_service)

    assert _mode_label(frame).text() == "Desired levels: manual"

    path = tmp_path / "profile.csv"
    path.write_text("20.0\n", encoding="utf-8")
    regulation_service.set_profile(ProfileLoader.load_profile(path))
    regulation_service.toggle_self_driven()
    frame.sync()

    assert _mode_label(frame).text() == "Desired levels: profile"
    assert not _regulation_button(frame).isEnabled()


def test_fault_shows_as_an_alert_on_the_overview_strip() -> None:
    regulation_service = RegulationService()
    frame = _frame(regulation_service)
    alert = frame.findChild(QLabel, "alert")
    assert alert is not None and alert.isHidden()

    regulation_service.emergency_stop()
    frame.sync()

    assert not alert.isHidden()
    assert alert.text() == "Stopped: emergency stop"
