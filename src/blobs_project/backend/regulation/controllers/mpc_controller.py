"""Model-predictive level controller and adapter for the regulation service."""

import math
import warnings

import casadi
import numpy as np
from numpy.typing import NDArray

from blobs_project import config

from .mpc_model import PlantParams, get_discrete_model
from .observer import KalmanFilter
from .regulation_controller_base import ControllerError, RegulationControllerBase

FloatArray = NDArray[np.float64]


class MPCController:
    """Finite-horizon linear MPC with pump-voltage and slew constraints."""

    def __init__(
        self,
        params: PlantParams,
        target_h_L_m: float,
        sample_period_s: float,
        horizon: int = config.MPC_HORIZON_STEPS,
        move_weight: float = config.MPC_MOVE_WEIGHT,
        integral_gain: float = config.MPC_INTEGRAL_GAIN,
        integral_limit_m_s: float = config.MPC_INTEGRAL_LIMIT_M_S,
        rate_limit_v_s: float = config.MPC_RATE_LIMIT_V_S,
    ) -> None:
        if horizon < 1:
            raise ValueError("MPC horizon must be positive")
        if not math.isfinite(move_weight) or move_weight < 0:
            raise ValueError("MPC move weight must be finite and non-negative")
        if not math.isfinite(integral_gain) or integral_gain < 0:
            raise ValueError("MPC integral gain must be finite and non-negative")
        if not math.isfinite(integral_limit_m_s) or integral_limit_m_s <= 0:
            raise ValueError("MPC integral limit must be finite and positive")
        if not math.isfinite(rate_limit_v_s) or rate_limit_v_s <= 0:
            raise ValueError("MPC slew limit must be finite and positive")
        self.params = params
        self.target_h_L_m = target_h_L_m
        self.sample_period_s = sample_period_s
        self.horizon = horizon
        self.move_weight = move_weight
        self.integral_gain = integral_gain
        self.integral_limit_m_s = integral_limit_m_s
        self.rate_limit_v_s = rate_limit_v_s
        self.integral_error_m_s = 0.0
        model = get_discrete_model(params, target_h_L_m, sample_period_s)
        self.Ad, self.Bd, self.Cd = model.Ad, model.Bd, model.Cd
        self.h_H_eq, self.u_eq = model.h_H_eq_m, model.u_eq_v
        self._build_optimizer()

    def _build_optimizer(self) -> None:
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message="The (ONNX|opcua|approximateMPC) feature .*",
                    category=UserWarning,
                )
                import do_mpc

            self.model = do_mpc.model.Model("discrete")
            self.h_H = self.model.set_variable(var_type="_x", var_name="h_H")
            self.h_L = self.model.set_variable(var_type="_x", var_name="h_L")
            self.u = self.model.set_variable(var_type="_x", var_name="u")
            self.e_int = self.model.set_variable(var_type="_x", var_name="e_int")
            self.du = self.model.set_variable(var_type="_u", var_name="du")

            dh_H = self.h_H - self.h_H_eq
            dh_L = self.h_L - self.target_h_L_m
            u_next = self.u + self.du * self.sample_period_s
            du_val = u_next - self.u_eq
            a11, a12 = float(self.Ad[0, 0]), float(self.Ad[0, 1])
            a21, a22 = float(self.Ad[1, 0]), float(self.Ad[1, 1])
            b1, b2 = float(self.Bd[0, 0]), float(self.Bd[1, 0])
            dh_H_next = a11 * dh_H + a12 * dh_L + b1 * du_val
            dh_L_next = a21 * dh_H + a22 * dh_L + b2 * du_val
            self.model.set_rhs("h_H", self.h_H_eq + dh_H_next)
            self.model.set_rhs("h_L", self.target_h_L_m + dh_L_next)
            self.model.set_rhs("u", u_next)
            integral_next = (
                self.e_int + (self.h_L - self.target_h_L_m) * self.sample_period_s
            )
            self.model.set_rhs(
                "e_int",
                casadi.fmin(
                    casadi.fmax(integral_next, -self.integral_limit_m_s),
                    self.integral_limit_m_s,
                ),
            )
            self.model.setup()

            self.mpc = do_mpc.controller.MPC(self.model)
            self.mpc.set_param(
                n_horizon=self.horizon,
                t_step=self.sample_period_s,
                store_full_solution=False,
                nlpsol_opts={
                    "ipopt.print_level": 0,
                    "ipopt.max_iter": 80,
                    "ipopt.tol": 1e-6,
                    "print_time": 0,
                    "ipopt.sb": "yes",
                },
            )
            error = self.h_L + self.integral_gain * self.e_int - self.target_h_L_m
            self.mpc.set_objective(
                mterm=3.0 * error**2,
                lterm=error**2 + self.move_weight * self.du**2,
            )
            self.mpc.set_rterm(du=self.move_weight * 0.01)
            self.mpc.bounds["lower", "_x", "u"] = self.params.u_min
            self.mpc.bounds["upper", "_x", "u"] = self.params.u_max
            self.mpc.bounds["lower", "_x", "h_H"] = 0.0
            self.mpc.bounds["upper", "_x", "h_H"] = self.params.H
            self.mpc.bounds["lower", "_x", "h_L"] = 0.0
            self.mpc.bounds["upper", "_x", "h_L"] = config.LEVEL_TRIP_CM / 100.0
            self.mpc.bounds["lower", "_u", "du"] = -self.rate_limit_v_s
            self.mpc.bounds["upper", "_u", "du"] = self.rate_limit_v_s
            self.mpc.setup()
            self.mpc.set_initial_guess()
            self._initialized = False
        except Exception as error:
            raise ControllerError(
                f"could not initialize MPC solver: {error}"
            ) from error

    def step(
        self,
        h_H_hat_m: float,
        h_L_meas_m: float,
        u_prev_v: float,
        dt_s: float,
    ) -> float:
        """Return a bounded pump voltage from the estimated/measured state."""
        if not all(
            math.isfinite(value) for value in (h_H_hat_m, h_L_meas_m, u_prev_v, dt_s)
        ):
            raise ValueError("MPC inputs must be finite")
        if dt_s <= 0:
            raise ValueError("MPC sample period must be positive")
        if not (
            self.params.u_min <= u_prev_v <= self.params.u_max
            and 0 <= h_H_hat_m <= self.params.H
            and 0 <= h_L_meas_m <= self.params.H
        ):
            raise ValueError("MPC state is outside the model limits")

        error_m = h_L_meas_m - self.target_h_L_m
        at_max = u_prev_v >= self.params.u_max - 1e-6
        at_min = u_prev_v <= self.params.u_min + 1e-6
        if not ((at_max and error_m < 0.0) or (at_min and error_m > 0.0)):
            self.integral_error_m_s = min(
                max(
                    self.integral_error_m_s + error_m * dt_s,
                    -self.integral_limit_m_s,
                ),
                self.integral_limit_m_s,
            )

        x0 = np.asarray(
            [h_H_hat_m, h_L_meas_m, u_prev_v, self.integral_error_m_s],
            dtype=float,
        ).reshape(-1, 1)
        self.mpc.x0 = x0
        try:
            if not self._initialized:
                self.mpc.set_initial_guess()
                self._initialized = True
            du_cmd = float(np.asarray(self.mpc.make_step(x0)).squeeze())
        except Exception as error:
            raise ControllerError(f"MPC optimization failed: {error}") from error
        if not math.isfinite(du_cmd):
            raise ControllerError("MPC returned a non-finite pump adjustment")

        max_step = self.rate_limit_v_s * dt_s
        delta_v = min(max(du_cmd * dt_s, -max_step), max_step)
        return float(min(max(u_prev_v + delta_v, self.params.u_min), self.params.u_max))


class MPCRegulationController(RegulationControllerBase):
    """Estimate the unmeasured upper tank and run the two-tank MPC."""

    def __init__(self, params: PlantParams | None = None) -> None:
        self._params = params or PlantParams()
        self._mpc: MPCController | None = None
        self._observer: KalmanFilter | None = None
        self._target_h_L_m: float | None = None
        self._last_output_v = 0.0

    def reset(self) -> None:
        """Forget previous-run estimator, optimizer and actuator state."""
        self._mpc = None
        self._observer = None
        self._target_h_L_m = None
        self._last_output_v = 0.0

    @property
    def output_limits_v(self) -> tuple[float, float]:
        """Return the MPC's pump-voltage bounds."""
        return self._params.u_min, self._params.u_max

    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        """Estimate the hidden state and return a pump command in volts."""
        if not all(math.isfinite(value) for value in (dt_s, desired_cm, actual_cm)):
            raise ValueError("controller inputs must be finite")
        if dt_s <= 0:
            raise ValueError("controller sample period must be positive")
        target_m, measured_m = desired_cm / 100.0, actual_cm / 100.0
        if not 0 < target_m < self._params.H:
            raise ValueError("setpoint must be inside the modeled tank capacity")
        if not 0 <= measured_m <= config.LEVEL_TRIP_CM / 100.0:
            raise ValueError("measured level is outside the MPC operating range")

        try:
            if self._mpc is None or target_m != self._target_h_L_m:
                self._configure(target_m)
            if self._observer is None or self._mpc is None:
                raise ControllerError("MPC controller was not initialized")
            state = self._observer.update(self._last_output_v, measured_m)
            output = self._mpc.step(
                float(state[0]), measured_m, self._last_output_v, dt_s
            )
        except ControllerError:
            raise
        except Exception as error:
            raise ControllerError(f"MPC controller update failed: {error}") from error
        self._last_output_v = output
        return output

    def _configure(self, target_h_L_m: float) -> None:
        model = get_discrete_model(self._params, target_h_L_m, config.CONTROL_PERIOD_S)
        equilibrium = np.asarray([[model.h_H_eq_m], [target_h_L_m]], dtype=float)
        if self._observer is None:
            self._observer = KalmanFilter(
                model.Ad,
                model.Bd,
                model.Cd,
                np.diag([config.MPC_PROCESS_NOISE_VARIANCE_M2] * 2),
                np.asarray([[config.MPC_SENSOR_NOISE_VARIANCE_M2]], dtype=float),
                equilibrium,
                model.u_eq_v,
                self._params.H,
            )
        else:
            self._observer.set_model(
                model.Ad, model.Bd, model.Cd, equilibrium, model.u_eq_v
            )
        self._mpc = MPCController(
            self._params,
            target_h_L_m,
            config.CONTROL_PERIOD_S,
        )
        self._target_h_L_m = target_h_L_m
