from __future__ import annotations

from dataclasses import dataclass

from blobs_project.config import (
    TANK_ACTUAL_LEVEL_CM,
    TANK_DESIRED_LEVEL_CM,
    TANK_LEVEL_MAX_CM,
)


@dataclass
class RegulationValues:
    _tank2_actual_cm: float
    _tank2_desired_cm: float
    _flow_l_min: float
    _pump_power_w: float
    _total_energy_wh: float = 0.0
    _pump_voltage_v: float = 0.0

    @property
    def tank2_actual_cm(self) -> float:
        return self._tank2_actual_cm

    @tank2_actual_cm.setter
    def tank2_actual_cm(self, value: float) -> None:
        self._tank2_actual_cm = self._clamp(value)

    @property
    def tank2_desired_cm(self) -> float:
        return self._tank2_desired_cm

    @tank2_desired_cm.setter
    def tank2_desired_cm(self, value: float) -> None:
        self._tank2_desired_cm = self._clamp(value)

    @property
    def flow_l_min(self) -> float:
        return self._flow_l_min

    @flow_l_min.setter
    def flow_l_min(self, value: float) -> None:
        self._flow_l_min = value

    @property
    def pump_power_w(self) -> float:
        return self._pump_power_w

    @pump_power_w.setter
    def pump_power_w(self, value: float) -> None:
        self._pump_power_w = value

    @property
    def pump_voltage_v(self) -> float:
        return self._pump_voltage_v

    @pump_voltage_v.setter
    def pump_voltage_v(self, value: float) -> None:
        self._pump_voltage_v = value

    @property
    def total_energy_wh(self) -> float:
        return self._total_energy_wh

    @total_energy_wh.setter
    def total_energy_wh(self, value: float) -> None:
        self._total_energy_wh = max(0.0, value)

    @classmethod
    def default(cls) -> RegulationValues:
        return cls(TANK_ACTUAL_LEVEL_CM, TANK_DESIRED_LEVEL_CM, 0.0, 0.0)

    def reset_flow(self) -> None:
        self._flow_l_min = 0.0

    def reset_pump(self) -> None:
        self._pump_power_w = 0.0
        self._pump_voltage_v = 0.0

    def reset_energy(self) -> None:
        self._total_energy_wh = 0.0

    @staticmethod
    def _clamp(value_cm: float) -> float:
        return max(0.0, min(TANK_LEVEL_MAX_CM, value_cm))
