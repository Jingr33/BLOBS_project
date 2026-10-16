"""PI level controller and its adapter for ``RegulationService``."""

import math

from blobs_project import config

from .regulation_controller_base import RegulationControllerBase


class PIController:
    """PI controller in metres and volts.

    ``Kp`` is in V/m and ``Ki`` in V/(m*s); the output stays in
    ``[min_out, max_out]`` volts.
    """

    def __init__(
        self, Kp: float, Ki: float, min_out: float = 0.0, max_out: float = 7.5
    ) -> None:
        """Store the gains ``Kp``, ``Ki`` and the output limits."""
        self.Kp = Kp
        self.Ki = Ki
        self.min_out = min_out
        self.max_out = max_out

        self.integral = 0.0
        self.last_output = 0.0

    def reset(self) -> None:
        """Deletes the internal memory of the controller."""
        self.integral = 0.0
        self.last_output = 0.0

    def compute(self, setpoint: float, measured: float, dt: float) -> float:
        """Return the pump voltage for ``setpoint`` and ``measured`` level [m]."""
        if not (math.isfinite(setpoint) and math.isfinite(measured)):
            self.last_output = self.min_out
            return self.min_out
        if dt <= 0:
            return self.last_output

        error = setpoint - measured
        P_term = self.Kp * error
        self.integral += error * dt
        I_term = self.Ki * self.integral
        output = P_term + I_term

        # Anti-windup
        if output > self.max_out:
            output = self.max_out
            if error > 0:
                self.integral -= error * dt
        elif output < self.min_out:
            output = self.min_out
            if error < 0:
                self.integral -= error * dt

        output = max(self.min_out, min(self.max_out, output))
        self.last_output = output
        return output


class PIRegulationController(RegulationControllerBase):
    """Run ``PIController`` on levels in cm and return the pump voltage."""

    def __init__(self, pi: PIController | None = None) -> None:
        """Wrap ``pi``, by default the CHR tuning from ``config``."""
        self._pi = pi or PIController(
            config.PI_KP_V_PER_M, config.PI_KI, config.PI_MIN_V, config.TOWER_PUMP_MAX_V
        )

    def reset(self) -> None:
        """Clear the integral before a new run."""
        self._pi.reset()

    def compute(self, dt_s: float, desired_cm: float, actual_cm: float) -> float:
        """Return the pump voltage for ``desired_cm`` and ``actual_cm``."""
        return self._pi.compute(desired_cm / 100.0, actual_cm / 100.0, dt_s)
