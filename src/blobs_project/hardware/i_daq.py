"""
Interface for Data Aquisition Devices. This inteface can be useful
to create MockDAQ(DAQ) for tests.
"""

from abc import ABC, abstractmethod


class DAQ(ABC):
    @abstractmethod
    def read_voltage(self, channel: str) -> float:
        pass

    @abstractmethod
    def write_voltage(self, channel: str, value: float) -> None:
        pass

    @abstractmethod
    def read_digital(self, channel: str) -> bool:
        pass

    @abstractmethod
    def write_digital(self, channel: str, value: bool) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
