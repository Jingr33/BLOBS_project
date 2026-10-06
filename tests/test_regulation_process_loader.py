from pathlib import Path

import pytest

from blobs_project.backend.regulation import RegulationService
from blobs_project.backend.regulation.regulation_process_loader import (
    CsvExporter,
    CsvProfile,
    CsvProfileError,
    ProfileLoader,
)
from blobs_project.backend.regulation.sample_log import Sample


def test_csv_profile_accepts_single_column(tmp_path: Path) -> None:
    path = tmp_path / "t2.csv"
    path.write_text("10.0\n12.5\n15.0\n", encoding="utf-8")

    profile = ProfileLoader.load_profile(path)

    assert profile.row_count == 3
    assert profile.tank2_levels == (10.0, 12.5, 15.0)
    assert profile.duration_s == pytest.approx(3.0)


def test_csv_profile_skips_a_single_header_row(tmp_path: Path) -> None:
    path = tmp_path / "header.csv"
    path.write_text("level\n5.0\n10.0\n", encoding="utf-8")

    profile = ProfileLoader.load_profile(path)

    assert profile.tank2_levels == (5.0, 10.0)


def test_csv_profile_rejects_two_columns(tmp_path: Path) -> None:
    path = tmp_path / "both.csv"
    path.write_text("1.0,2.0\n3.0,4.0\n", encoding="utf-8")

    with pytest.raises(CsvProfileError):
        ProfileLoader.load_profile(path)


def test_csv_profile_rejects_non_numeric_rows() -> None:
    with pytest.raises(CsvProfileError):
        CsvProfile.from_text("10.0\nnot-a-number\n")


def test_csv_profile_rejects_file_without_rows() -> None:
    with pytest.raises(CsvProfileError):
        CsvProfile.from_text("\n   \n")


def test_csv_profile_reads_values_by_elapsed_time() -> None:
    profile = CsvProfile.from_text("5.0\n10.0\n15.0\n")

    assert profile.desired_at(0.0) == 5.0
    assert profile.desired_at(1.5) == 10.0
    assert profile.desired_at(99.0) == 15.0


def test_export_samples_csv_writes_the_recorded_columns(tmp_path: Path) -> None:
    path = tmp_path / "out.csv"

    written = CsvExporter.export_samples_csv(
        [Sample(1.0, 25.0, 19.5), Sample(2.0, 25.0, 21.0)], path
    )

    assert written is True
    assert path.read_text(encoding="utf-8").splitlines() == [
        "time_s,tank2_actual_cm",
        "1.0,19.50",
        "2.0,21.00",
    ]


def test_export_samples_csv_reports_missing_samples(tmp_path: Path) -> None:
    assert CsvExporter.export_samples_csv([], tmp_path / "out.csv") is False


def test_export_reports_missing_samples(tmp_path: Path) -> None:
    service = RegulationService()

    assert (
        CsvExporter.export_samples_csv(service.sample_log.samples, tmp_path / "out.csv")
        is False
    )


def test_export_writes_recorded_samples(tmp_path: Path) -> None:
    service = RegulationService()
    service.toggle_regulation()
    for _ in range(25):
        service.tick(0.1)
    path = tmp_path / "out.csv"

    assert CsvExporter.export_samples_csv(service.sample_log.samples, path) is True

    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "time_s,tank2_actual_cm"
    assert len(lines) >= 3
