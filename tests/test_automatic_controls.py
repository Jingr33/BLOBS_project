import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QDoubleSpinBox, QLabel, QPushButton

from blobs_project.backend.regulation import ProfileLoader, RegulationService
from blobs_project.frontend.frames.regulation_frame import RegulationFrame
from blobs_project.frontend.widgets.automatic_controls import AutomaticControls

# The application must outlive every standalone widget created in these tests.
_APP = QApplication.instance() or QApplication([])


def _controls(regulation_service: RegulationService) -> AutomaticControls:
    controls = AutomaticControls(regulation_service)
    controls.show()
    _APP.processEvents()
    return controls


def _button(controls: AutomaticControls) -> QPushButton:
    button = controls.findChild(QPushButton)
    assert button is not None
    return button


def _profile_label(controls: AutomaticControls) -> QLabel:
    label = controls.findChild(QLabel, "profile")
    assert label is not None
    return label


def _regulation_button(strip: RegulationFrame) -> QPushButton:
    button = strip.findChild(QPushButton)
    assert button is not None
    return button


def _load_profile(regulation_service: RegulationService, path: Path) -> None:
    path.write_text("20.0\n21.0\n", encoding="utf-8")
    regulation_service.set_profile(ProfileLoader.load_profile(path))


def test_automatic_button_waits_for_a_loaded_profile(tmp_path: Path) -> None:
    regulation_service = RegulationService()
    controls = _controls(regulation_service)
    button = _button(controls)

    assert not button.isEnabled()
    assert _profile_label(controls).text() == "No CSV profile loaded"

    _load_profile(regulation_service, tmp_path / "profile.csv")
    controls.sync()

    assert button.isEnabled()
    assert _profile_label(controls).text() == "Profile: 2 × 5 min = 10 min"


def test_automatic_is_disabled_without_a_profile() -> None:
    regulation_service = RegulationService()
    controls = _controls(regulation_service)

    assert not _button(controls).isEnabled()

    _button(controls).click()
    assert not regulation_service.self_driven_active


def test_starting_regulation_disables_the_automatic_button(tmp_path: Path) -> None:
    regulation_service = RegulationService()
    controls = _controls(regulation_service)
    strip = RegulationFrame(regulation_service)
    _load_profile(regulation_service, tmp_path / "profile.csv")
    controls.sync()

    _regulation_button(strip).click()
    controls.sync()

    assert regulation_service.regulation_active
    assert not _button(controls).isEnabled()

    _regulation_button(strip).click()
    controls.sync()

    assert not regulation_service.regulation_active
    assert _button(controls).isEnabled()


def test_starting_automatic_disables_the_overview_button(tmp_path: Path) -> None:
    regulation_service = RegulationService()
    controls = _controls(regulation_service)
    strip = RegulationFrame(regulation_service)
    _load_profile(regulation_service, tmp_path / "profile.csv")
    controls.sync()

    _button(controls).click()
    strip.sync()

    assert regulation_service.self_driven_active
    assert _button(controls).text() == "Stop automatic regulation"
    assert not _regulation_button(strip).isEnabled()

    _button(controls).click()
    strip.sync()

    assert not regulation_service.self_driven_active
    assert _button(controls).text() == "Start automatic regulation"
    assert _regulation_button(strip).isEnabled()


def test_step_duration_is_applied_to_the_service() -> None:
    regulation_service = RegulationService()
    controls = _controls(regulation_service)
    step_spin = controls.findChild(QDoubleSpinBox)
    assert step_spin is not None

    step_spin.setValue(12.5)

    assert regulation_service.step_s == 750.0
