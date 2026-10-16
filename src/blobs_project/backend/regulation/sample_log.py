from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass

from blobs_project import config


@dataclass(frozen=True)
class Sample:
    time_s: float
    tank2_desired_cm: float
    tank2_actual_cm: float
    flow_l_min: float = 0.0
    pump_power_w: float = 0.0
    pump_voltage_v: float = 0.0


class SampleLog:
    def __init__(self, limit: int = config.SAMPLE_LOG_LIMIT) -> None:
        self._samples: deque[Sample] = deque(maxlen=limit)

    def append(
        self,
        time_s: float,
        tank2_desired_cm: float,
        tank2_actual_cm: float,
        flow_l_min: float = 0.0,
        pump_power_w: float = 0.0,
        pump_voltage_v: float = 0.0,
    ) -> None:
        self._samples.append(
            Sample(
                time_s,
                tank2_desired_cm,
                tank2_actual_cm,
                flow_l_min,
                pump_power_w,
                pump_voltage_v,
            )
        )

    def clear(self) -> None:
        self._samples.clear()

    def load(self, samples: Sequence[Sample]) -> None:
        """Replace the log with ``samples``, e.g. a run imported from CSV."""
        self._samples.clear()
        self._samples.extend(samples)

    def __len__(self) -> int:
        return len(self._samples)

    @property
    def samples(self) -> tuple[Sample, ...]:
        return tuple(self._samples)

    def trend_points(self) -> list[tuple[float, float]]:
        return [(sample.time_s, sample.tank2_actual_cm) for sample in self._samples]

    def desired_trend_points(self) -> list[tuple[float, float]]:
        return [(sample.time_s, sample.tank2_desired_cm) for sample in self._samples]

    def flow_trend_points(self) -> list[tuple[float, float]]:
        return [(sample.time_s, sample.flow_l_min) for sample in self._samples]

    def pump_power_trend_points(self) -> list[tuple[float, float]]:
        return [(sample.time_s, sample.pump_power_w) for sample in self._samples]
