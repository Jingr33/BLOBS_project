import nidaqmx
from nidaqmx.constants import TerminalConfiguration

from .DAQ_base import DAQ_base


class NIDAQ(DAQ_base):
    def __init__(self, device_name: str = "Dev1") -> None:
        self.device_name = device_name

    def read_voltage(self, channel: str) -> float:
        physical_channel = f"{self.device_name}/{channel}"
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(
                physical_channel,
                terminal_config=TerminalConfiguration.RSE,
                min_val=-10.0,
                max_val=10.0,
            )
            return float(task.read())

    def write_voltage(self, channel: str, value: float) -> None:
        if not -10.0 <= value <= 10.0:
            raise ValueError("Voltage must be between -10 V and +10 V")
        physical_channel = f"{self.device_name}/{channel}"
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                physical_channel, min_val=-10.0, max_val=10.0
            )
            task.write(value)

    def read_digital(self, channel: str) -> bool:
        return True

    def write_digital(self, channel: str, value: bool) -> None:
        pass

    def close(self) -> None:
        pass

    def __str__(self) -> str:
        return f"Name: {self.device_name}"
