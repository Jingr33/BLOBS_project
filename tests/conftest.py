import pytest
from PyQt6.QtWidgets import QMessageBox

from blobs_project.frontend.widgets.tare_prompt import TarePrompt


@pytest.fixture(autouse=True)
def skip_tare_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Answer the pre-run tare prompt with No so start buttons never block."""
    monkeypatch.setattr(
        TarePrompt, "exec", lambda _: QMessageBox.StandardButton.No.value
    )
