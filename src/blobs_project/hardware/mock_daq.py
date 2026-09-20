from .i_daq import DAQ


class MockDAQ(DAQ):
    def __init__(self) -> None:
        self._analog_inputs: dict[str, float] = {}
        self._analog_outputs: dict[str, float] = {}

    def read_voltage(self, channel: str) -> float:
        return self._analog_inputs.get(channel, 0.0)

    def write_voltage(self, channel: str, value: float) -> None:
        self._analog_outputs[channel] = value

    def set_input_voltage(self, channel: str, voltage: float) -> None:
        self._analog_inputs[channel] = voltage

    def get_output_voltage(self, channel: str) -> float:
        return self._analog_outputs.get(channel, 0.0)

    def read_digital(self, channel: str) -> bool:
        return True

    def write_digital(self, channel: str, value: bool) -> None:
        ...

    def close(self) -> None:
        ...
