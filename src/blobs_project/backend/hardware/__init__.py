from .DAQ_base import DAQ_base
from .MockDAQ import MockDAQ

__all__ = ["DAQ_base", "NIDAQ", "MockDAQ"]


def __getattr__(name: str) -> object:
    if name == "NIDAQ":
        from .NIDAQ import NIDAQ

        return NIDAQ
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
