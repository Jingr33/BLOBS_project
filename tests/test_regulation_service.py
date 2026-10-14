from pathlib import Path

import pytest

from blobs_project import config
from blobs_project.backend.regulation import (
    ProfileLoader,
    ProfileRequiredError,
    RegulationService,
)


def test_self_driven_requires_imported_profile() -> None:
    regulation_service = RegulationService()

    with pytest.raises(ProfileRequiredError):
        regulation_service.toggle_self_driven()

    assert not regulation_service.is_running


def test_manual_regulation_toggle() -> None:
    regulation_service = RegulationService()

    regulation_service.toggle_regulation()
    assert regulation_service.regulation_active
    assert regulation_service.is_running

    regulation_service.toggle_regulation()
    assert not regulation_service.is_running


def test_self_driven_replaces_manual_regulation(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("20.0\n21.0\n", encoding="utf-8")
    regulation_service = RegulationService()
    regulation_service.set_profile(ProfileLoader.load_profile(path))
    regulation_service.toggle_regulation()

    regulation_service.toggle_self_driven()

    assert regulation_service.self_driven_active
    assert not regulation_service.regulation_active


def test_self_driven_stops_when_profile_finishes(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("25.0\n25.0\n25.0\n", encoding="utf-8")
    regulation_service = RegulationService()
    regulation_service.set_profile(ProfileLoader.load_profile(path))
    regulation_service.toggle_self_driven()

    for _ in range(40):
        regulation_service.tick(0.1)

    assert not regulation_service.self_driven_active
    assert regulation_service.profile_finished
    assert regulation_service.regulation_values.tank2_desired_cm == pytest.approx(25.0)
    assert regulation_service.elapsed_s >= 3.0


def test_desired_setpoint_is_clamped_to_tank_range() -> None:
    regulation_service = RegulationService()

    regulation_service.regulation_values.tank2_desired_cm = 120.0

    assert (
        regulation_service.regulation_values.tank2_desired_cm
        == config.TANK_LEVEL_MAX_CM
    )


def test_regulation_moves_actual_level_towards_desired() -> None:
    regulation_service = RegulationService()
    regulation_service.regulation_values.tank2_desired_cm = config.TANK_LEVEL_MAX_CM
    regulation_service.toggle_regulation()

    for _ in range(100):
        regulation_service.tick(0.1)

    assert (
        regulation_service.regulation_values.tank2_actual_cm
        > config.TANK_ACTUAL_LEVEL_CM
    )


def test_trend_points_expose_recorded_samples() -> None:
    regulation_service = RegulationService()
    regulation_service.toggle_regulation()
    for _ in range(15):
        regulation_service.tick(0.1)

    points = regulation_service.trend_points()

    assert points
    assert all(len(point) == 2 for point in points)


def test_starting_a_run_clears_the_chart_and_resets_the_time() -> None:
    regulation_service = RegulationService()
    regulation_service.toggle_regulation()
    for _ in range(15):
        regulation_service.tick(0.1)
    regulation_service.toggle_regulation()
    assert regulation_service.trend_points()

    regulation_service.toggle_regulation()

    assert regulation_service.regulation_active
    assert regulation_service.trend_points() == []
    assert regulation_service.elapsed_s == 0.0
    assert regulation_service.chart_started


def test_force_reset_stops_both_modes_and_clears_the_chart(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("20.0\n21.0\n", encoding="utf-8")
    regulation_service = RegulationService()
    regulation_service.set_profile(ProfileLoader.load_profile(path))
    regulation_service.regulation_values.tank2_desired_cm = 25.0
    regulation_service.toggle_self_driven()
    for _ in range(10):
        regulation_service.tick(0.1)

    regulation_service.force_reset()

    assert not regulation_service.is_running
    assert regulation_service.trend_points() == []
    assert regulation_service.elapsed_s == 0.0
    assert regulation_service.regulation_values.tank2_desired_cm == 0.0
    assert regulation_service.chart_started


def test_desired_trend_points_track_the_setpoint() -> None:
    regulation_service = RegulationService()
    regulation_service.regulation_values.tank2_desired_cm = 25.0
    regulation_service.toggle_regulation()
    for _ in range(15):
        regulation_service.tick(0.1)
    regulation_service.regulation_values.tank2_desired_cm = 18.0
    for _ in range(10):
        regulation_service.tick(0.1)

    desired = regulation_service.desired_trend_points()
    actual = regulation_service.trend_points()

    assert desired
    assert len(desired) == len(actual)
    assert [time_s for time_s, _ in desired] == [time_s for time_s, _ in actual]
    assert desired[0][1] == pytest.approx(25.0)
    assert desired[-1][1] == pytest.approx(18.0)


def test_remaining_time_counts_down_only_in_self_driven_mode(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("20.0\n21.0\n22.0\n", encoding="utf-8")
    regulation_service = RegulationService()
    regulation_service.set_profile(ProfileLoader.load_profile(path))

    assert regulation_service.remaining_s is None

    regulation_service.toggle_self_driven()
    assert regulation_service.remaining_s == pytest.approx(3.0)

    regulation_service.tick(1.0)
    assert regulation_service.remaining_s == pytest.approx(2.0)

    regulation_service.toggle_self_driven()
    assert regulation_service.remaining_s is None


def test_self_driven_desired_line_covers_the_whole_profile_from_the_start(
    tmp_path: Path,
) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("5.0\n10.0\n15.0\n20.0\n", encoding="utf-8")
    regulation_service = RegulationService()
    regulation_service.set_profile(ProfileLoader.load_profile(path))
    regulation_service.toggle_self_driven()
    regulation_service.tick(0.1)

    desired = regulation_service.desired_trend_points()

    assert desired[0] == (0.0, 5.0)
    assert desired[-1] == (4.0, 20.0)
    assert [time_s for time_s, _ in desired] == sorted(time_s for time_s, _ in desired)
    assert regulation_service.trend_points() == []


def test_flow_and_power_are_measured_while_the_level_rises() -> None:
    regulation_service = RegulationService()
    regulation_service.regulation_values.tank2_desired_cm = config.TANK_LEVEL_MAX_CM
    regulation_service.toggle_regulation()
    regulation_service.tick(0.1)

    assert regulation_service.regulation_values.flow_l_min > 0.0
    assert regulation_service.regulation_values.pump_power_w > 0.0

    for _ in range(10):
        regulation_service.tick(0.1)

    assert regulation_service.flow_trend_points()
    assert regulation_service.pump_power_trend_points()

    regulation_service.toggle_regulation()
    regulation_service.tick(0.1)

    assert regulation_service.regulation_values.flow_l_min == 0.0
    assert regulation_service.regulation_values.pump_power_w == 0.0
