from pathlib import Path

import pytest

from blobs_project import config
from blobs_project.backend.dtos import Sample
from blobs_project.backend.regulation import (
    CsvError,
    CsvExporter,
    CsvProfile,
    ProfileLoader,
    RegulationService,
)


def test_csv_profile_accepts_single_column(tmp_path: Path) -> None:
    path = tmp_path / "t2.csv"
    path.write_text("10.0\n12.5\n15.0\n", encoding="utf-8")

    profile = ProfileLoader.load_profile(path)

    assert profile.row_count == 3
    assert profile.tank2_levels == (10.0, 12.5, 15.0)
    assert profile.duration_s == pytest.approx(3 * config.PROFILE_STEP_S)


def test_csv_profile_skips_a_single_header_row(tmp_path: Path) -> None:
    path = tmp_path / "header.csv"
    path.write_text("level\n5.0\n10.0\n", encoding="utf-8")

    profile = ProfileLoader.load_profile(path)

    assert profile.tank2_levels == (5.0, 10.0)


def test_csv_profile_rejects_two_columns(tmp_path: Path) -> None:
    path = tmp_path / "both.csv"
    path.write_text("1.0,2.0\n3.0,4.0\n", encoding="utf-8")

    with pytest.raises(CsvError):
        ProfileLoader.load_profile(path)


def test_csv_profile_rejects_non_numeric_rows() -> None:
    with pytest.raises(CsvError, match=r"line 2: level 'not-a-number' is not a number"):
        CsvProfile.from_text("10.0\nnot-a-number\n")


def test_csv_profile_comments_and_blank_rows_are_ignored() -> None:
    profile = CsvProfile.from_text(
        "# profile levels\n\n# one level per row\nhladina_cm\n10\n12.5\n"
    )

    assert profile.tank2_levels == (10.0, 12.5)


def test_csv_profile_reports_non_finite_levels() -> None:
    with pytest.raises(CsvError, match=r"line 2: level 'nan' must be a finite number"):
        CsvProfile.from_text("hladina_cm\nnan\n")


def test_csv_profile_reports_out_of_range_levels() -> None:
    with pytest.raises(
        CsvError, match=r"line 2: level 25 cm is outside the allowed range"
    ):
        CsvProfile.from_text("hladina_cm\n25\n")


def test_csv_profile_reports_extra_columns() -> None:
    with pytest.raises(CsvError, match=r"line 1: expected 1 column.*found 2"):
        CsvProfile.from_text("10,11\n")


def test_csv_profile_rejects_file_without_rows() -> None:
    with pytest.raises(CsvError):
        CsvProfile.from_text("\n   \n")


def test_csv_profile_reads_values_by_elapsed_time() -> None:
    profile = CsvProfile.from_text("5.0\n10.0\n15.0\n").with_step(1.0)

    assert profile.desired_at(0.0) == 5.0
    assert profile.desired_at(1.5) == 10.0
    assert profile.desired_at(99.0) == 15.0


def test_export_samples_writes_the_recorded_columns(tmp_path: Path) -> None:
    path = tmp_path / "out.csv"

    written = CsvExporter.export_samples(
        [Sample(1.0, 25.0, 19.5), Sample(2.0, 25.0, 21.0)], path
    )

    assert written is True
    assert path.read_text(encoding="utf-8").splitlines() == [
        "time_s,desired_cm,actual_cm,pump_voltage_v,pump_power_w,flow_l_min",
        "1.0,25.00,19.50,0.000,0.000,0.000",
        "2.0,25.00,21.00,0.000,0.000,0.000",
    ]


def test_export_samples_reports_missing_samples(tmp_path: Path) -> None:
    assert CsvExporter.export_samples([], tmp_path / "out.csv") is False


def test_export_reports_missing_samples(tmp_path: Path) -> None:
    regulation_service = RegulationService()

    assert (
        CsvExporter.export_samples(
            regulation_service.sample_log.samples, tmp_path / "out.csv"
        )
        is False
    )


def test_export_writes_recorded_samples(tmp_path: Path) -> None:
    regulation_service = RegulationService()
    regulation_service.toggle_regulation()
    for _ in range(25):
        regulation_service.tick(0.1)
    path = tmp_path / "out.csv"

    assert (
        CsvExporter.export_samples(regulation_service.sample_log.samples, path) is True
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    assert (
        lines[0] == "time_s,desired_cm,actual_cm,pump_voltage_v,pump_power_w,flow_l_min"
    )
    assert len(lines) >= 3
