"""Interface for data acquisition devices, real (``NIDAQ``) or mocked (``MockDAQ``)."""

from abc import ABC, abstractmethod


class DAQ_base(ABC):
    """Raw analog voltage I/O on channels such as ``ai0`` or ``ao1``."""

    @abstractmethod
    def open(self) -> None:
        """Connect to the device; raises ``HardwareError`` if that fails."""
        pass

    @abstractmethod
    def read_voltage(self, channel: str) -> float:
        """Return the voltage on analog input ``channel``."""
        pass

    @abstractmethod
    def write_voltage(self, channel: str, value: float) -> None:
        """Set analog output ``channel`` to ``value`` volts."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Release the device; safe to call more than once."""
        pass
