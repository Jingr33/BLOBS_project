from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from blobs_project import config
from blobs_project.backend.dtos import RegulationValues
from blobs_project.translations import tr

from .metric_card import MetricCard


class MetricsStrip(QWidget):
    """Numeric readouts unified on the Overview tab from the regulation panel."""

    def __init__(self) -> None:
        super().__init__()
        self._power_card = MetricCard(tr("metrics.pump_power"))
        self._voltage_card = MetricCard(tr("metrics.pump_voltage"))
        self._height_card = MetricCard(tr("metrics.actual_height"))
        self._flow_card = MetricCard(tr("metrics.flow"))
        cards = QHBoxLayout()
        cards.setSpacing(24)
        for card in (
            self._power_card,
            self._voltage_card,
            self._height_card,
            self._flow_card,
        ):
            cards.addWidget(card, 1)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addLayout(cards)

    def set_process_data(self, regulation_values: RegulationValues) -> None:
        """Refresh the readouts; pump-related values turn green while running."""
        running = regulation_values.pump_power_w > 0.0
        pump_color = config.GREEN if running else ""
        self._power_card.set_value(f"{regulation_values.pump_power_w:.2f}", pump_color)
        self._voltage_card.set_value(
            f"{regulation_values.pump_voltage_v:.2f}", pump_color
        )
        self._height_card.set_value(
            tr("common.value_cm", value=f"{regulation_values.tank2_actual_cm:.1f}")
        )
        self._flow_card.set_value(f"{regulation_values.flow_l_min:.1f}", pump_color)
