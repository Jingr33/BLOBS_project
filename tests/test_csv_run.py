from pathlib import Path

import pytest

from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.dtos import Sample
from blobs_project.backend.regulation import (
    CsvError,
    CsvProfile,
    RegulationService,
    RunCsv,
)

SAMPLES = (
    Sample(1.0, 10.0, 9.5, 0.4, 5.1, 4.2),
    Sample(2.0, 10.0, 9.9, 0.45, 5.3, 4.4),
)


def test_exported_run_is_read_back() -> None:
    """A run written to CSV comes back with every column."""
    assert RunCsv.from_text(RunCsv.to_text(SAMPLES)) == SAMPLES


def test_exported_run_is_plain_csv() -> None:
    lines = RunCsv.to_text(SAMPLES).splitlines()

    assert (
        lines[0] == "time_s,desired_cm,actual_cm,pump_voltage_v,pump_power_w,flow_l_min"
    )
    assert lines[1] == "1.0,10.00,9.50,4.200,5.100,0.400"


def test_run_with_a_broken_row_is_rejected() -> None:
    with pytest.raises(CsvError):
        RunCsv.from_text(RunCsv.to_text(SAMPLES) + "3.0,10.00\n")


def test_csv_service_tells_a_profile_from_a_recorded_run(tmp_path: Path) -> None:
    profile, run = tmp_path / "profile.csv", tmp_path / "run.csv"
    profile.write_text("hladina_cm\n10\n12.5\n", encoding="utf-8")
    run.write_text(RunCsv.to_text(SAMPLES), encoding="utf-8")

    assert CsvService().load(profile) == CsvProfile((10.0, 12.5))
    assert CsvService().load(run) == SAMPLES


def test_loaded_run_shows_its_chart_and_statistics() -> None:
    service = RegulationService()

    service.load_history(SAMPLES)

    assert service.chart_started
    assert service.trend_points() == [(1.0, 9.5), (2.0, 9.9)]
    assert service.statistics.duration_s == pytest.approx(1.0)


def test_run_cannot_be_loaded_during_regulation() -> None:
    service = RegulationService()
    service.toggle_regulation()

    with pytest.raises(RuntimeError):
        service.load_history(SAMPLES)


def test_profile_steps_last_the_chosen_duration(tmp_path: Path) -> None:
    """Each level is held for the step duration and the run ends after the last."""
    service = RegulationService()
    service.set_step_s(60.0)
    service.set_profile(CsvProfile((10.0, 12.0)))
    service.toggle_self_driven()

    for _ in range(650):
        service.tick(0.1)
    assert service.profile_step == 1
    assert service.regulation_values.tank2_desired_cm == 12.0

    for _ in range(600):
        service.tick(0.1)
    assert not service.self_driven_active
    assert service.profile_finished
    assert service.tower.pump_voltage == 0.0


def test_step_duration_cannot_change_during_a_profile() -> None:
    service = RegulationService()
    service.set_profile(CsvProfile((10.0,)))
    service.toggle_self_driven()

    service.set_step_s(10.0)

    assert service.profile is not None
    assert service.profile.step_s == service.step_s != 10.0


def test_export_writes_the_statistics_next_to_the_run(tmp_path: Path) -> None:
    """``run.csv`` gets ``run_statistics.csv`` with the summary and the steps."""
    levels = [0, 2, 5, 8, 9.5, 11, 12, 11, 10.4, 10.1, 10, 10, 10]
    samples = [Sample(float(t), 10.0, h, 0.0, 3.6) for t, h in enumerate(levels)]
    path = tmp_path / "run.csv"

    CsvService().export_samples(samples, path)

    lines = (tmp_path / "run_statistics.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "run_time_s,energy_wh,mean_power_w,within_1mm_percent"
    assert lines[1] == "12.0,0.012,3.60,"
    assert lines[3].startswith("step_start_s,from_cm,to_cm,rise_s")
    assert lines[4] == "0,0.00,10.00,3,6,20.0,8"


def test_run_is_told_from_a_profile() -> None:
    assert RunCsv.is_run(RunCsv.to_text(SAMPLES))
    assert not RunCsv.is_run("hladina_cm\n10\n")


def test_run_without_all_columns_is_rejected() -> None:
    with pytest.raises(CsvError):
        RunCsv.from_text("time_s,actual_cm\n1.0,9.5\n")


def test_run_without_samples_is_rejected() -> None:
    with pytest.raises(CsvError):
        RunCsv.from_text(RunCsv.to_text(()))
