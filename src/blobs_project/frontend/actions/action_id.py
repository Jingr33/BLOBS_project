from enum import Enum


class ActionId(Enum):
    FORCE_RESET = "force_reset"
    IMPORT_CSV = "import_csv"
    EXPORT_CSV = "export_csv"
    DOWNLOAD_CSV_TEMPLATE = "download_template"
    TARE = "tare"
