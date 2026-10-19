from pathlib import Path

import pytest

from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.regulation import (
    CsvError,
    CsvProfile,
    RegulationService,
    SampleExportStatus,
)


def test_load_profile_reports_the_row_count(tmp_path: Path) -> None:
    path = tmp_path / "profile.csv"
    path.write_text("20.0\n21.0\n", encoding="utf-8")
    csv_service = CsvService()

    loaded = csv_service.load_profile(path)

    assert loaded is not None
    assert loaded.row_count == 2


def test_load_profile_reports_an_invalid_file(tmp_path: Path) -> None:
    path = tmp_path / "broken.csv"
    path.write_text("not-a-number\n", encoding="utf-8")
    csv_service = CsvService()

    assert csv_service.load_profile(path) is None


def test_load_reports_the_specific_profile_value_error(tmp_path: Path) -> None:
    path = tmp_path / "bad-level.csv"
    path.write_text("hladina_cm\n10\nbad-level\n", encoding="utf-8")

    with pytest.raises(CsvError) as error:
        CsvService().load_or_raise(path)
    assert str(error.value) == "line 3: level 'bad-level' is not a number"


def test_load_reports_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(CsvError, match="could not read file"):
        CsvService().load_or_raise(tmp_path / "missing.csv")


def test_export_samples_writes_the_recorded_samples(tmp_path: Path) -> None:
    regulation_service = RegulationService()
    regulation_service.toggle_regulation()
    for _ in range(25):
        regulation_service.tick(0.1)
    csv_service = CsvService()
    path = tmp_path / "samples.csv"

    assert (
        csv_service.export_samples(regulation_service.sample_log.samples, path)
        is SampleExportStatus.WRITTEN
    )
    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert (
        header == "time_s,desired_cm,actual_cm,pump_voltage_v,pump_power_w,flow_l_min"
    )


def test_export_samples_without_samples_reports_an_empty_log(tmp_path: Path) -> None:
    csv_service = CsvService()

    assert (
        csv_service.export_samples([], tmp_path / "samples.csv")
        is SampleExportStatus.NO_SAMPLES
    )


def test_export_samples_reports_a_file_error(tmp_path: Path) -> None:
    regulation_service = RegulationService()
    regulation_service.toggle_regulation()
    for _ in range(25):
        regulation_service.tick(0.1)
    csv_service = CsvService()
    unwritable = tmp_path / "missing-directory" / "samples.csv"

    assert (
        csv_service.export_samples(regulation_service.sample_log.samples, unwritable)
        is SampleExportStatus.FAILED
    )


def test_save_template_writes_a_loadable_profile(tmp_path: Path) -> None:
    """The template documents its format and still loads as a profile."""
    csv_service = CsvService()
    path = tmp_path / "template.csv"

    assert csv_service.save_template(path)
    text = path.read_text(encoding="utf-8")
    assert "# One desired lower-tank level in cm per row" in text
    assert "# Values must be numeric and between 3 and 22 cm" in text
    assert "hladina_cm\n" in text

    profile = CsvService().load_or_raise(path)

    assert isinstance(profile, CsvProfile)
    assert profile.tank2_levels == (10.0, 15.0, 12.5, 8.0)


def test_save_template_reports_a_file_error(tmp_path: Path) -> None:
    csv_service = CsvService()
    unwritable = tmp_path / "missing-directory" / "template.csv"

    assert not csv_service.save_template(unwritable)
