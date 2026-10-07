from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from blobs_project import config


@dataclass(frozen=True)
class Sample:
    time_s: float
    tank2_desired_cm: float
    tank2_actual_cm: float


class SampleLog:
    def __init__(self, limit: int = config.SAMPLE_LOG_LIMIT) -> None:
        self._samples: deque[Sample] = deque(maxlen=limit)

    def append(
        self,
        time_s: float,
        tank2_desired_cm: float,
        tank2_actual_cm: float,
    ) -> None:
        self._samples.append(Sample(time_s, tank2_desired_cm, tank2_actual_cm))

    def clear(self) -> None:
        self._samples.clear()

    def __len__(self) -> int:
        return len(self._samples)

    @property
    def samples(self) -> tuple[Sample, ...]:
        return tuple(self._samples)

    def trend_points(self) -> list[tuple[float, float]]:
        return [(sample.time_s, sample.tank2_actual_cm) for sample in self._samples]

    def desired_trend_points(self) -> list[tuple[float, float]]:
        return [(sample.time_s, sample.tank2_desired_cm) for sample in self._samples]
