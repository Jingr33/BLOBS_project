import numpy as np
from scipy.linalg import solve_discrete_are
 
def solve_kalman_gain(Ad: np.ndarray, Cd: np.ndarray, Q_kf: np.ndarray, R_kf: np.ndarray) -> np.ndarray:
    P = solve_discrete_are(Ad.T, Cd.T, Q_kf, R_kf)
    S = Cd @ P @ Cd.T + R_kf
    return P @ Cd.T @ np.linalg.inv(S)
 
class KalmanFilter:
    def __init__(self, Ad, Bd, Cd, Q_kf, R_kf, x_eq, u_eq):
        self.Ad, self.Bd, self.Cd = Ad, Bd, Cd
        self.Q_kf, self.R_kf = Q_kf, R_kf
        self.n = Ad.shape[0]
        self.x_eq = np.asarray(x_eq, dtype=float).reshape(self.n, 1)
        self.u_eq = u_eq
        self.y_eq = (Cd @ self.x_eq).item()
 
        self.dx_hat = np.zeros((self.n, 1))
        # P = how uncertain the current state estimate is believed to be.
        # Starts deliberately oversized (relative to Q_kf, which is ~1e-8),
        # so the filter trusts the first few measurements strongly and
        # quickly corrects a cold-start guess that may be far from the
        # truth. It shrinks over the first ~50-100 steps as confidence grows.
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
        du = u_prev - self.u_eq
        dy = y_meas - self.y_eq
 
        # Predict: propagate the estimate and its uncertainty one step
        # forward using the linear model.
        dx_pred = self.Ad @ self.dx_hat + self.Bd * du
        P_pred = self.Ad @ self.P @ self.Ad.T + self.Q_kf
 
        # Correct: compare the model's predicted measurement against the
        # real one, and pull the estimate toward the measurement by an
        # amount set by the Kalman gain L (how much to trust the
        # measurement versus the model's own prediction).
        S = self.Cd @ P_pred @ self.Cd.T + self.R_kf
        L = P_pred @ self.Cd.T @ np.linalg.inv(S)
 
        innovation = dy - (self.Cd @ dx_pred).item()
        self.dx_hat = dx_pred + L * innovation
        self.P = (np.eye(self.n) - L @ self.Cd) @ P_pred
 
        return self.x_hat