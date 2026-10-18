from enum import StrEnum


class StepColumn(StrEnum):
    """Columns of the step table in the statistics CSV."""

    STEP_START_S = "step_start_s"
    FROM_CM = "from_cm"
    TO_CM = "to_cm"
    RISE_S = "rise_s"
    PEAK_S = "peak_s"
    OVERSHOOT_PERCENT = "overshoot_percent"
    SETTLING_S = "settling_s"
