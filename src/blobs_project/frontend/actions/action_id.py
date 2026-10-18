from enum import Enum


class ActionId(Enum):
    IMPORT_CSV = "import_csv"
    EXPORT_CSV = "export_csv"
    DOWNLOAD_CSV_TEMPLATE = "download_template"
    TARE = "tare"
