import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from blobs_project.frontend.widgets.tank_control import TankControl

_APP = QApplication.instance() or QApplication([])


def test_desired_is_sent_when_editing_finishes() -> None:
    """Typed digits are not sent one by one, only the finished value."""
    control = TankControl("T2", "#ffffff")

    assert not control.desired_spin.keyboardTracking()


def test_refresh_does_not_overwrite_the_value_being_typed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    control = TankControl("T2", "#ffffff")
    control.desired_spin.setValue(12.0)
    monkeypatch.setattr(control.desired_spin, "hasFocus", lambda: True)

    control.set_values(10.0, 20.0, 0.0)

    assert control.desired_spin.value() == 12.0


def test_refresh_shows_the_service_setpoint_when_not_editing() -> None:
    control = TankControl("T2", "#ffffff")

    control.set_values(10.0, 15.0, 0.0)

    assert control.desired_spin.value() == 15.0
