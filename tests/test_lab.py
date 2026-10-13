"""Tests for the lab bench CLI over ``MockDAQ``."""

import io

import pytest

from blobs_project import lab
from blobs_project.backend import HardwareError, MockDAQ, Tower


class RecordingDAQ(MockDAQ):
    """Mock DAQ that keeps every analog write in ``writes``."""

    def __init__(self) -> None:
        """Start with no writes."""
        super().__init__()
        self.writes: list[float] = []

    def write_voltage(self, channel: str, value: float) -> None:
        """Record ``value`` and write it."""
        self.writes.append(value)
        super().write_voltage(channel, value)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``time.sleep`` in the lab module return at once."""
    monkeypatch.setattr(lab.time, "sleep", lambda s: None)


def test_ramp_steps_at_most_0_1_v() -> None:
    """The pump reaches the target in steps of at most 0.1 V."""
    daq = RecordingDAQ()

    lab.ramp(Tower(daq), 1.0)

    steps = [b - a for a, b in zip(daq.writes, daq.writes[1:])]
    assert daq.writes[-1] == pytest.approx(1.0)
    assert max(abs(s) for s in steps) <= 0.1 + 1e-9


def test_run_logs_every_level() -> None:
    """Each level is held for ``hold`` seconds and logged with ai0 and level."""
    daq = MockDAQ()
    daq.set_input_voltage("ai0", 1.255)
    log = io.StringIO()

    lab.run(Tower(daq), [1.0, 2.0], hold=2.0, period=1.0, log=log)

    rows = log.getvalue().splitlines()
    assert len(rows) == 4
    assert [row.split(",")[1] for row in rows] == ["1.000"] * 2 + ["2.000"] * 2
    assert all(row.endswith(",1.2550,3.060") for row in rows)


def test_main_writes_csv_header(tmp_path: pytest.TempPathFactory) -> None:
    """``run --csv`` writes the header the analysis scripts read."""
    path = f"{tmp_path}/out.csv"

    assert lab.main(["--mock", "run", "0", "--hold", "0", "--csv", path]) == 0
    with open(path) as f:
        assert f.readline().strip() == "t_s,ao_v,ai0,level_cm"


@pytest.mark.parametrize(
    "argv", [["run", "8", "--max-v", "8"], ["run", "6"], ["run", "1", "2"]]
)
def test_main_rejects_bad_args(argv: list[str]) -> None:
    """Above 7.5 V, above --max-v, or several levels without --hold exit with 2."""
    with pytest.raises(SystemExit) as info:
        lab.main(["--mock", *argv])
    assert info.value.code == 2


def test_main_tare_prints_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """``tare`` prints the measured zero to pass as ``--zero-v``."""
    assert lab.main(["--mock", "tare", "--samples", "1"]) == 0
    assert "--zero-v 0.0000" in capsys.readouterr().out


def test_main_reports_hardware_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A ``HardwareError`` is printed without a traceback and exits 1."""

    def fail_open(self: MockDAQ) -> None:
        """Simulate a missing card."""
        raise HardwareError("Dev1 not found")

    monkeypatch.setattr(MockDAQ, "open", fail_open)

    assert lab.main(["--mock", "run", "0", "--hold", "0"]) == 1
    assert "Dev1 not found" in capsys.readouterr().err
