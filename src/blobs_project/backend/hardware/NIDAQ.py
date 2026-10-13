"""NI-DAQmx implementation of ``DAQ_base``; driver failures become ``HardwareError``."""

from collections.abc import Iterator
from contextlib import contextmanager
from types import ModuleType
from typing import Any

from blobs_project import config

from .DAQ_base import DAQ_base
from .hardware_error import HardwareError

VOLTAGE_LIMIT_V = 10.0


class NIDAQ(DAQ_base):
    """NI card ``device_name``; call ``open`` first, each operation is one task."""

    def __init__(self, device_name: str = config.DAQ_DEVICE_NAME) -> None:
        """Store ``device_name``; no I/O happens until ``open``."""
        self.device_name = device_name
        self._nidaqmx: ModuleType | None = None

    def open(self) -> None:
        """Load the driver and check the device exists, else raise ``HardwareError``."""
        try:
            import nidaqmx
            import nidaqmx.system
        except ImportError as e:
            raise HardwareError("NI-DAQmx driver not available") from e
        self._nidaqmx = nidaqmx
        try:
            with self._guard("open"):
                nidaqmx.system.Device(self.device_name).product_type
        except HardwareError:
            self._nidaqmx = None
            raise

    def read_voltage(self, channel: str) -> float:
        """Return the voltage on analog input ``channel`` (RSE, +-10 V)."""
        nidaqmx, lim = self._require_open(), VOLTAGE_LIMIT_V
        rse = nidaqmx.constants.TerminalConfiguration.RSE
        with self._guard(f"read {channel}"), nidaqmx.Task() as task:
            chan = task.ai_channels.add_ai_voltage_chan
            chan(
                self._physical(channel), terminal_config=rse, min_val=-lim, max_val=lim
            )
            return float(task.read())

    def write_voltage(self, channel: str, value: float) -> None:
        """Set output ``channel`` to ``value``; ``ValueError`` outside +-10 V."""
        if not -VOLTAGE_LIMIT_V <= value <= VOLTAGE_LIMIT_V:
            raise ValueError("Voltage must be between -10 V and +10 V")
        nidaqmx, lim = self._require_open(), VOLTAGE_LIMIT_V
        with self._guard(f"write {channel}"), nidaqmx.Task() as task:
            chan = task.ao_channels.add_ao_voltage_chan
            chan(self._physical(channel), min_val=-lim, max_val=lim)
            task.write(value)

    def close(self) -> None:
        """Forget the driver handle; later operations raise until ``open``."""
        self._nidaqmx = None

    def __str__(self) -> str:
        """Return the device name for display."""
        return f"Name: {self.device_name}"

    def _physical(self, channel: str) -> str:
        """Return ``channel`` prefixed with the device name, e.g. ``Dev1/ai0``."""
        return f"{self.device_name}/{channel}"

    def _require_open(self) -> Any:
        """Return the driver module, or raise ``HardwareError`` if not open."""
        if self._nidaqmx is None:
            raise HardwareError(f"{self.device_name} is not open")
        return self._nidaqmx

    @contextmanager
    def _guard(self, action: str) -> Iterator[None]:
        """Re-raise driver and OS errors during ``action`` as ``HardwareError``."""
        assert self._nidaqmx is not None
        try:
            yield
        except (self._nidaqmx.errors.Error, OSError) as e:
            raise HardwareError(f"{action} failed on {self.device_name}: {e}") from e
