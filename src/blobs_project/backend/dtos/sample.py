from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    time_s: float
    tank2_desired_cm: float
    tank2_actual_cm: float
    flow_l_min: float = 0.0
    pump_power_w: float = 0.0
    pump_voltage_v: float = 0.0
