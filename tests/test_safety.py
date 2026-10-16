import math
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication, QDoubleSpinBox, QLabel, QPushButton, QWidget

from blobs_project import config
from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.hardware import HardwareError, MockDAQ, Tower
from blobs_project.backend.regulation import (
    CsvProfileError,
    ProfileLoader,
    RegulationControllerBase,
    RegulationService,
)
from blobs_project.frontend.actions import ActionDispatcher, ActionId
from blobs_project.frontend.frames.footer_frame import FooterFrame
from blobs_project.frontend.frames.regulation_frame import RegulationFrame

_APP = QApplication.instance() or QApplication([])


class _RecordingController(RegulationControllerBase):
    def __init__(self) -> None:
        self.desired: list[float] = []

    def reset(self) -> None:
        pass

    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        self.desired.append(desired_cm)
        return 5.0


class _FailingDAQ(MockDAQ):
    def read_voltage(self, channel: str) -> float:
        raise HardwareError("card unplugged")


def make_service(level_cm: float) -> tuple[RegulationService, MockDAQ]:
    """Return a service on a mocked tower whose sensor reads ``level_cm``."""
    daq = MockDAQ()
    set_level(daq, level_cm)
    return RegulationService(_RecordingController(), Tower(daq)), daq


def set_level(daq: MockDAQ, level_cm: float) -> None:
    """Make the mocked sensor read ``level_cm``."""
    above_zero_cm = level_cm - config.TOWER_LEVEL_OFFSET_CM
    level_v = config.TOWER_LEVEL_ZERO_V + above_zero_cm / config.TOWER_LEVEL_CM_PER_V
    daq.set_input_voltage(config.TOWER_LEVEL_CHANNEL, level_v)


def run(service: RegulationService, seconds: float) -> None:
    """Tick ``service`` like the UI timer."""
    for _ in range(round(seconds / 0.1)):
        service.tick(0.1)


def pump_v(daq: MockDAQ) -> float:
    return daq.get_output_voltage(config.TOWER_PUMP_CHANNEL)


def test_emergency_stop_stops_the_run_and_the_pump() -> None:
    """The emergency stop sets the pump to 0 V and records the reason."""
    service, daq = make_service(10.0)
    service.toggle_regulation()
    run(service, 1.0)
    assert pump_v(daq) == 5.0

    service.emergency_stop()

    assert not service.is_running
    assert pump_v(daq) == 0.0
    assert service.fault == "emergency stop"


def test_starting_again_clears_the_fault() -> None:
    service, _ = make_service(10.0)
    service.emergency_stop()

    service.toggle_regulation()

    assert service.fault is None


def test_high_level_stops_the_run() -> None:
    """A level at the trip limit stops the pump."""
    service, daq = make_service(config.LEVEL_TRIP_CM + 1.0)
    service.toggle_regulation()

    run(service, 1.0)

    assert not service.is_running
    assert pump_v(daq) == 0.0
    assert service.fault is not None and "reached" in service.fault


def test_overflow_warning_follows_the_level() -> None:
    service, daq = make_service(config.LEVEL_WARNING_CM + 0.5)
    run(service, 3.0)
    assert service.overflow_warning

    set_level(daq, 10.0)
    run(service, 3.0)

    assert not service.overflow_warning


@pytest.mark.parametrize(
    ("desired_cm", "expected_cm"),
    [(1.0, config.SETPOINT_MIN_CM), (30.0, config.SETPOINT_MAX_CM), (12.0, 12.0)],
)
def test_controller_gets_the_setpoint_within_limits(
    desired_cm: float, expected_cm: float
) -> None:
    controller = _RecordingController()
    daq = MockDAQ()
    set_level(daq, 10.0)
    service = RegulationService(controller, Tower(daq))
    service.regulation_values.tank2_desired_cm = desired_cm
    service.toggle_regulation()

    run(service, 1.0)

    assert controller.desired == [expected_cm, expected_cm]


def test_level_is_measured_while_idle() -> None:
    """The level is read without a run, the pump stays off."""
    service, daq = make_service(12.0)

    run(service, 1.0)

    assert service.regulation_values.tank2_actual_cm == pytest.approx(12.0)
    assert pump_v(daq) == 0.0


def test_lost_card_while_idle_is_reported() -> None:
    service = RegulationService(_RecordingController(), Tower(_FailingDAQ()))

    run(service, 1.0)

    assert service.fault is not None and "card unplugged" in service.fault


def test_tare_sets_the_sensor_zero() -> None:
    service, daq = make_service(0.0)
    daq.set_input_voltage(config.TOWER_LEVEL_CHANNEL, 0.3)

    assert service.tare() == pytest.approx(0.3)
    assert service.tower.read_level_cm() == pytest.approx(config.TOWER_LEVEL_OFFSET_CM)


def test_tare_is_refused_while_running() -> None:
    service, _ = make_service(10.0)
    service.toggle_regulation()

    with pytest.raises(RuntimeError):
        service.tare()


def test_profile_rejects_levels_outside_the_setpoint_range(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("hladina_cm\n10\n25\n", encoding="utf-8")

    with pytest.raises(CsvProfileError, match="line 3"):
        ProfileLoader.load_profile(path)


def test_profile_rejects_nan_level(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text(f"10\n{math.nan}\n", encoding="utf-8")

    with pytest.raises(CsvProfileError):
        ProfileLoader.load_profile(path)


def test_desired_spin_box_allows_only_the_setpoint_range() -> None:
    frame = RegulationFrame(RegulationService())
    spin = frame.findChild(QDoubleSpinBox)
    assert spin is not None

    assert spin.minimum() == config.SETPOINT_MIN_CM
    assert spin.maximum() == config.SETPOINT_MAX_CM


def test_emergency_button_stops_and_shows_the_reason() -> None:
    service, daq = make_service(10.0)
    frame = RegulationFrame(service)
    frame.show()
    buttons = {button.text(): button for button in frame.findChildren(QPushButton)}
    alert = frame.findChild(QLabel, "alert")
    assert alert is not None and alert.isHidden()
    buttons["Start regulation"].click()
    run(service, 1.0)

    buttons["EMERGENCY STOP"].click()

    assert not service.is_running
    assert pump_v(daq) == 0.0
    assert not alert.isHidden()
    assert alert.text() == "Stopped: emergency stop"


def test_tare_action_reports_the_result() -> None:
    service, daq = make_service(0.0)
    dispatcher = ActionDispatcher(service, CsvService())

    assert dispatcher.execute(ActionId.TARE, QWidget()) is not None
    service.toggle_regulation()
    message = dispatcher.execute(ActionId.TARE, QWidget())

    assert message == "Stop the regulation before zeroing the sensor"


def test_footer_shows_alerts_in_red() -> None:
    footer = FooterFrame()

    footer.set_status("Regulation stopped: emergency stop", alert=True)

    assert config.RED in footer.status_label.styleSheet()
