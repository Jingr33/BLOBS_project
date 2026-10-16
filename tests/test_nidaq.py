"""Tests for ``NIDAQ`` against a fake ``nidaqmx`` package (no card needed)."""

import sys
import types
from typing import Any, Self

import pytest

from blobs_project.backend.hardware import NIDAQ, HardwareError


class _FakeError(Exception):
    """Stand-in for ``nidaqmx.errors.Error``."""


class _FakeDaqError(_FakeError):
    """Stand-in for ``nidaqmx.errors.DaqError``."""


class _Channels:
    """Records the physical channel added to a fake task."""

    def __init__(self, task: "_FakeTask") -> None:
        """Remember the ``task`` that owns these channels."""
        self._task = task

    def _add(self, physical_channel: str, **_: Any) -> None:
        """Store ``physical_channel`` on the task."""
        self._task.channel = physical_channel

    add_ai_voltage_chan = _add
    add_ao_voltage_chan = _add


class _FakeTask:
    """Context-managed task that reads fixed values and records writes."""

    fail_on: str | None = None
    tasks: list["_FakeTask"] = []

    def __init__(self) -> None:
        """Create channel groups and register the task in ``tasks``."""
        if self.fail_on == "task":
            raise _FakeDaqError("device unplugged")
        self.channel = ""
        self.written: Any = None
        self.ai_channels = self.ao_channels = _Channels(self)
        _FakeTask.tasks.append(self)

    def __enter__(self) -> Self:
        """Return the task itself."""
        return self

    def __exit__(self, *_: object) -> None:
        """Do nothing on exit."""

    def read(self) -> float | bool:
        """Return a fixed analog reading of 1.25 V."""
        if self.fail_on == "read":
            raise _FakeDaqError("read failed")
        return 1.25

    def write(self, value: Any) -> None:
        """Record ``value``, or raise if writes are set to fail."""
        if self.fail_on == "write":
            raise _FakeDaqError("write failed")
        self.written = value


def make_fake_nidaqmx(
    device_ok: bool = True, fail_on: str | None = None
) -> types.ModuleType:
    """Return a fake ``nidaqmx`` that fails in ``fail_on`` (task, read or write)."""
    errors = types.ModuleType("nidaqmx.errors")
    errors.Error = _FakeError  # type: ignore[attr-defined]
    errors.DaqError = _FakeDaqError  # type: ignore[attr-defined]

    class Device:
        """Fake device whose ``product_type`` fails unless ``device_ok``."""

        def __init__(self, name: str) -> None:
            """Store the device ``name``."""
            self.name = name

        @property
        def product_type(self) -> str:
            """Return the product name or raise ``DaqError``."""
            if not device_ok:
                raise _FakeDaqError(f"device {self.name} not found")
            return "USB-6001"

    system = types.ModuleType("nidaqmx.system")
    system.Device = Device  # type: ignore[attr-defined]
    constants = types.ModuleType("nidaqmx.constants")
    constants.TerminalConfiguration = types.SimpleNamespace(  # type: ignore[attr-defined]
        RSE="RSE"
    )
    _FakeTask.fail_on = fail_on
    _FakeTask.tasks = []
    module = types.ModuleType("nidaqmx")
    module.Task = _FakeTask  # type: ignore[attr-defined]
    module.errors = errors  # type: ignore[attr-defined]
    module.system = system  # type: ignore[attr-defined]
    module.constants = constants  # type: ignore[attr-defined]
    return module


def install(monkeypatch: pytest.MonkeyPatch, module: types.ModuleType) -> None:
    """Put ``module`` and its submodules in ``sys.modules`` for one test."""
    monkeypatch.setitem(sys.modules, "nidaqmx", module)
    for name in ("errors", "system", "constants"):
        monkeypatch.setitem(sys.modules, f"nidaqmx.{name}", getattr(module, name))


def make_open_daq(monkeypatch: pytest.MonkeyPatch, fail_on: str | None = None) -> NIDAQ:
    """Return an opened ``NIDAQ`` over a fake driver that fails on ``fail_on``."""
    install(monkeypatch, make_fake_nidaqmx(fail_on=fail_on))
    daq = NIDAQ()
    daq.open()
    return daq


def test_open_missing_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without the nidaqmx package, ``open`` raises ``HardwareError``."""
    monkeypatch.setitem(sys.modules, "nidaqmx", None)
    with pytest.raises(HardwareError):
        NIDAQ().open()


def test_open_missing_device(monkeypatch: pytest.MonkeyPatch) -> None:
    """An absent device makes ``open`` raise ``HardwareError`` naming it."""
    install(monkeypatch, make_fake_nidaqmx(device_ok=False))
    with pytest.raises(HardwareError, match="Dev1"):
        NIDAQ().open()


def test_read_before_open() -> None:
    """Reading before ``open`` raises ``HardwareError``."""
    with pytest.raises(HardwareError):
        NIDAQ().read_voltage("ai0")


def test_read_voltage_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    """An opened device reads the analog value from ``Dev1/ai0``."""
    daq = make_open_daq(monkeypatch)

    assert daq.read_voltage("ai0") == 1.25
    assert _FakeTask.tasks[-1].channel == "Dev1/ai0"


def test_read_error_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    """A driver error during a read becomes ``HardwareError`` with its cause."""
    daq = make_open_daq(monkeypatch, fail_on="read")

    with pytest.raises(HardwareError) as info:
        daq.read_voltage("ai0")
    assert isinstance(info.value.__cause__, _FakeDaqError)


def test_write_error_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    """A driver error during a write becomes ``HardwareError``."""
    daq = make_open_daq(monkeypatch, fail_on="write")

    with pytest.raises(HardwareError):
        daq.write_voltage("ao1", 1.0)


def test_write_out_of_range_is_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A voltage outside +-10 V is a caller bug and raises ``ValueError``."""
    daq = make_open_daq(monkeypatch)

    with pytest.raises(ValueError):
        daq.write_voltage("ao1", 10.5)


def test_close_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Closing twice is safe, and reading after ``close`` raises."""
    daq = make_open_daq(monkeypatch)

    daq.close()
    daq.close()
    with pytest.raises(HardwareError):
        daq.read_voltage("ai0")


def test_task_creation_error_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    """A device lost before the task starts (USB pulled) becomes ``HardwareError``."""
    daq = make_open_daq(monkeypatch, fail_on="task")

    with pytest.raises(HardwareError):
        daq.read_voltage("ai0")
