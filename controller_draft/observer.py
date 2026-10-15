import numpy as np
from scipy.linalg import solve_discrete_are
 
def solve_kalman_gain(Ad: np.ndarray, Cd: np.ndarray, Q_kf: np.ndarray, R_kf: np.ndarray) -> np.ndarray:
    P = solve_discrete_are(Ad.T, Cd.T, Q_kf, R_kf)
    S = Cd @ P @ Cd.T + R_kf
    return P @ Cd.T @ np.linalg.inv(S)
 
class KalmanFilter:
    def __init__(self, Ad, Bd, Cd, Q_kf, R_kf, x_eq, u_eq):
        """
        Args:
            Ad, Bd, Cd: discrete state-space matrices (see
                mpc_model.get_discrete_model).
            Q_kf: process noise covariance (model uncertainty), shape (n, n).
            R_kf: measurement noise covariance, shape (1, 1).
            x_eq: equilibrium state (the same point Ad/Bd/Cd are linearized
                around), length n.
            u_eq: equilibrium voltage [V] corresponding to x_eq.

        `P` (state covariance) starts deliberately oversized relative to
        Q_kf (~1e-8), so the filter trusts the first few measurements
        strongly and quickly corrects a cold-start guess. It shrinks over the
        first 50-100 steps as confidence grows.
        """
        self.Ad, self.Bd, self.Cd = Ad, Bd, Cd
        self.Q_kf, self.R_kf = Q_kf, R_kf
        self.n = Ad.shape[0]
        self.x_eq = np.asarray(x_eq, dtype=float).reshape(self.n, 1)
        self.u_eq = u_eq
        self.y_eq = (Cd @ self.x_eq).item()
 
        self.dx_hat = np.zeros((self.n, 1))
        self.P = np.eye(self.n) * 1.0
 
    @property
    def x_hat(self) -> np.ndarray:
        full = (self.x_eq + self.dx_hat).flatten()
        n_phys = min(2, full.shape[0])
        full[:n_phys] = np.maximum(full[:n_phys], 0.0)
        return full
 
    def set_target(self, Ad, Bd, Cd, x_eq, u_eq):
        x_abs = self.x_eq + self.dx_hat
        self.Ad, self.Bd, self.Cd = Ad, Bd, Cd
        self.x_eq = np.asarray(x_eq, dtype=float).reshape(self.n, 1)
        self.u_eq = u_eq
        self.y_eq = (Cd @ self.x_eq).item()
        self.dx_hat = x_abs - self.x_eq
        # self.P (covariance) is left as-is - still a reasonable uncertainty
        # estimate for the new operating point.
 
    def update(self, u_prev: float, y_meas: float) -> np.ndarray:
        """One filter step: predict from the model, then correct from the measurement.

        Predict propagates the estimate and its uncertainty one step forward
        using the linear model. Correct compares the model's predicted
        measurement against the real one, and pulls the estimate toward the
        measurement by an amount set by the Kalman gain L.
        """
        du = u_prev - self.u_eq
        dy = y_meas - self.y_eq
       
        # Predict
        dx_pred = self.Ad @ self.dx_hat + self.Bd * du
        P_pred = self.Ad @ self.P @ self.Ad.T + self.Q_kf
 
        # Correct
        S = self.Cd @ P_pred @ self.Cd.T + self.R_kf
        L = P_pred @ self.Cd.T @ np.linalg.inv(S)
 
        innovation = dy - (self.Cd @ dx_pred).item()
        self.dx_hat = dx_pred + L * innovation
        self.P = (np.eye(self.n) - L @ self.Cd) @ P_pred
 
        return self.x_hat
