import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from blobs_project import config
from blobs_project.backend.hardware import SimulatedDAQ, Tower
from blobs_project.backend.regulation import RegulationService, Sample
from blobs_project.backend.statistics import run_statistics
from blobs_project.frontend.widgets.statistics_view import StatisticsView

_APP = QApplication.instance() or QApplication([])


def samples_of(
    levels: list[float], desired: float, power_w: float = 0.0
) -> list[Sample]:
    """Return one sample per second following ``levels`` at a fixed setpoint."""
    return [
        Sample(float(t), desired, level, 0.0, power_w) for t, level in enumerate(levels)
    ]


def test_empty_run_has_no_statistics() -> None:
    statistics = run_statistics([])

    assert statistics.steps == ()
    assert statistics.efficiency_percent is None
    assert statistics.energy_wh == 0.0


def test_energy_integrates_the_pump_power() -> None:
    """3600 s at 10 W is 10 Wh."""
    samples = [
        Sample(0.0, 10.0, 10.0, 0.0, 10.0),
        Sample(3600.0, 10.0, 10.0, 0.0, 10.0),
    ]

    statistics = run_statistics(samples)

    assert statistics.energy_wh == pytest.approx(10.0)
    assert statistics.mean_power_w == pytest.approx(10.0)


def test_step_metrics_of_an_overshooting_response() -> None:
    """A 0 -> 10 cm step that peaks at 12 cm and then settles at 10 cm."""
    levels = [0, 2, 5, 8, 9.5, 11, 12, 11, 10.4, 10.1, 10, 10, 10]
    statistics = run_statistics(samples_of(levels, 10.0))

    (step,) = statistics.steps
    assert (step.from_cm, step.to_cm) == (0.0, 10.0)
    assert step.rise_time_s == pytest.approx(4.0 - 1.0)
    assert step.peak_time_s == pytest.approx(6.0)
    assert step.overshoot_percent == pytest.approx(20.0)
    assert step.settling_time_s == pytest.approx(8.0)


def test_step_without_overshoot_has_no_peak_time() -> None:
    levels = [0, 3, 6, 8, 9, 9.6, 9.9, 10, 10]
    (step,) = run_statistics(samples_of(levels, 10.0)).steps

    assert step.overshoot_percent == 0.0
    assert step.peak_time_s is None
    assert step.settling_time_s is not None


def test_overshoot_within_sensor_noise_is_not_counted() -> None:
    """Exceeding a 10 cm step by 0.5 mm is noise, not overshoot."""
    levels = [0, 4, 8, 9.6, 10.05, 10.0, 10.0]
    (step,) = run_statistics(samples_of(levels, 10.0)).steps

    assert step.overshoot_percent == 0.0
    assert step.peak_time_s is None


def test_unsettled_step_has_no_settling_time() -> None:
    (step,) = run_statistics(samples_of([0, 3, 6, 8], 10.0)).steps

    assert step.settling_time_s is None


def test_downward_step_is_measured_like_an_upward_one() -> None:
    levels = [15, 13, 11, 10.2, 10, 10]
    (step,) = run_statistics(samples_of(levels, 10.0)).steps

    assert (step.from_cm, step.to_cm) == (15.0, 10.0)
    assert step.rise_time_s is not None
    assert step.overshoot_percent == 0.0


def test_every_setpoint_change_starts_a_new_step() -> None:
    samples = samples_of([0, 5, 10, 10], 10.0) + [
        Sample(4.0, 12.0, 10.0),
        Sample(5.0, 12.0, 12.0),
    ]

    steps = run_statistics(samples).steps

    assert [(s.start_s, s.from_cm, s.to_cm) for s in steps] == [
        (0.0, 0.0, 10.0),
        (4.0, 10.0, 12.0),
    ]


def test_efficiency_skips_the_time_after_a_change() -> None:
    """Off by 5 mm during the skip window, then half of the time within 1 mm."""
    skip = int(config.EFFICIENCY_SKIP_S)
    levels = [9.5] * skip + [10.0] * 100 + [10.5] * 100
    statistics = run_statistics(samples_of(levels, 10.0))

    assert statistics.efficiency_percent == pytest.approx(50.0, abs=1.0)


def test_service_statistics_follow_a_simulated_run() -> None:
    """A run on the simulated tower yields one settled step and some energy."""
    clock = [0.0]
    service = RegulationService(tower=Tower(SimulatedDAQ(clock=lambda: clock[0])))
    service.regulation_values.tank2_desired_cm = 10.0
    service.toggle_regulation()
    for _ in range(4000):
        clock[0] += 0.1
        service.tick(0.1)

    statistics = service.statistics

    assert len(statistics.steps) == 1
    assert statistics.steps[0].settling_time_s is not None
    assert statistics.energy_wh > 0.0
    assert statistics.efficiency_percent is not None


def test_statistics_view_lists_the_steps() -> None:
    view = StatisticsView()
    levels = [0, 2, 5, 8, 9.5, 11, 12, 11, 10.4, 10.1, 10, 10, 10]

    view.set_statistics(run_statistics(samples_of(levels, 10.0)))

    assert view.table.rowCount() == 1
    items = [view.table.item(0, column) for column in range(6)]
    cells = [item.text() if item is not None else None for item in items]
    assert cells == ["0", "0.0 → 10.0", "3", "6", "20.0", "8"]
