from __future__ import annotations


class Stopwatch:
    def __init__(self, sample_interval_s: float) -> None:
        self._sample_interval_s = sample_interval_s
        self._elapsed_s = 0.0
        self._marked_s = 0.0

    @property
    def elapsed_s(self) -> float:
        return self._elapsed_s

    @property
    def seconds_since_mark(self) -> float:
        return self._elapsed_s - self._marked_s

    @property
    def sample_due(self) -> bool:
        return self.seconds_since_mark >= self._sample_interval_s

    def advance(self, dt_s: float) -> None:
        self._elapsed_s += dt_s

    def mark(self) -> None:
        self._marked_s = self._elapsed_s

    def start(self) -> None:
        self._elapsed_s = 0.0
        self._marked_s = 0.0
