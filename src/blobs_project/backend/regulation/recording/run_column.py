from enum import StrEnum


class RunColumn(StrEnum):
    """Columns of a recorded run in the CSV export."""

    TIME_S = "time_s"
    DESIRED_CM = "desired_cm"
    ACTUAL_CM = "actual_cm"
    PUMP_VOLTAGE_V = "pump_voltage_v"
    PUMP_POWER_W = "pump_power_w"
    FLOW_L_MIN = "flow_l_min"
