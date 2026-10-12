from pathlib import Path

from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.regulation import RegulationService, SampleExportStatus


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
    assert header == "time_s,tank2_actual_cm"


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
