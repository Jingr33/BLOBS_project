import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QFileDialog, QWidget

from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.regulation import RegulationService
from blobs_project.frontend.actions import ActionDispatcher, ActionId

_APP = QApplication.instance() or QApplication([])


def test_import_action_shows_csv_validation_details(tmp_path, monkeypatch) -> None:
    path = tmp_path / "bad-profile.csv"
    path.write_text("hladina_cm\n10\nbad-value\n", encoding="utf-8")
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", lambda *_args: (str(path), "CSV files (*.csv)")
    )
    dispatcher = ActionDispatcher(RegulationService(), CsvService())

    message = dispatcher.execute(ActionId.IMPORT_CSV, QWidget())

    assert message == "CSV import failed: line 3: level 'bad-value' is not a number"
