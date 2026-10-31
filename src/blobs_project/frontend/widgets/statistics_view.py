from __future__ import annotations

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from blobs_project.backend.dtos import RunStatistics, StepMetrics
from blobs_project.frontend.helpers.qt_helper import QtHelper
from blobs_project.translations import tr

STEP_COLUMNS = (
    "statistics.step_start",
    "statistics.step_levels",
    "statistics.rise_time",
    "statistics.peak_time",
    "statistics.overshoot",
    "statistics.settling_time",
)


class StatisticsView(QWidget):
    """Run summary and the response metrics of every setpoint step."""

    def __init__(self) -> None:
        super().__init__()
        self._statistics: RunStatistics | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        summary = QWidget()
        summary.setObjectName("statisticsSummary")
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(12, 8, 12, 0)
        summary_layout.setSpacing(12)
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        self._duration_label = QtHelper.add_metric_row(
            grid, 0, tr("statistics.duration")
        )
        self._energy_label = QtHelper.add_metric_row(grid, 1, tr("statistics.energy"))
        self._power_label = QtHelper.add_metric_row(
            grid, 2, tr("statistics.mean_power")
        )
        self._efficiency_label = QtHelper.add_metric_row(
            grid, 3, tr("statistics.efficiency")
        )
        summary_layout.addLayout(grid)
        summary_layout.addWidget(
            QtHelper.make_label(tr("statistics.steps_title"), "muted")
        )
        layout.addWidget(summary)
        self._table = QTableWidget(0, len(STEP_COLUMNS))
        self._table.setHorizontalHeaderLabels([tr(key) for key in STEP_COLUMNS])
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        rows, columns = self._table.verticalHeader(), self._table.horizontalHeader()
        if rows is not None and columns is not None:
            rows.setVisible(False)
            columns.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table, 1)

    @property
    def table(self) -> QTableWidget:
        return self._table

    def set_statistics(self, statistics: RunStatistics) -> None:
        """Show ``statistics``; nothing is redrawn if they did not change."""
        if statistics == self._statistics:
            return
        self._statistics = statistics
        self._duration_label.setText(f"{statistics.duration_s:.0f} s")
        self._energy_label.setText(f"{statistics.energy_wh:.3f} Wh")
        self._power_label.setText(f"{statistics.mean_power_w:.2f} W")
        efficiency = statistics.efficiency_percent
        self._efficiency_label.setText(
            "—" if efficiency is None else f"{efficiency:.1f} %"
        )
        self._table.setRowCount(len(statistics.steps))
        for row, step in enumerate(statistics.steps):
            for column, text in enumerate(self._step_cells(step)):
                self._table.setItem(row, column, QTableWidgetItem(text))

    @staticmethod
    def _step_cells(step: StepMetrics) -> tuple[str, ...]:
        def seconds(value: float | None) -> str:
            return "—" if value is None else f"{value:.0f}"

        return (
            f"{step.start_s:.0f}",
            f"{step.from_cm:.1f} → {step.to_cm:.1f}",
            seconds(step.rise_time_s),
            seconds(step.peak_time_s),
            f"{step.overshoot_percent:.1f}",
            seconds(step.settling_time_s),
        )
