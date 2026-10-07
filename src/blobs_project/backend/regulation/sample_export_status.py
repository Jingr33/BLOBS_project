from enum import Enum


class SampleExportStatus(Enum):
    WRITTEN = "written"
    NO_SAMPLES = "no_samples"
    FAILED = "failed"
