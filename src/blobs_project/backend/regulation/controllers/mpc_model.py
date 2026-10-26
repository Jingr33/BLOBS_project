"""Linearized two-tank plant model used by the predictive controller."""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.signal import cont2discrete

from blobs_project import config

FloatArray = NDArray[np.float64]
GRAVITY_M_S2 = 9.81


@dataclass(frozen=True)
class PlantParams:
    """Identified two-tank plant parameters in SI units."""

    S: float = math.pi * 0.05**2 / 4.0
    H: float = 0.28
    c_H: float = 1.47327e-05
    c_L: float = 1.11327e-05
    r_pump: float = 1.06558e-05
    s_pump: float = 0.455031
    u0_pump: float = 1.56
    u_min: float = 0.0
    u_max: float = config.TOWER_PUMP_MAX_V

    def __post_init__(self) -> None:
        values = (
            self.S,
            self.H,
            self.c_H,
            self.c_L,
            self.r_pump,
            self.s_pump,
            self.u0_pump,
            self.u_min,
            self.u_max,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("plant parameters must be finite")
        if min(self.S, self.H, self.c_H, self.c_L, self.r_pump, self.s_pump) <= 0:
            raise ValueError("plant geometry and coefficients must be positive")
        if not 0 <= self.u_min < self.u_max <= config.TOWER_PUMP_MAX_V:
            raise ValueError("plant pump limits are outside the approved range")


@dataclass(frozen=True)
class DiscretePlantModel:
    """Discrete plant matrices and equilibrium values in SI units."""

    Ad: FloatArray
    Bd: FloatArray
    Cd: FloatArray
    h_H_eq_m: float
    u_eq_v: float


def outflow(level_m: float, coefficient: float) -> float:
    """Return tank outflow [m^3/s] at level ``level_m``."""
    return coefficient * math.sqrt(2.0 * GRAVITY_M_S2 * max(level_m, 0.0))


def pump_voltage_from_flow(flow_m3_s: float, params: PlantParams) -> float:
    """Return the identified steady-state pump voltage for ``flow_m3_s``."""
    if flow_m3_s <= 0:
        return params.u0_pump
    return params.u0_pump + (flow_m3_s / params.r_pump) ** (1.0 / params.s_pump)


def get_discrete_model(
    params: PlantParams, target_h_L_m: float, sample_period_s: float
) -> DiscretePlantModel:
    """Linearize and discretize the cascade about a lower-tank target level.

    The measured output is lower-tank height in metres. The returned matrices
    model state deviations around the steady-state operating point.
    """
    if not math.isfinite(target_h_L_m) or not 0 < target_h_L_m < params.H:
        raise ValueError("target level must be finite and inside tank capacity")
    if not math.isfinite(sample_period_s) or sample_period_s <= 0:
        raise ValueError("sample period must be finite and positive")

    q_eq = outflow(target_h_L_m, params.c_L)
    h_H_eq = (q_eq / params.c_H) ** 2 / (2.0 * GRAVITY_M_S2)
    u_eq = pump_voltage_from_flow(q_eq, params)
    if not 0 <= u_eq <= params.u_max or not 0 < h_H_eq < params.H:
        raise ValueError("target has no feasible steady state within plant limits")

    sqrt_2g = math.sqrt(2.0 * GRAVITY_M_S2)
    a11 = -params.c_H * sqrt_2g / (2.0 * params.S * math.sqrt(h_H_eq))
    a21 = params.c_H * sqrt_2g / (2.0 * params.S * math.sqrt(h_H_eq))
    a22 = -params.c_L * sqrt_2g / (2.0 * params.S * math.sqrt(target_h_L_m))

    delta_u_eq = max(u_eq - params.u0_pump, 1e-4)
    dq_du = params.r_pump * params.s_pump * delta_u_eq ** (params.s_pump - 1.0)
    A = np.asarray([[a11, 0.0], [a21, a22]], dtype=float)
    B = np.asarray([[dq_du / params.S], [0.0]], dtype=float)
    C = np.asarray([[0.0, 1.0]], dtype=float)
    D = np.zeros((1, 1), dtype=float)
    Ad, Bd, Cd, _, _ = cont2discrete((A, B, C, D), sample_period_s, method="zoh")
    return DiscretePlantModel(
        Ad=np.asarray(Ad, dtype=float),
        Bd=np.asarray(Bd, dtype=float),
        Cd=np.asarray(Cd, dtype=float),
        h_H_eq_m=h_H_eq,
        u_eq_v=u_eq,
    )
