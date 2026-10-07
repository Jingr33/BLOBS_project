from __future__ import annotations

import math
from collections.abc import Sequence

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from blobs_project import config
from blobs_project.translations import tr

PLOT_LEFT_MARGIN: float = 46.0
PLOT_TOP_MARGIN: float = 20.0
PLOT_RIGHT_MARGIN: float = 16.0
PLOT_BOTTOM_MARGIN: float = 58.0
Y_LABEL_WIDTH: float = 34.0
Y_LABEL_BLOCK_HEIGHT: float = 34.0
X_LABEL_WIDTH: float = 56.0


class TrendPreview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(config.TREND_MINIMUM_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._samples: list[tuple[float, float]] | None = None
        self._desired_samples: list[tuple[float, float]] | None = None
        self._x_span = config.TREND_TIME_WINDOW_S

    def set_samples(
        self,
        samples: Sequence[tuple[float, float]] | None,
        desired_samples: Sequence[tuple[float, float]] | None = None,
    ) -> None:
        if samples is None:
            self._samples = None
            self._desired_samples = None
            self._x_span = config.TREND_TIME_WINDOW_S
        else:
            self._samples = list(samples)
            self._desired_samples = (
                [] if desired_samples is None else list(desired_samples)
            )
            self._x_span = self._calculate_x_span()
        self.update()

    def _calculate_x_span(self) -> float:
        times = [time_s for time_s, _ in self._samples or []]
        times.extend(time_s for time_s, _ in self._desired_samples or [])
        if not times:
            return config.TREND_TIME_WINDOW_S
        latest = max(times)
        if latest <= config.TREND_TIME_WINDOW_S:
            return config.TREND_TIME_WINDOW_S
        steps = math.ceil(latest / config.TREND_X_TICK_S)
        return steps * config.TREND_X_TICK_S

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(config.PANEL))

        plot = self._plot_rect()
        self._draw_grid(painter, plot, self._x_span)
        self._draw_axis_labels(painter, plot)
        self._draw_series(painter, plot)

    def _plot_rect(self) -> QRectF:
        return QRectF(
            PLOT_LEFT_MARGIN,
            PLOT_TOP_MARGIN,
            max(100.0, self.width() - PLOT_LEFT_MARGIN - PLOT_RIGHT_MARGIN),
            max(60.0, self.height() - PLOT_TOP_MARGIN - PLOT_BOTTOM_MARGIN),
        )

    @staticmethod
    def _x_ticks(x_span: float) -> list[float]:
        step = config.TREND_X_TICK_S
        return [step * index for index in range(int(x_span / step) + 1)]

    @staticmethod
    def _draw_grid(painter: QPainter, plot: QRectF, x_span: float) -> None:
        painter.setPen(QPen(QColor("#29405d"), 1))
        for tick in config.TANK_SCALE_TICKS:
            y = plot.bottom() - plot.height() * (tick / config.TANK_LEVEL_MAX_CM)
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
        for time_tick in TrendPreview._x_ticks(x_span):
            x = plot.left() + plot.width() * (time_tick / x_span)
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
        painter.setPen(QPen(QColor(config.MUTED), 1))
        painter.drawRect(plot)

    def _draw_axis_labels(self, painter: QPainter, plot: QRectF) -> None:
        painter.setPen(QPen(QColor(config.MUTED), 1))
        self._draw_y_axis_label(painter, plot)
        for tick in config.TANK_SCALE_TICKS:
            y = plot.bottom() - plot.height() * (tick / config.TANK_LEVEL_MAX_CM)
            painter.drawText(
                QRectF(4, y - 9, Y_LABEL_WIDTH, 18),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(tick),
            )
        x_ticks = self._x_ticks(self._x_span)
        max_labels = max(2, int(plot.width() // 40))
        label_step = max(1, math.ceil(len(x_ticks) / max_labels))
        for index, time_tick in enumerate(x_ticks):
            if index % label_step != 0:
                continue
            x = plot.left() + plot.width() * (time_tick / self._x_span)
            left = min(
                max(x - X_LABEL_WIDTH / 2, 4.0), self.width() - 4 - X_LABEL_WIDTH
            )
            painter.drawText(
                QRectF(left, plot.bottom() + 6, X_LABEL_WIDTH, 16),
                Qt.AlignmentFlag.AlignCenter,
                str(int(time_tick)),
            )
        painter.drawText(
            QRectF(plot.left(), self.height() - 20, plot.width(), 16),
            Qt.AlignmentFlag.AlignCenter,
            tr("trend.x_axis"),
        )

    @staticmethod
    def _draw_y_axis_label(painter: QPainter, plot: QRectF) -> None:
        painter.save()
        painter.translate(PLOT_LEFT_MARGIN / 2, (plot.top() + plot.bottom()) / 2)
        painter.rotate(-90)
        painter.drawText(
            QRectF(
                -plot.height() / 2,
                -Y_LABEL_BLOCK_HEIGHT / 2,
                plot.height(),
                Y_LABEL_BLOCK_HEIGHT,
            ),
            Qt.AlignmentFlag.AlignCenter,
            tr("trend.y_axis"),
        )
        painter.restore()

    def _draw_series(self, painter: QPainter, plot: QRectF) -> None:
        if self._samples is None:
            self._draw_preview_series(painter, plot)
            return
        if self._desired_samples:
            self._draw_line(
                painter,
                plot,
                self._desired_samples,
                config.TREND_DESIRED_COLOR,
                Qt.PenStyle.DashLine,
            )
        if self._samples:
            self._draw_line(
                painter,
                plot,
                self._samples,
                config.TREND_ACTUAL_COLOR,
                Qt.PenStyle.SolidLine,
            )

    def _draw_line(
        self,
        painter: QPainter,
        plot: QRectF,
        points: Sequence[tuple[float, float]],
        color: str,
        pen_style: Qt.PenStyle,
    ) -> None:
        pen = QPen(QColor(color), 2, pen_style)
        painter.setPen(pen)
        if len(points) == 1:
            painter.setBrush(QColor(color))
            painter.drawEllipse(self._point_at(plot, *points[0]), 3.0, 3.0)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            return
        path = QPainterPath()
        for index, point in enumerate(points):
            position = self._point_at(plot, *point)
            if index == 0:
                path.moveTo(position)
            else:
                path.lineTo(position)
        painter.drawPath(path)

    def _point_at(self, plot: QRectF, time_s: float, level_cm: float) -> QPointF:
        x_fraction = min(1.0, max(0.0, time_s / self._x_span))
        y_fraction = min(1.0, max(0.0, level_cm / config.TANK_LEVEL_MAX_CM))
        return QPointF(
            plot.left() + plot.width() * x_fraction,
            plot.bottom() - plot.height() * y_fraction,
        )

    @staticmethod
    def _draw_preview_series(painter: QPainter, plot: QRectF) -> None:
        for color, points in config.TREND_SERIES:
            path = QPainterPath()
            for index in range(0, len(points), 2):
                x = plot.left() + plot.width() * points[index]
                y = plot.top() + plot.height() * points[index + 1]
                if index == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            painter.setPen(QPen(QColor(color), 2))
            painter.drawPath(path)
