import pytest
from PyQt6.QtWidgets import QMessageBox


@pytest.fixture(autouse=True)
def skip_tare_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Answer the pre-run tare prompt with No so start buttons never block."""
    monkeypatch.setattr(
        QMessageBox, "question", lambda *_: QMessageBox.StandardButton.No
    )
