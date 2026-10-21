from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QPainter

from blobs_project.config import PRIMARY_TEXT, TEXT
from blobs_project.translations import tr

PILL_TEXT_PADDING: float = 26.0
ENERGY_PILL_TEXT_PADDING: float = 20.0


class PaintHelper:
    @staticmethod
    def draw_energy_pill(
        painter: QPainter,
        total_energy_wh: float,
        x: float,
        y: float,
        pill_height: float,
    ) -> None:
        text = tr("diagram.energy_value", value=total_energy_wh)
        font = QFont(painter.font())
        font.setBold(True)
        width = QFontMetricsF(font).horizontalAdvance(text) + ENERGY_PILL_TEXT_PADDING
        rect = QRectF(x, y, width, pill_height)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(TEXT))
        painter.drawRoundedRect(rect, pill_height / 2, pill_height / 2)
        painter.setFont(font)
        painter.setPen(QColor(PRIMARY_TEXT))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

    @staticmethod
    def draw_pill(
        painter: QPainter,
        text: str,
        color: str,
        x: float,
        y_center: float,
        height: float,
    ) -> None:
        font = QFont(painter.font())
        font.setBold(True)
        width = QFontMetricsF(font).horizontalAdvance(text) + PILL_TEXT_PADDING
        rect = QRectF(x, y_center - height / 2, width, height)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(rect, height / 2, height / 2)
        painter.setFont(font)
        painter.setPen(QColor(PRIMARY_TEXT))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()
