"""The one exception the hardware layer raises for expected failures."""


class HardwareError(Exception):
    """A DAQ or tower failure (driver, device, read or write) the app can handle."""
