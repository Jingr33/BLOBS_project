from pathlib import Path
from typing import Final

from PyQt6.QtGui import QIcon

ASSETS_DIR: Final = Path(__file__).resolve().parent
LOGO_PATH: Final = ASSETS_DIR / "small_logo_image.png"


def logo_icon() -> QIcon:
    return QIcon(str(LOGO_PATH))
