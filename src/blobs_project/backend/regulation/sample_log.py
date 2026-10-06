from __future__ import annotations

from dataclasses import dataclass

from ... import configuration as config


@dataclass(frozen=True)
class Sample:
    time_s: float
    tank2_desired_cm: float
    tank2_actual_cm: float


class SampleLog:
    def __init__(self, limit: int = config.SAMPLE_LOG_LIMIT) -> None:
        self._limit = limit
        self._samples: list[Sample] = []

    def append(
        self,
        time_s: float,
        tank2_desired_cm: float,
        tank2_actual_cm: float,
    ) -> None:
        self._samples.append(Sample(time_s, tank2_desired_cm, tank2_actual_cm))
        if len(self._samples) > self._limit:
            del self._samples[0]

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
