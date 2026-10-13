"""In-memory DAQ for tests and for running without the NI card."""

from .DAQ_base import DAQ_base


class MockDAQ(DAQ_base):
    """Records outputs and serves inputs set by the caller; unset inputs read 0."""

    def __init__(self) -> None:
        """Start closed with no channel values."""
        self.is_open = False
        self._analog_inputs: dict[str, float] = {}
        self._analog_outputs: dict[str, float] = {}

    def open(self) -> None:
        """Mark the device open."""
        self.is_open = True

    def read_voltage(self, channel: str) -> float:
        """Return the voltage set on ``channel``, 0.0 if never set."""
        return self._analog_inputs.get(channel, 0.0)

    def write_voltage(self, channel: str, value: float) -> None:
        """Record ``value`` volts on output ``channel``."""
        self._analog_outputs[channel] = value

    def set_input_voltage(self, channel: str, voltage: float) -> None:
        """Make input ``channel`` read ``voltage``."""
        self._analog_inputs[channel] = voltage

    def get_output_voltage(self, channel: str) -> float:
        """Return the last voltage written to ``channel``, 0.0 if none."""
        return self._analog_outputs.get(channel, 0.0)

    def close(self) -> None:
        """Mark the device closed."""
        self.is_open = False
