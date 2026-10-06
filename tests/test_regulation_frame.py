import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel, QPushButton

from blobs_project.backend.regulation import ProfileLoader, RegulationService
from blobs_project.frontend.frames.regulation_frame import RegulationFrame

# The application must outlive every standalone frame created in these tests.
_APP = QApplication.instance() or QApplication([])


def _frame(service: RegulationService) -> RegulationFrame:
    frame = RegulationFrame(service)
    frame.show()
    _APP.processEvents()
    return frame


def _buttons(frame: RegulationFrame) -> tuple[QPushButton, QPushButton]:
    buttons = frame.findChildren(QPushButton)
    return buttons[0], buttons[3]


def _profile_label(frame: RegulationFrame) -> QLabel:
    label = frame.findChild(QLabel, "profile")
    assert label is not None
    return label


def test_self_driven_button_waits_for_a_loaded_profile(tmp_path: Path) -> None:
    service = RegulationService()
    frame = _frame(service)
    regulation, self_driven = _buttons(frame)

    assert not self_driven.isEnabled()
    assert _profile_label(frame).text() == "No CSV profile loaded"
    assert regulation.isEnabled()

    path = tmp_path / "profile.csv"
    path.write_text("20.0\n21.0\n", encoding="utf-8")
    service.set_profile(ProfileLoader.load_profile(path))
    frame.sync()

    assert self_driven.isEnabled()
    assert _profile_label(frame).text() == "Profile: CSV / 2 rows / 2 s"


def test_self_driven_is_disabled_without_a_profile() -> None:
    service = RegulationService()
    frame = _frame(service)
    _, self_driven = _buttons(frame)

    assert not self_driven.isEnabled()

    self_driven.click()
    assert not service.self_driven_active


def test_starting_regulation_disables_self_driven_button(tmp_path: Path) -> None:
    service = RegulationService()
    frame = _frame(service)
    regulation, self_driven = _buttons(frame)
    path = tmp_path / "profile.csv"
    path.write_text("20.0\n", encoding="utf-8")
    service.set_profile(ProfileLoader.load_profile(path))
    frame.sync()

    regulation.click()

    assert service.regulation_active
    assert regulation.text() == "Stop regulation"
    assert not self_driven.isEnabled()

    regulation.click()

    assert not service.regulation_active
    assert regulation.text() == "Start regulation"
    assert self_driven.isEnabled()


def test_starting_self_driven_disables_regulation_button(tmp_path: Path) -> None:
    service = RegulationService()
    frame = _frame(service)
    regulation, self_driven = _buttons(frame)
    path = tmp_path / "profile.csv"
    path.write_text("20.0\n", encoding="utf-8")
    service.set_profile(ProfileLoader.load_profile(path))
    frame.sync()

    self_driven.click()

    assert service.self_driven_active
    assert self_driven.text() == "Stop self-driven regulation"
    assert not regulation.isEnabled()

    self_driven.click()

    assert not service.self_driven_active
    assert self_driven.text() == "Start self-driven regulation"
    assert regulation.isEnabled()
