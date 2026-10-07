import pytest

from blobs_project import config
from blobs_project.backend.regulation import (
    ProportionalController,
    RegulationControllerBase,
    RegulationService,
)


class _RecordingController(RegulationControllerBase):
    def __init__(self) -> None:
        self.calls: list[tuple[float, float, float]] = []
        self.reset_count = 0

    def reset(self) -> None:
        self.reset_count += 1

    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        self.calls.append((dt_s, desired_cm, actual_cm))
        return 5.0


def test_proportional_controller_scales_the_error_by_gain_and_time() -> None:
    controller = ProportionalController()

    change = controller.compute(0.1, 30.0, 10.0)

    assert change == pytest.approx((30.0 - 10.0) * 0.1 * config.LEVEL_RESPONSE_RATE)


def test_proportional_controller_never_overshoots_the_setpoint() -> None:
    controller = ProportionalController()

    change = controller.compute(1000.0, 30.0, 10.0)

    assert change == pytest.approx(30.0 - 10.0)


def test_service_uses_the_injected_controller() -> None:
    controller = _RecordingController()
    service = RegulationService(controller)
    service.set_desired_tank2(10.0)

    service.toggle_regulation()
    service.tick(0.1)

    assert controller.reset_count == 1
    assert controller.calls == [(0.1, 10.0, config.TANK_ACTUAL_LEVEL_CM)]
    assert service.tank2_actual_cm == pytest.approx(config.TANK_ACTUAL_LEVEL_CM + 5.0)
