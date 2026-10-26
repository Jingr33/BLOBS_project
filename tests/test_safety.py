import math
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

from blobs_project import Application, config
from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.hardware import (
    HardwareError,
    MockDAQ,
    Tower,
    TowerCalibration,
)
from blobs_project.backend.regulation import (
    ControllerError,
    CsvError,
    MPCRegulationController,
    ProfileLoader,
    RegulationControllerBase,
    RegulationService,
)
from blobs_project.frontend.actions import ActionDispatcher, ActionId
from blobs_project.frontend.frames.footer_frame import FooterFrame
from blobs_project.frontend.frames.header_frame import HeaderFrame
from blobs_project.frontend.frames.regulation_frame import RegulationFrame
from blobs_project.frontend.widgets.tank_control import TankControl

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


class _FailingWriteDAQ(MockDAQ):
    def __init__(self) -> None:
        super().__init__()
        self.fail_writes = False

    def write_voltage(self, channel: str, value: float) -> None:
        if self.fail_writes:
            raise HardwareError("write failed")
        super().write_voltage(channel, value)


class _FailingController(RegulationControllerBase):
    def reset(self) -> None:
        pass

    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        raise ControllerError("solver failed")


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


def test_raw_high_level_stops_without_waiting_for_median_filter() -> None:
    service, daq = make_service(10.0)
    service.toggle_regulation()
    run(service, 2.0)
    assert service.is_running

    set_level(daq, config.LEVEL_TRIP_CM + 0.5)
    run(service, config.CONTROL_PERIOD_S)

    assert not service.is_running
    assert pump_v(daq) == 0.0
    assert service.regulation_values.tank2_actual_cm >= config.LEVEL_TRIP_CM


def test_pump_limit_status_uses_mpc_and_tower_output_bounds() -> None:
    service = RegulationService(
        MPCRegulationController(),
        Tower(MockDAQ(), TowerCalibration(max_pump_v=4.0)),
    )
    service.toggle_regulation()
    service.regulation_values.pump_voltage_v = 1.0
    assert not service.pump_at_limit

    service.regulation_values.pump_voltage_v = 4.0
    assert service.pump_at_limit


def test_level_observer_warns_before_the_warning_level_is_reached() -> None:
    service, daq = make_service(18.0)
    run(service, 1.0)
    assert not service.overflow_warning

    set_level(daq, 20.0)
    run(service, 1.0)

    assert service.regulation_values.tank2_actual_cm < config.LEVEL_WARNING_CM
    assert service.predicted_level_cm is not None
    assert service.predicted_level_cm >= config.LEVEL_WARNING_CM
    assert service.overflow_warning


def test_failed_pump_stop_is_reported_as_uncertain() -> None:
    daq = _FailingWriteDAQ()
    service = RegulationService(_RecordingController(), Tower(daq))
    service.toggle_regulation()
    run(service, 1.0)
    assert service.regulation_values.pump_voltage_v == 5.0
    daq.fail_writes = True

    service.toggle_regulation()

    assert not service.is_running
    assert service.pump_state_uncertain
    assert service.regulation_values.pump_voltage_v == 5.0
    assert service.fault is not None and "pump off unconfirmed" in service.fault


def test_regulation_does_not_start_when_pump_zero_cannot_be_confirmed() -> None:
    daq = _FailingWriteDAQ()
    daq.fail_writes = True
    service = RegulationService(_RecordingController(), Tower(daq))

    service.toggle_regulation()

    assert not service.is_running
    assert service.pump_state_uncertain
    assert service.fault is not None and "pump off unconfirmed" in service.fault


def test_controller_failure_stops_the_pump_and_reports_a_fault() -> None:
    daq = MockDAQ()
    service = RegulationService(_FailingController(), Tower(daq))
    service.toggle_regulation()

    run(service, 1.0)

    assert not service.is_running
    assert pump_v(daq) == 0.0
    assert service.fault is not None and "solver failed" in service.fault


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

    with pytest.raises(CsvError, match="line 3"):
        ProfileLoader.load_profile(path)


def test_profile_rejects_nan_level(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text(f"10\n{math.nan}\n", encoding="utf-8")

    with pytest.raises(CsvError):
        ProfileLoader.load_profile(path)


def test_desired_spin_box_allows_only_the_setpoint_range() -> None:
    frame = RegulationFrame(RegulationService())
    control = frame.findChild(TankControl)
    assert control is not None
    spin = control.desired_spin

    assert spin.minimum() == config.SETPOINT_MIN_CM
    assert spin.maximum() == config.SETPOINT_MAX_CM


def test_emergency_button_stops_and_shows_the_reason() -> None:
    service, daq = make_service(10.0)
    window = Application.create_window(service, CsvService())
    window.show()
    _APP.processEvents()
    header = window.findChild(HeaderFrame)
    frame = window.findChild(RegulationFrame)
    assert header is not None and frame is not None
    buttons = {button.text(): button for button in header.findChildren(QPushButton)}
    regulation_buttons = {
        button.text(): button for button in frame.findChildren(QPushButton)
    }
    alert = frame.findChild(QLabel, "alert")
    assert alert is not None and alert.isHidden()
    regulation_buttons["Start regulation"].click()
    run(service, 1.0)

    buttons["EMERGENCY STOP"].click()
    _APP.processEvents()

    assert not service.is_running
    assert pump_v(daq) == 0.0
    assert not alert.isHidden()
    assert alert.text() == "Stopped: emergency stop"
    window.close()


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

    assert config.STATE_ALARM in footer.status_label.styleSheet()
