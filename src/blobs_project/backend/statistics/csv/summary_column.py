from enum import StrEnum


class SummaryColumn(StrEnum):
    """Columns of the run summary in the statistics CSV."""

    RUN_TIME_S = "run_time_s"
    ENERGY_WH = "energy_wh"
    MEAN_POWER_W = "mean_power_w"
    WITHIN_1MM_PERCENT = "within_1mm_percent"
