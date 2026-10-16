"""Tests for the mock DAQ used in place of the NI card."""

from blobs_project.backend.hardware import MockDAQ


def test_mock_daq_reads_voltage() -> None:
    """A voltage set on an input is read back from that channel."""
    daq = MockDAQ()
    daq.set_input_voltage("ai0", 1.5)

    assert daq.read_voltage("ai0") == 1.5


def test_mock_daq_writes_voltage() -> None:
    """A voltage written to an output is recorded for that channel."""
    daq = MockDAQ()

    daq.write_voltage("ao0", 2.5)

    assert daq.get_output_voltage("ao0") == 2.5


def test_mock_daq_open_close() -> None:
    """``open`` and ``close`` toggle ``is_open``, which starts False."""
    daq = MockDAQ()
    assert daq.is_open is False

    daq.open()
    assert daq.is_open is True

    daq.close()
    assert daq.is_open is False
