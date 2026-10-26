"""Median filtering of level sensor readings."""

import math
from collections import deque


class LevelFilter:
    """Median over the last ``size`` valid samples; invalid samples pass through."""

    def __init__(self, size: int) -> None:
        """Keep up to ``size`` samples."""
        self._samples: deque[float] = deque(maxlen=size)

    def clear(self) -> None:
        """Forget all samples before a new run."""
        self._samples.clear()

    def __call__(self, value: float) -> float:
        """Add ``value`` and return the median, or NaN if ``value`` is not finite."""
        if not math.isfinite(value):
            return math.nan
        self._samples.append(value)
        ordered = sorted(self._samples)
        return ordered[len(ordered) // 2]
