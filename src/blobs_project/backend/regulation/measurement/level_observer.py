"""Short-term projection of the measured lower-tank level."""

import math
from collections import deque


class LevelObserver:
    """Estimate the rising level trend and project it over a short horizon."""

    def __init__(self, size: int) -> None:
        self._samples: deque[tuple[float, float]] = deque(maxlen=size)
        self._elapsed_s = 0.0

    def clear(self) -> None:
        self._samples.clear()
        self._elapsed_s = 0.0

    def observe(self, level_cm: float, dt_s: float) -> None:
        if not math.isfinite(level_cm) or not math.isfinite(dt_s) or dt_s <= 0:
            self.clear()
            return
        self._elapsed_s += dt_s
        self._samples.append((self._elapsed_s, level_cm))

    def predict(self, horizon_s: float) -> float | None:
        if len(self._samples) < 3:
            return None
        mean_t = sum(t for t, _ in self._samples) / len(self._samples)
        mean_level = sum(level for _, level in self._samples) / len(self._samples)
        variance = sum((t - mean_t) ** 2 for t, _ in self._samples)
        if variance <= 0:
            return self._samples[-1][1]
        slope = (
            sum((t - mean_t) * (level - mean_level) for t, level in self._samples)
            / variance
        )
        return self._samples[-1][1] + max(0.0, slope) * max(0.0, horizon_s)
