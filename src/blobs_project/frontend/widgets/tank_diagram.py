from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QSizePolicy, QWidget

from blobs_project import config
from blobs_project.translations import tr

from .tank_geometry import TankGeometry

ARROW_HALF_WIDTH: float = 8.0
ARROW_BODY: float = 11.0
TANK_FILL_INSET: float = 4.0
MARKER_SIZE: float = 7.0
PILL_TEXT_PADDING: float = 26.0


class TankDiagram(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(config.TANK_MINIMUM_WIDTH, config.TANK_MINIMUM_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._tank2_actual_cm = config.TANK_ACTUAL_LEVEL_CM
        self._tank2_desired_cm = config.TANK_DESIRED_LEVEL_CM

    def set_process_data(self, tank2_actual_cm: float, tank2_desired_cm: float) -> None:
        self._tank2_actual_cm = tank2_actual_cm
        self._tank2_desired_cm = tank2_desired_cm
        self.update()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(config.PANEL))
        geometry = TankGeometry.from_size(float(self.width()), float(self.height()))
        self._draw_pipes(painter, geometry)
        self._draw_tank_body(painter, geometry.tank1)
        self._draw_missing_sensor(painter, geometry.tank1)
        self._draw_tank_body(painter, geometry.tank2)
        self._draw_level(painter, geometry.tank2)
        self._draw_scale(painter, geometry)
        self._draw_pump(painter, geometry.pump)
        self._draw_pill(
            painter,
            geometry,
            geometry.tank1,
            tr("tank.upper_label"),
            config.TANK_UPPER_COLOR,
        )
        self._draw_pill(
            painter,
            geometry,
            geometry.tank2,
            tr("tank.lower_label"),
            config.TANK_LOWER_COLOR,
        )

    def _draw_pipes(self, painter: QPainter, geometry: TankGeometry) -> None:
        center_x = geometry.tank_center_x
        pipe_y = geometry.pump.center().y()
        painter.save()
        painter.setPen(QPen(QColor(config.TANK_PIPE_COLOR), 4))
        painter.drawLine(
            QPointF(geometry.pump.right(), pipe_y), QPointF(center_x, pipe_y)
        )
        painter.drawLine(
            QPointF(center_x, pipe_y), QPointF(center_x, geometry.tank1.top())
        )
        painter.drawLine(
            QPointF(center_x, geometry.tank1.bottom()),
            QPointF(center_x, geometry.tank2.top()),
        )
        painter.restore()
        arrow_color = QColor(config.TANK_PIPE_COLOR)
        self._draw_arrow(painter, QPointF(center_x, geometry.tank1.top()), arrow_color)
        self._draw_arrow(painter, QPointF(center_x, geometry.tank2.top()), arrow_color)

    @staticmethod
    def _draw_arrow(painter: QPainter, tip: QPointF, color: QColor) -> None:
        polygon = QPolygonF(
            [
                tip,
                QPointF(tip.x() - ARROW_HALF_WIDTH, tip.y() - ARROW_BODY),
                QPointF(tip.x() + ARROW_HALF_WIDTH, tip.y() - ARROW_BODY),
            ]
        )
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(polygon)
        painter.restore()

    @staticmethod
    def _draw_tank_body(painter: QPainter, tank: QRectF) -> None:
        painter.save()
        painter.setPen(QPen(QColor("#8ba2be"), 2))
        painter.setBrush(QColor("#182940"))
        painter.drawRoundedRect(tank, 12, 12)
        painter.restore()

    @staticmethod
    def _draw_missing_sensor(painter: QPainter, tank: QRectF) -> None:
        painter.save()
        painter.setPen(QPen(QColor(config.MUTED), 1))
        painter.drawText(tank, Qt.AlignmentFlag.AlignCenter, tr("diagram.no_sensor"))
        painter.restore()

    def _draw_level(self, painter: QPainter, tank: QRectF) -> None:
        fraction = max(0.0, min(1.0, self._tank2_actual_cm / config.TANK_LEVEL_MAX_CM))
        fill_height = (tank.height() - 2 * TANK_FILL_INSET) * fraction
        fill = QRectF(
            tank.left() + TANK_FILL_INSET,
            tank.bottom() - TANK_FILL_INSET - fill_height,
            tank.width() - 2 * TANK_FILL_INSET,
            fill_height,
        )
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(config.TANK_FILL_COLOR))
        painter.drawRoundedRect(fill, 4, 4)
        painter.restore()

        self._draw_actual_marker(painter, fill.left(), fill.top())
        self._draw_desired_line(painter, tank)

    @staticmethod
    def _draw_actual_marker(painter: QPainter, left: float, level_y: float) -> None:
        polygon = QPolygonF(
            [
                QPointF(left, level_y),
                QPointF(left + 2 * MARKER_SIZE, level_y - MARKER_SIZE),
                QPointF(left + 2 * MARKER_SIZE, level_y + MARKER_SIZE),
            ]
        )
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(config.TANK_ACTUAL_MARKER_COLOR))
        painter.drawPolygon(polygon)
        painter.restore()

    def _draw_desired_line(self, painter: QPainter, tank: QRectF) -> None:
        fraction = max(0.0, min(1.0, self._tank2_desired_cm / config.TANK_LEVEL_MAX_CM))
        desired_y = tank.bottom() - tank.height() * fraction
        painter.save()
        painter.setPen(
            QPen(QColor(config.TANK_DESIRED_LINE_COLOR), 2, Qt.PenStyle.DashLine)
        )
        painter.drawLine(
            QPointF(tank.left() + TANK_FILL_INSET, desired_y),
            QPointF(tank.right() - TANK_FILL_INSET, desired_y),
        )
        painter.restore()

    @staticmethod
    def _draw_scale(painter: QPainter, geometry: TankGeometry) -> None:
        tank = geometry.tank2
        text_left = geometry.scale_left
        label_width = tank.left() - text_left
        painter.save()
        painter.setPen(QPen(QColor(config.MUTED), 1))
        painter.drawText(
            QRectF(text_left - 10, tank.top() - 34, label_width, 20),
            Qt.AlignmentFlag.AlignRight,
            tr("diagram.scale_unit"),
        )
        for tick in config.TANK_SCALE_TICKS:
            tick_y = tank.bottom() - tank.height() * (tick / config.TANK_LEVEL_MAX_CM)
            painter.setPen(QPen(QColor("#324a67"), 1, Qt.PenStyle.DashLine))
            painter.drawLine(
                QPointF(tank.left(), tick_y), QPointF(tank.right(), tick_y)
            )
            painter.setPen(QPen(QColor(config.MUTED), 1))
            painter.drawText(
                QRectF(text_left - 10, tick_y - 10, label_width, 20),
                Qt.AlignmentFlag.AlignRight,
                str(tick),
            )
        painter.restore()

    @staticmethod
    def _draw_pump(painter: QPainter, pump: QRectF) -> None:
        painter.save()
        painter.setPen(QPen(QColor(config.TANK_PUMP_COLOR), 2))
        painter.setBrush(QColor("#173746"))
        painter.drawRoundedRect(pump, 8, 8)
        painter.setPen(QPen(QColor(config.TANK_PUMP_COLOR), 1))
        painter.drawText(pump, Qt.AlignmentFlag.AlignCenter, tr("diagram.pump"))
        painter.restore()

    @staticmethod
    def _draw_pill(
        painter: QPainter,
        geometry: TankGeometry,
        tank: QRectF,
        text: str,
        color: str,
    ) -> None:
        font = QFont(painter.font())
        font.setBold(True)
        width = QFontMetricsF(font).horizontalAdvance(text) + PILL_TEXT_PADDING
        height = geometry.pill_height
        rect = QRectF(geometry.pill_x, tank.center().y() - height / 2, width, height)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(rect, height / 2, height / 2)
        painter.setFont(font)
        painter.setPen(QColor(config.PRIMARY_TEXT))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()
