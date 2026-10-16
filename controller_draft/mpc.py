import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
 
import numpy as np
import do_mpc
from controller_draft.mpc_model import PlantParams, get_discrete_model
 
 
class MPCController: 
    def __init__(self, p: PlantParams, target_h_L: float, Ts: float, N: int = 50,
                 R: float = 0.1, Ki: float = 0.010):
        self.p = p
        self.Ts = Ts
        self.N, self.R, self.Ki = N, R, Ki   # stored for set_target() below
        self.target_h_L = target_h_L
        self.e_int_val = 0.0  # memory for the tracking-error integrator
 
        Ad, Bd, Cd, h_H_eq, u_eq = get_discrete_model(p, target_h_L, Ts)
 
        self.model = do_mpc.model.Model('discrete')
        self.h_H = self.model.set_variable(var_type='_x', var_name='h_H')
        self.h_L = self.model.set_variable(var_type='_x', var_name='h_L')
        self.u   = self.model.set_variable(var_type='_x', var_name='u')
        self.e_int = self.model.set_variable(var_type='_x', var_name='e_int')
        self.du  = self.model.set_variable(var_type='_u', var_name='du')
 
        # x[k+1] = A x[k] + B u[k], in deviations from the operating point
        dh_H = self.h_H - h_H_eq
        dh_L = self.h_L - target_h_L
        u_next = self.u + self.du * Ts
        du_val = u_next - u_eq
 
        dh_H_next = Ad[0, 0] * dh_H + Ad[0, 1] * dh_L + Bd[0, 0] * du_val
        dh_L_next = Ad[1, 0] * dh_H + Ad[1, 1] * dh_L + Bd[1, 0] * du_val
 
        self.model.set_rhs('h_H', h_H_eq + dh_H_next)
        self.model.set_rhs('h_L', target_h_L + dh_L_next)
        self.model.set_rhs('u', u_next)
        self.model.set_rhs('e_int', self.e_int + (self.h_L - target_h_L) * Ts)
        self.model.setup()
 
        self.mpc = do_mpc.controller.MPC(self.model)
        self.mpc.set_param(n_horizon=N, t_step=Ts, store_full_solution=False,
                            nlpsol_opts={'ipopt.print_level': 0, 'print_time': 0, 'ipopt.sb': 'yes'})
 
        err = self.h_L + Ki * self.e_int - target_h_L
        mterm = 3 * err ** 2   # terminal state weighted higher - pulls toward the target even after a big step
        lterm = err ** 2 + R * self.du ** 2
        self.mpc.set_objective(mterm=mterm, lterm=lterm)
        self.mpc.set_rterm(du=0.0)
 
        self.mpc.bounds['lower', '_x', 'u'] = p.u_min
        self.mpc.bounds['upper', '_x', 'u'] = p.u_max
        self.mpc.bounds['lower', '_x', 'h_H'] = self.mpc.bounds['lower', '_x', 'h_L'] = 0.0
        self.mpc.bounds['upper', '_x', 'h_H'] = self.mpc.bounds['upper', '_x', 'h_L'] = p.H
        self.mpc.bounds['lower', '_u', 'du'] = -1.0
        self.mpc.bounds['upper', '_u', 'du'] = 1.0
 
        self.mpc.setup()
        self.mpc.set_initial_guess()
        self._initialized = False  # see step() - reset once we have a real x0
 
    def set_target(self, target_h_L: float):
        self.__init__(self.p, target_h_L, self.Ts, N=self.N, R=self.R, Ki=self.Ki)
 
    def step(self, h_H_hat: float, h_L_meas: float, u_prev: float) -> float:
        err = h_L_meas - self.target_h_L
        # anti-windup: pump at its voltage limit and the error would only
        # push it further - so the integrator freezes (otherwise e_int
        # would grow needlessly large).
        at_max = u_prev >= self.p.u_max - 1e-6
        at_min = u_prev <= self.p.u_min + 1e-6
        if not ((at_max and err < 0.0) or (at_min and err > 0.0)):
            self.e_int_val += err * self.Ts
 
        x0 = np.array([h_H_hat, h_L_meas, u_prev, self.e_int_val]).reshape(-1, 1)
        self.mpc.x0 = x0
        if not self._initialized:
            self.mpc.set_initial_guess()
            self._initialized = True
 
        du_cmd = self.mpc.make_step(x0)
        u_cmd = u_prev + float(np.squeeze(du_cmd)) * self.Ts
        return float(np.clip(u_cmd, self.p.u_min, self.p.u_max))
