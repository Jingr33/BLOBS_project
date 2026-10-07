from typing import Final

# window default sizes
WINDOW_MINIMUM_WIDTH: Final = 1040
WINDOW_MINIMUM_HEIGHT: Final = 640
WINDOW_WIDTH: Final = 1280
WINDOW_HEIGHT: Final = 700
LOGO_HEIGHT: Final = 64
TICK_INTERVAL_MS: Final = 100

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
TANK_UPPER_COLOR: Final = "#a978ff"
TANK_LOWER_COLOR: Final = "#ff9e5c"
TANK_FILL_COLOR: Final = "#58c7e5"
TANK_ACTUAL_MARKER_COLOR: Final = "#ff3ea5"
TANK_DESIRED_LINE_COLOR: Final = GREEN
TANK_ACTUAL_LEVEL_CM: Final = 17.9
TANK_DESIRED_LEVEL_CM: Final = 20.0
TANK_PIPE_COLOR: Final = "#526b88"
TANK_PUMP_COLOR: Final = CYAN

# trend preview parameters
TREND_MINIMUM_HEIGHT: Final = 170
TREND_TIME_WINDOW_S: Final = 120.0
TREND_X_TICK_S: Final = 30.0
TREND_ACTUAL_COLOR: Final = CYAN
TREND_DESIRED_COLOR: Final = RED
TREND_SERIES: Final = (
    (CYAN, (0.0, 0.65, 0.2, 0.56, 0.42, 0.48, 0.64, 0.34, 0.82, 0.25, 1.0, 0.30)),
    (ORANGE, (0.0, 0.48, 0.2, 0.49, 0.42, 0.53, 0.64, 0.58, 0.82, 0.52, 1.0, 0.55)),
)

DEVIATION_OK_PERCENT: Final = 5.0
LEVEL_RESPONSE_RATE: Final = 0.6

PROFILE_DURATION_S: Final = 120.0
PROFILE_SAMPLE_INTERVAL_S: Final = 1.0
SAMPLE_LOG_LIMIT: Final = 5000

# componenet styles
STYLE_SHEET: Final = f"""
    QMainWindow, QWidget {{
        background: {BACKGROUND};
        color: {TEXT};
        font-family: {FONT_FAMILY};
    }}
    QFrame#panel {{
        background: {PANEL};
        border: 1px solid {PANEL_BORDER};
        border-radius: 12px;
    }}
    QFrame#regulation {{
        background: transparent;
        border: none;
    }}
    QFrame#regulation QLabel {{
        background: transparent;
        border: none;
    }}
    QDoubleSpinBox {{
        background: {BUTTON_BACKGROUND};
        border: 1px solid {BUTTON_BORDER};
        border-radius: 7px;
        padding: 6px 8px;
        color: {TEXT};
        font-weight: 600;
    }}
    QDoubleSpinBox:hover {{
        border-color: {CYAN};
    }}
    QDoubleSpinBox:focus {{
        border-color: {CYAN};
    }}
    QDoubleSpinBox:disabled {{
        background: {PANEL};
        border-color: {PANEL_BORDER};
        color: {MUTED};
    }}
    QLabel#eyebrow {{
        color: {CYAN};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
    }}
    QLabel#sectionTitle {{
        color: {CYAN};
        font-size: 17px;
        font-weight: 700;
        letter-spacing: 3px;
    }}
    QLabel#title {{ font-size: 25px; font-weight: 700; }}
    QLabel#muted {{ color: {MUTED}; }}
    QLabel#profile {{ color: {MUTED}; font-size: 12px; }}
    QPushButton {{
        background: {BUTTON_BACKGROUND};
        border: 1px solid {BUTTON_BORDER};
        border-radius: 7px;
        padding: 9px 14px;
        color: {TEXT};
    }}
    QPushButton:hover {{
        background: {BUTTON_HOVER_BACKGROUND};
        border-color: {CYAN};
    }}
    QPushButton#primary {{
        background: {CYAN};
        color: {PRIMARY_TEXT};
        font-weight: 700;
        border: 0;
    }}
    QPushButton#danger {{
        background: {RED};
        color: {DANGER_TEXT};
        font-weight: 700;
        border: 0;
    }}
    QPushButton:disabled,
    QPushButton#primary:disabled,
    QPushButton#danger:disabled {{
        background: {PANEL};
        border: 1px solid {PANEL_BORDER};
        color: {MUTED};
        font-weight: 600;
    }}
    QPushButton#small {{ padding: 6px 10px; }}
    QPushButton#nav {{
        background: transparent;
        border: 1px solid {PANEL_BORDER};
        border-radius: 7px;
        padding: 7px 14px;
        color: {MUTED};
        font-weight: 600;
    }}
    QPushButton#nav:hover {{
        color: {TEXT};
        border-color: {CYAN};
    }}
    QPushButton#navActive {{
        background: {CYAN};
        border: 1px solid {CYAN};
        border-radius: 7px;
        padding: 7px 14px;
        color: {PRIMARY_TEXT};
        font-weight: 700;
    }}
"""
