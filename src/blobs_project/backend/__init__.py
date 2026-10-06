from .hardware import DAQ_base, MockDAQ

__all__ = ["DAQ_base", "MockDAQ", "NIDAQ"]


def __getattr__(name: str) -> object:
    if name == "NIDAQ":
        from .hardware import NIDAQ

        return NIDAQ
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
