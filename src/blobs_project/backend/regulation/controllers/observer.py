"""Kalman state observer for the unmeasured upper-tank level."""

import math

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import solve_discrete_are

FloatArray = NDArray[np.float64]


def solve_kalman_gain(
    Ad: FloatArray, Cd: FloatArray, Q_kf: FloatArray, R_kf: FloatArray
) -> FloatArray:
    """Return the steady-state discrete Kalman gain for a linear system."""
    covariance = solve_discrete_are(Ad.T, Cd.T, Q_kf, R_kf)
    innovation_covariance = Cd @ covariance @ Cd.T + R_kf
    return np.linalg.solve(innovation_covariance.T, (covariance @ Cd.T).T).T


class KalmanFilter:
    """Estimate both tank levels from pump voltage and lower-level readings."""

    def __init__(
        self,
        Ad: FloatArray,
        Bd: FloatArray,
        Cd: FloatArray,
        Q_kf: FloatArray,
        R_kf: FloatArray,
        x_eq: FloatArray,
        u_eq: float,
        state_max_m: float,
    ) -> None:
        self.Q_kf = np.asarray(Q_kf, dtype=float)
        self.R_kf = np.asarray(R_kf, dtype=float)
        if self.Q_kf.shape != (2, 2) or self.R_kf.shape != (1, 1):
            raise ValueError("observer covariance matrices have invalid dimensions")
        if not (
            np.isfinite(self.Q_kf).all()
            and np.isfinite(self.R_kf).all()
            and np.linalg.eigvalsh(self.Q_kf).min() >= 0
            and self.R_kf[0, 0] > 0
        ):
            raise ValueError("observer covariances must be finite and positive")
        self.Ad: FloatArray
        self.Bd: FloatArray
        self.Cd: FloatArray
        self.x_eq: FloatArray
        self.dx_hat: FloatArray
        self.u_eq: float
        self.y_eq: float
        if not math.isfinite(state_max_m) or state_max_m <= 0:
            raise ValueError("observer state limit must be finite and positive")
        self._state_max_m = state_max_m
        self.P = np.eye(2, dtype=float) * 0.01
        self.set_model(Ad, Bd, Cd, x_eq, u_eq, initialize=True)

    @property
    def x_hat(self) -> FloatArray:
        """Return estimated absolute tank heights [m] inside tank limits."""
        state = (self.x_eq + self.dx_hat).flatten()
        state[:2] = np.clip(state[:2], 0.0, self._state_max_m)
        return state

    def set_model(
        self,
        Ad: FloatArray,
        Bd: FloatArray,
        Cd: FloatArray,
        x_eq: FloatArray,
        u_eq: float,
        *,
        initialize: bool = False,
    ) -> None:
        """Update the operating point while preserving the absolute estimate."""
        A = np.asarray(Ad, dtype=float)
        B = np.asarray(Bd, dtype=float)
        C = np.asarray(Cd, dtype=float)
        equilibrium = np.asarray(x_eq, dtype=float).reshape(2, 1)
        if A.shape != (2, 2) or B.shape != (2, 1) or C.shape != (1, 2):
            raise ValueError("observer matrices must have 2-state, 1-input shapes")
        if not all(np.isfinite(value).all() for value in (A, B, C, equilibrium)):
            raise ValueError("observer model must contain only finite values")
        if not math.isfinite(u_eq):
            raise ValueError("equilibrium pump voltage must be finite")
        previous = equilibrium if initialize else self.x_eq + self.dx_hat
        self.Ad, self.Bd, self.Cd = A, B, C
        self.x_eq = equilibrium
        self.u_eq = u_eq
        self.y_eq = float((C @ equilibrium).item())
        self.dx_hat = previous - equilibrium
        if initialize:
            self.P = np.eye(2, dtype=float) * 0.01

    def reset(self) -> None:
        """Reset the estimate to its current operating point."""
        self.dx_hat = np.zeros((2, 1), dtype=float)
        self.P = np.eye(2, dtype=float) * 0.01

    def update(self, u_prev: float, y_meas: float) -> FloatArray:
        """Correct the state estimate using the latest pump and level readings."""
        if not (math.isfinite(u_prev) and math.isfinite(y_meas)):
            raise ValueError("observer inputs must be finite")

        input_deviation = u_prev - self.u_eq
        measurement_deviation = y_meas - self.y_eq
        dx_pred = self.Ad @ self.dx_hat + self.Bd * input_deviation
        P_pred = self.Ad @ self.P @ self.Ad.T + self.Q_kf
        innovation_covariance = self.Cd @ P_pred @ self.Cd.T + self.R_kf
        gain = np.linalg.solve(innovation_covariance.T, (P_pred @ self.Cd.T).T).T
        innovation = measurement_deviation - float((self.Cd @ dx_pred).item())
        self.dx_hat = dx_pred + gain * innovation
        residual = np.eye(2, dtype=float) - gain @ self.Cd
        self.P = residual @ P_pred @ residual.T + gain @ self.R_kf @ gain.T
        return self.x_hat
