from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QRectF

MINIMUM_TANK_WIDTH: float = 80.0
PUMP_WIDTH: float = 48.0
PUMP_HEIGHT: float = 32.0
PILL_HEIGHT: float = 28.0
PILL_GAP: float = 16.0
SCALE_LABEL_WIDTH: float = 44.0
SCALE_GAP: float = 14.0


@dataclass(frozen=True)
class TankGeometry:
    pump: QRectF
    tank1: QRectF
    tank2: QRectF
    pill_x: float
    pill_height: float
    scale_left: float

    @property
    def tank_center_x(self) -> float:
        return self.tank1.center().x()

    @classmethod
    def from_size(cls, width: float, height: float) -> TankGeometry:
        tank_width = max(MINIMUM_TANK_WIDTH, min(width * 0.24, 150.0))
        tank_x = width * 0.58 - tank_width / 2
        tank1 = QRectF(tank_x, height * 0.10, tank_width, height * 0.34)
        tank2 = QRectF(tank_x, height * 0.55, tank_width, height * 0.38)
        pump = QRectF(width * 0.20, height * 0.10, PUMP_WIDTH, PUMP_HEIGHT)
        return cls(
            pump=pump,
            tank1=tank1,
            tank2=tank2,
            pill_x=tank_x + tank_width + PILL_GAP,
            pill_height=PILL_HEIGHT,
            scale_left=tank_x - SCALE_GAP - SCALE_LABEL_WIDTH,
        )
