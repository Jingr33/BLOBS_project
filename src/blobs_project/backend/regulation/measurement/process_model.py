from __future__ import annotations

import math

from blobs_project import config


class ProcessModel:
    """Estimates of quantities the tower does not measure."""

    @staticmethod
    def pump_power_w(u: float) -> float:
        """Return the estimated pump power [W] at control voltage ``u``."""
        (i0, i1), (v0, v1) = config.PUMP_CURRENT_A, config.PUMP_VOLTAGE_V
        return (v0 + v1 * u) * (i0 + i1 * u)

    @staticmethod
    def lower_outflow_l_min(level_cm: float) -> float:
        """Return the lower-tank outflow [l/min]; in steady state it is the inflow."""
        h_m = max(level_cm, 0.0) / 100.0
        q_m3_s = config.LOWER_OUTFLOW_COEFF_M2 * math.sqrt(
            2.0 * config.GRAVITY_M_S2 * h_m
        )
        return q_m3_s * 60000.0
