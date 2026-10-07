from pathlib import Path

import pytest

from blobs_project import config
from blobs_project.backend.regulation import (
    ProfileLoader,
    ProfileRequiredError,
    RegulationService,
    SampleExportStatus,
)


def test_self_driven_requires_imported_profile() -> None:
    service = RegulationService()

    with pytest.raises(ProfileRequiredError):
        service.toggle_self_driven()

    assert not service.is_running


def test_manual_regulation_toggle() -> None:
    service = RegulationService()

    service.toggle_regulation()
    assert service.regulation_active
    assert service.is_running

    service.toggle_regulation()
    assert not service.is_running


def test_self_driven_replaces_manual_regulation(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("20.0\n21.0\n", encoding="utf-8")
    service = RegulationService()
    service.set_profile(ProfileLoader.load_profile(path))
    service.toggle_regulation()

    service.toggle_self_driven()

    assert service.self_driven_active
    assert not service.regulation_active


def test_self_driven_stops_when_profile_finishes(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("25.0\n25.0\n25.0\n", encoding="utf-8")
    service = RegulationService()
    service.set_profile(ProfileLoader.load_profile(path))
    service.toggle_self_driven()

    for _ in range(40):
        service.tick(0.1)

    assert not service.self_driven_active
    assert service.profile_finished
    assert service.tank2_desired_cm == pytest.approx(25.0)
    assert service.elapsed_s >= 3.0


def test_desired_setpoint_is_clamped_to_tank_range() -> None:
    service = RegulationService()

    service.set_desired_tank2(120.0)

    assert service.tank2_desired_cm == config.TANK_LEVEL_MAX_CM


def test_regulation_moves_actual_level_towards_desired() -> None:
    service = RegulationService()
    service.set_desired_tank2(config.TANK_LEVEL_MAX_CM)
    service.toggle_regulation()

    for _ in range(100):
        service.tick(0.1)

    assert service.tank2_actual_cm > config.TANK_ACTUAL_LEVEL_CM


def test_trend_points_expose_recorded_samples() -> None:
    service = RegulationService()
    service.toggle_regulation()
    for _ in range(15):
        service.tick(0.1)

    points = service.trend_points()

    assert points
    assert all(len(point) == 2 for point in points)


def test_starting_a_run_clears_the_chart_and_resets_the_time() -> None:
    service = RegulationService()
    service.toggle_regulation()
    for _ in range(15):
        service.tick(0.1)
    service.toggle_regulation()
    assert service.trend_points()

    service.toggle_regulation()

    assert service.regulation_active
    assert service.trend_points() == []
    assert service.elapsed_s == 0.0
    assert service.chart_started


def test_force_reset_stops_both_modes_and_clears_the_chart(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("20.0\n21.0\n", encoding="utf-8")
    service = RegulationService()
    service.set_profile(ProfileLoader.load_profile(path))
    service.set_desired_tank2(25.0)
    service.toggle_self_driven()
    for _ in range(10):
        service.tick(0.1)

    service.force_reset()

    assert not service.is_running
    assert service.trend_points() == []
    assert service.elapsed_s == 0.0
    assert service.tank2_desired_cm == 0.0
    assert service.chart_started


def test_desired_trend_points_track_the_setpoint() -> None:
    service = RegulationService()
    service.set_desired_tank2(25.0)
    service.toggle_regulation()
    for _ in range(15):
        service.tick(0.1)
    service.set_desired_tank2(18.0)
    for _ in range(10):
        service.tick(0.1)

    desired = service.desired_trend_points()
    actual = service.trend_points()

    assert desired
    assert len(desired) == len(actual)
    assert [time_s for time_s, _ in desired] == [time_s for time_s, _ in actual]
    assert desired[0][1] == pytest.approx(25.0)
    assert desired[-1][1] == pytest.approx(18.0)


def test_import_profile_loads_and_stores_the_profile(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("20.0\n21.0\n", encoding="utf-8")
    service = RegulationService()

    loaded = service.import_profile(path)

    assert loaded is not None
    assert loaded.row_count == 2
    assert service.profile is loaded


def test_import_profile_reports_an_invalid_file(tmp_path: Path) -> None:
    path = tmp_path / "broken.csv"
    path.write_text("not-a-number\n", encoding="utf-8")
    service = RegulationService()

    assert service.import_profile(path) is None
    assert service.profile is None


def test_export_samples_writes_the_recorded_samples(tmp_path: Path) -> None:
    service = RegulationService()
    service.toggle_regulation()
    for _ in range(25):
        service.tick(0.1)
    path = tmp_path / "samples.csv"

    assert service.export_samples(path) is SampleExportStatus.WRITTEN
    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert header == "time_s,tank2_actual_cm"


def test_export_samples_without_samples_reports_an_empty_log(tmp_path: Path) -> None:
    service = RegulationService()

    assert (
        service.export_samples(tmp_path / "samples.csv")
        is SampleExportStatus.NO_SAMPLES
    )


def test_export_samples_reports_a_file_error(tmp_path: Path) -> None:
    service = RegulationService()
    service.toggle_regulation()
    for _ in range(25):
        service.tick(0.1)
    unwritable = tmp_path / "missing-directory" / "samples.csv"

    assert service.export_samples(unwritable) is SampleExportStatus.FAILED
