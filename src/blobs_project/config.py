from typing import Final

# window default sizes
WINDOW_MINIMUM_WIDTH: Final = 1040
WINDOW_MINIMUM_HEIGHT: Final = 640
WINDOW_WIDTH: Final = 1280
WINDOW_HEIGHT: Final = 700
TICK_INTERVAL_MS: Final = 100
CLOCK_INTERVAL_MS: Final = 1000

# application main colors
BACKGROUND: Final = "#d9dcdf"
PANEL: Final = "#eceef0"
PANEL_BORDER: Final = "#8a9199"
TEXT: Final = "#1c1f23"
MUTED: Final = "#4a4f55"
CYAN: Final = "#4a5058"  # primary / active elements (slate grey)
GREEN: Final = "#4a4f55"  # normal state - neutral instead of green
ORANGE: Final = "#6b7280"  # T2 label, flow series - mid grey
RED: Final = "#d6001c"  # alarm only
VIOLET: Final = "#5f6670"  # T1 label - dark grey
YELLOW: Final = "#b36b00"  # warning (amber), readable on light grey
ACTUAL_BLUE: Final = "#1f5fa8"  # Actual value
DESIRED_GREY: Final = "#4d4d4d"  # Desired value in the trend
SETPOINT_DARK: Final = "#333333"  # Desired line / marker in the tank

READOUT_BACKGROUND: Final = "#17263a"
GRID: Final = "#29405d"
GRID_DASH: Final = "#324a67"
TANK_OUTLINE: Final = "#8ba2be"
TANK_BODY: Final = "#182940"
PUMP_BODY: Final = "#173746"

# deatil colors
BUTTON_BACKGROUND: Final = "#f6f7f8"
BUTTON_BORDER: Final = "#6b7280"
BUTTON_HOVER_BACKGROUND: Final = "#e2e5e8"
PRIMARY_TEXT: Final = "#ffffff"  # text on CYAN and on grey labels
DANGER_TEXT: Final = "#ffffff"  # text on RED
FONT_FAMILY: Final = "Arial"

# tank diagram parameters
TANK_MINIMUM_WIDTH: Final = 560
TANK_MINIMUM_HEIGHT: Final = 360
TANK_LEVEL_MAX_CM: Final = 30
TANK_SCALE_TICKS: Final = (0, 10, 20, 30)
TANK_UPPER_COLOR: Final = VIOLET
TANK_LOWER_COLOR: Final = ORANGE
TANK_FILL_COLOR: Final = "#9fb3c8"
TANK_ACTUAL_MARKER_COLOR: Final = ACTUAL_BLUE
TANK_DESIRED_LINE_COLOR: Final = SETPOINT_DARK
TANK_ACTUAL_LEVEL_CM: Final = 17.9
TANK_DESIRED_LEVEL_CM: Final = 20.0
TANK_PIPE_COLOR: Final = "#8a9199"
TANK_PUMP_COLOR: Final = "#4a5058"  # running pump / flow

# trend preview parameters
TREND_MINIMUM_HEIGHT: Final = 240
TREND_TIME_WINDOW_S: Final = 120.0
TREND_X_TICK_S: Final = 30.0
TREND_ACTUAL_COLOR: Final = ACTUAL_BLUE
TREND_DESIRED_COLOR: Final = DESIRED_GREY
TREND_FLOW_COLOR: Final = ORANGE
TREND_POWER_COLOR: Final = "#2a7f7f"  # teal, distinct from the grey flow line
TREND_SERIES: Final = (
    (
        ACTUAL_BLUE,
        (0.0, 0.65, 0.2, 0.56, 0.42, 0.48, 0.64, 0.34, 0.82, 0.25, 1.0, 0.30),
    ),
    (ORANGE, (0.0, 0.48, 0.2, 0.49, 0.42, 0.53, 0.64, 0.58, 0.82, 0.52, 1.0, 0.55)),
)

DEVIATION_OK_PERCENT: Final = 5.0

PROFILE_DURATION_S: Final = 120.0
PROFILE_SAMPLE_INTERVAL_S: Final = 1.0
# Default time one profile level is held [s]; the operator can change it.
PROFILE_STEP_S: Final = 300.0

# NI DAQ / tower hardware
# NI-DAQmx device name of the USB-6001 card.
DAQ_DEVICE_NAME: Final = "Dev1"
# Lower-tank level sensor input.
TOWER_LEVEL_CHANNEL: Final = "ai0"
# Pump driver output.
TOWER_PUMP_CHANNEL: Final = "ao1"
# Level sensor gain (TMDG 338 Z3H), fitted to the tank scale on 16 Oct 2026.
TOWER_LEVEL_CM_PER_V: Final = 3.17
# Sensor voltage of an empty tank; drifts, re-tare before use.
TOWER_LEVEL_ZERO_V: Final = 0.255
# Height of the sensor zero (empty, drained tank) above the tank bottom [cm].
TOWER_LEVEL_OFFSET_CM: Final = 1.54
# Pump cap; above it the upper tank overflows.
TOWER_PUMP_MAX_V: Final = 7.5
SAMPLE_LOG_LIMIT: Final = 5000

# regulation loop
# Controller and measurement period [s].
CONTROL_PERIOD_S: Final = 0.5
# PI gains (CHR tuning), level in metres -> pump volts.
PI_KP_V_PER_M: Final = 46.8
PI_KI: Final = 1.28
# Predictive controller model and tuning (validate against physical runs).
MPC_HORIZON_STEPS: Final = 50
MPC_MOVE_WEIGHT: Final = 0.1
MPC_INTEGRAL_GAIN: Final = 0.010
# Bound accumulated tracking error to prevent delayed-plant integral windup.
MPC_INTEGRAL_LIMIT_M_S: Final = 1.0
MPC_RATE_LIMIT_V_S: Final = 1.0
MPC_PROCESS_NOISE_VARIANCE_M2: Final = 1e-6
MPC_SENSOR_NOISE_VARIANCE_M2: Final = 1e-5
# Lowest PI output; below ~1.56 V the pump lifts no water.
PI_MIN_V: Final = 1.5
# Median window against single sensor spikes [samples].
LEVEL_MEDIAN_SAMPLES: Final = 5
# Invalid level readings in a row before the run stops.
MAX_INVALID_SAMPLES: Final = 5
# Time horizon for projecting a rising lower-tank level to the warning threshold.
LEVEL_PREDICTION_HORIZON_S: Final = 10.0

# safety limits
# Allowed desired level of the lower tank [cm].
SETPOINT_MIN_CM: Final = 3.0
SETPOINT_MAX_CM: Final = 22.0
# Lower-tank level that warns of overflow [cm].
LEVEL_WARNING_CM: Final = 23.0
# Lower-tank level that stops the run and the pump [cm].
LEVEL_TRIP_CM: Final = 25.0
# Empty-tank readings averaged by the sensor tare.
TARE_SAMPLES: Final = 10
TARE_INTERVAL_S: Final = 0.05

# run statistics
# Setpoint change that starts a new step in the statistics [cm].
STEP_MIN_CM: Final = 0.1
# Settling band: percent of the step size, but at least the minimum [cm].
SETTLING_BAND_PERCENT: Final = 5.0
SETTLING_BAND_MIN_CM: Final = 0.2
# Overshoot smaller than this is sensor noise and is not counted [cm].
OVERSHOOT_MIN_CM: Final = 0.1
# Efficiency: level within the tolerance [cm], not counting the time after a change.
EFFICIENCY_TOL_CM: Final = 0.1
EFFICIENCY_SKIP_S: Final = 120.0

# process estimates from the 7 Oct 2026 measurements
# Lower-tank outflow coefficient [m^2]; steady flow = c * sqrt(2 g h).
LOWER_OUTFLOW_COEFF_M2: Final = 1.11327e-05
GRAVITY_M_S2: Final = 9.81
# Pump current I = a + b*u [A] and pump voltage U = c + d*u [V] vs control voltage u.
PUMP_CURRENT_A: Final = (0.408, 0.0741)
PUMP_VOLTAGE_V: Final = (3.5, 0.6)
