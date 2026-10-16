from typing import Final

# window default sizes
WINDOW_MINIMUM_WIDTH: Final = 1040
WINDOW_MINIMUM_HEIGHT: Final = 640
WINDOW_WIDTH: Final = 1280
WINDOW_HEIGHT: Final = 700
LOGO_HEIGHT: Final = 64
TICK_INTERVAL_MS: Final = 100
CLOCK_INTERVAL_MS: Final = 1000

# application main colors
BACKGROUND: Final = "#0b1220"
PANEL: Final = "#111c2e"
PANEL_BORDER: Final = "#263750"
TEXT: Final = "#e6edf7"
MUTED: Final = "#8da0b8"
CYAN: Final = "#45d7e8"
GREEN: Final = "#70e1ac"
ORANGE: Final = "#ffab5c"
RED: Final = "#ff6d83"
VIOLET: Final = "#a978ff"
YELLOW: Final = "#ffd166"

# deatil colors
BUTTON_BACKGROUND: Final = "#1b2b42"
BUTTON_BORDER: Final = "#385273"
BUTTON_HOVER_BACKGROUND: Final = "#263d5a"
PRIMARY_TEXT: Final = "#07121e"
DANGER_TEXT: Final = "#1b0b12"
FONT_FAMILY: Final = "Arial"

# tank diagram parameters
TANK_MINIMUM_WIDTH: Final = 560
TANK_MINIMUM_HEIGHT: Final = 360
TANK_LEVEL_MAX_CM: Final = 30
TANK_SCALE_TICKS: Final = (0, 10, 20, 30)
TANK_UPPER_COLOR: Final = VIOLET
TANK_LOWER_COLOR: Final = "#ff9e5c"
TANK_FILL_COLOR: Final = "#58c7e5"
TANK_ACTUAL_MARKER_COLOR: Final = "#ff3ea5"
TANK_DESIRED_LINE_COLOR: Final = GREEN
TANK_ACTUAL_LEVEL_CM: Final = 17.9
TANK_DESIRED_LEVEL_CM: Final = 20.0
TANK_PIPE_COLOR: Final = "#526b88"
TANK_PUMP_COLOR: Final = CYAN

# trend preview parameters
TREND_MINIMUM_HEIGHT: Final = 240
TREND_TIME_WINDOW_S: Final = 120.0
TREND_X_TICK_S: Final = 30.0
TREND_ACTUAL_COLOR: Final = CYAN
TREND_DESIRED_COLOR: Final = RED
TREND_FLOW_COLOR: Final = ORANGE
TREND_POWER_COLOR: Final = VIOLET
TREND_SERIES: Final = (
    (CYAN, (0.0, 0.65, 0.2, 0.56, 0.42, 0.48, 0.64, 0.34, 0.82, 0.25, 1.0, 0.30)),
    (ORANGE, (0.0, 0.48, 0.2, 0.49, 0.42, 0.53, 0.64, 0.58, 0.82, 0.52, 1.0, 0.55)),
)

DEVIATION_OK_PERCENT: Final = 5.0
LEVEL_RESPONSE_RATE: Final = 0.6

PROFILE_DURATION_S: Final = 120.0
PROFILE_SAMPLE_INTERVAL_S: Final = 1.0

# NI DAQ / tower hardware
# NI-DAQmx device name of the USB-6001 card. Used in: backend/hardware/NIDAQ.py
DAQ_DEVICE_NAME: Final = "Dev1"
# Lower-tank level sensor input. Used in: backend/hardware/tower.py
TOWER_LEVEL_CHANNEL: Final = "ai0"
# Pump driver output. Used in: backend/hardware/tower.py
TOWER_PUMP_CHANNEL: Final = "ao1"
# Level sensor gain, TMDG 338 Z3H 0-3 kPa -> 0-10 V. Used in: backend/hardware/tower.py
TOWER_LEVEL_CM_PER_V: Final = 3.06
# Sensor voltage of an empty tank; drifts, re-tare before use.
# Used in: backend/hardware/tower.py
TOWER_LEVEL_ZERO_V: Final = 0.255
# Pump cap; above it the upper tank overflows. Used in: backend/hardware/tower.py
TOWER_PUMP_MAX_V: Final = 7.5
SAMPLE_LOG_LIMIT: Final = 5000

# process measurements
TANK_CROSS_SECTION_CM2: Final = 200.0
L_MIN_PER_CM3_S: Final = 0.06
WATER_DENSITY_KG_M3: Final = 1000.0
GRAVITY_M_S2: Final = 9.81
PUMP_EFFICIENCY: Final = 0.5
