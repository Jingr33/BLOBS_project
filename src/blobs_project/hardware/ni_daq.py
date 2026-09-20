from .i_daq import DAQ
import nidaqmx
from nidaqmx.constants import TerminalConfiguration


class NIDAQ(DAQ):
    def __init__(self, device_name: str = "Dev1") -> None:
        self.device_name = device_name

    def read_voltage(self, channel: str) -> float:
        ...

    def write_voltage(self, channel: str, value: float) -> None:
        ...

    def read_digital(self, channel: str) -> bool:
        ...

    def write_digital(self, channel: str, value: bool) -> None:
        ...

    def close(self) -> None:
        ...

    def __str__(self) -> str:
        return f"Name: {self.device_name}"
