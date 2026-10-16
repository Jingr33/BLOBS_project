import numpy as np
from scipy.signal import cont2discrete
from dataclasses import dataclass
 
g = 9.81

@dataclass
class PlantParams:
    S: float = np.pi * 0.05 ** 2 / 4.0   # tank cross-section [m^2]
    H: float = 0.28                      # tank height [m] - overflows above this
    k_sensor: float = 100.0 / 3.06       # sensor conversion, volts to cm
 
    u_min: float = 2.0        # V
    u_max: float = 10         # V   #10 V for faster regulation
 
    # identified parameters (Vlada, 7. 10. 2026)
    c_H: float = 1.47327e-05   # outflow coefficient, upper tank
    c_L: float = 1.11327e-05   # outflow coefficient, lower tank
    r_pump: float = 1.06558e-05   # gain of the pump's power-law characteristic
    s_pump: float = 0.455031      # exponent of the power-law characteristic
    u0_pump: float = 1.56         # voltage above which the pump starts delivering water
 
 
def outflow(h: float, c: float) -> float:
    return c * np.sqrt(2.0 * g * max(h, 0.0))
 
 
def pump_voltage_from_flow(Q: float, p: PlantParams) -> float:
    
    if Q <= 0.0:
        return p.u0_pump
    return p.u0_pump + (Q / p.r_pump) ** (1.0 / p.s_pump)
 
 
def get_discrete_model(p: PlantParams, target_h_L: float, Ts: float):
    target_h_L = max(target_h_L, 1e-4) 
    Q_eq = outflow(target_h_L, p.c_L)
    h_H_eq = (Q_eq / p.c_H) ** 2 / (2.0 * g)
    u_eq = pump_voltage_from_flow(Q_eq, p)
 
    sqrt2g = np.sqrt(2.0 * g)
    a11 = -p.c_H * sqrt2g / (2.0 * p.S * np.sqrt(h_H_eq))
    a21 = p.c_H * sqrt2g / (2.0 * p.S * np.sqrt(h_H_eq))
    a22 = -p.c_L * sqrt2g / (2.0 * p.S * np.sqrt(target_h_L))
 
    # derivative of pump flow (needed for Bd, since the pump characteristic is nonlinear)
    du_eq = max(u_eq - p.u0_pump, 1e-4)
    dq_du = p.r_pump * p.s_pump * (du_eq ** (p.s_pump - 1.0))
 
    A = np.array([[a11, 0.0], [a21, a22]])
    B = np.array([[dq_du / p.S], [0.0]])
    C = np.array([[0.0, p.k_sensor]])
    D = np.array([[0.0]])
 
    Ad, Bd, Cd, _, _ = cont2discrete((A, B, C, D), Ts, method="zoh")
    return Ad, Bd, Cd, h_H_eq, u_eq
