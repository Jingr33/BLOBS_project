from blobs_project.hardware import MockDAQ


def test_mock_daq_reads_voltage() -> None:
    daq = MockDAQ()
    daq.set_input_voltage("ai0", 1.5)

    assert daq.read_voltage("ai0") == 1.5


def test_mock_daq_writes_voltage() -> None:
    daq = MockDAQ()

    daq.write_voltage("ao0", 2.5)

    assert daq.get_output_voltage("ao0") == 2.5
