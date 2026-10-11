# pid.py

class PIController:
    def __init__(self, Kp, Ki, min_out=0.0, max_out=7.5):
        self.Kp = Kp
        self.Ki = Ki
        self.min_out = min_out
        self.max_out = max_out
        
        self.integral = 0.0
        self.last_output = 0.0

    def reset(self):
        """Deletes the internal memory of the controller."""
        self.integral = 0.0
        self.last_output = 0.0

    def compute(self, setpoint, measured, dt):
        if dt <= 0:
            return self.last_output
            
        error = setpoint - measured
        P = self.Kp * error
        self.integral += error * dt
        I = self.Ki * self.integral
        output = P + I
        
        # Anti-windup
        if output > self.max_out:
            output = self.max_out
            self.integral -= error * dt 
        elif output < self.min_out:
            output = self.min_out
            self.integral -= error * dt 
            
        output = max(self.min_out, min(self.max_out, output))
        self.last_output = output
        return output


class PIDController:
    def __init__(self, Kp, Ki, Kd, min_out=0.0, max_out=7.5):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.min_out = min_out
        self.max_out = max_out
        
        self.integral = 0.0
        self.prev_error = 0.0
        self.last_output = 0.0

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0
        self.last_output = 0.0

    def compute(self, setpoint, measured, dt):
        if dt <= 0:
            return self.last_output
            
        error = setpoint - measured
        P = self.Kp * error
        self.integral += error * dt
        I = self.Ki * self.integral
        D = self.Kd * (error - self.prev_error) / dt
        
        output = P + I + D
        
        # Anti-windup
        if output > self.max_out:
            output = self.max_out
            self.integral -= error * dt 
        elif output < self.min_out:
            output = self.min_out
            self.integral -= error * dt 
            
        output = max(self.min_out, min(self.max_out, output))
        self.prev_error = error
        self.last_output = output
        return output