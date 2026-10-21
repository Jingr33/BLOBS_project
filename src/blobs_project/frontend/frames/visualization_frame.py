from collections.abc import Sequence

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from blobs_project import config
from blobs_project.backend.dtos import RegulationValues, RunStatistics
from blobs_project.backend.events import EventEntry
from blobs_project.frontend.actions import ActionId, ActionPlace, visible_actions
from blobs_project.frontend.helpers.qt_helper import QtHelper
from blobs_project.frontend.widgets.alert_log_view import AlertLogView
from blobs_project.frontend.widgets.metrics_strip import MetricsStrip
from blobs_project.frontend.widgets.statistics_view import StatisticsView
from blobs_project.frontend.widgets.tank_diagram import TankDiagram
from blobs_project.frontend.widgets.trend_preview import TrendPreview
from blobs_project.translations import tr

NAV_PAGES = (
    "nav.overview",
    "nav.chart",
    "nav.statistics",
    "nav.alerts",
    "nav.regulation",
    "nav.settings",
)


class VisualizationFrame(QFrame):
    action_requested = pyqtSignal(object)

    def __init__(self, regulation_frame: QWidget) -> None:
        super().__init__()
        self.setObjectName("panel")
        self._stack = QStackedWidget()
        self._nav_buttons: list[QPushButton] = []
        self._metrics_strip = MetricsStrip()
        self._tank_diagram = TankDiagram()
        self._overview_trend = TrendPreview()
        self._overview_trend.setMinimumHeight(config.OVERVIEW_TREND_MINIMUM_HEIGHT)
        self._trend_preview = TrendPreview()
        self._statistics_view = StatisticsView()
        self._alert_log_view = AlertLogView()
        self._regulation_frame = regulation_frame
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)
        layout.addLayout(self._build_nav_bar())
        layout.addWidget(self._stack, 1)
        self._add_page(self._build_overview_page())
        self._add_page(self._trend_preview)
        self._add_page(self._statistics_view)
        self._add_page(self._alert_log_view)
        self._add_page(self._build_regulation_page())
        self._add_page(self._build_settings_page())
        self._select_page(0)

    def update_process_data(self, regulation_values: RegulationValues) -> None:
        self._metrics_strip.set_process_data(regulation_values)
        self._tank_diagram.set_process_data(regulation_values)
        self._overview_trend.set_total_energy(regulation_values.total_energy_wh)

    def update_statistics(self, statistics: RunStatistics) -> None:
        self._statistics_view.set_statistics(statistics)

    def update_alert_entries(self, entries: tuple[EventEntry, ...]) -> None:
        self._alert_log_view.set_entries(entries)

    def update_trend_samples(
        self,
        samples: Sequence[tuple[float, float]] | None,
        desired_samples: Sequence[tuple[float, float]] | None = None,
        flow_samples: Sequence[tuple[float, float]] | None = None,
        pump_power_samples: Sequence[tuple[float, float]] | None = None,
    ) -> None:
        for preview in (self._overview_trend, self._trend_preview):
            preview.set_samples(
                samples, desired_samples, flow_samples, pump_power_samples
            )

    def _build_overview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._metrics_strip)
        diagrams = QHBoxLayout()
        diagrams.setSpacing(12)
        diagrams.addWidget(self._tank_diagram, 3)
        diagrams.addWidget(self._overview_trend, 2)
        layout.addLayout(diagrams, 1)
        return page

    def _build_regulation_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self._regulation_frame.setMaximumWidth(480)
        layout.addWidget(self._regulation_frame)
        layout.addStretch()
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(
            QtHelper.make_label(tr("settings.section_title"), "sectionTitle")
        )
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        for action_id in visible_actions(ActionPlace.SETTINGS):
            buttons_row.addWidget(self._build_action_button(action_id))
        buttons_row.addStretch()
        layout.addLayout(buttons_row)
        layout.addStretch()
        return page

    def _build_action_button(self, action_id: ActionId) -> QPushButton:
        button = QPushButton(tr(f"action.{action_id.value}"))
        button.clicked.connect(
            lambda _checked=False, action_id=action_id: self.action_requested.emit(
                action_id
            )
        )
        return button

    def _build_nav_bar(self) -> QHBoxLayout:
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(8)
        for index, key in enumerate(NAV_PAGES):
            nav_bar.addWidget(self._build_nav_button(index, tr(key)))
        nav_bar.addStretch()
        return nav_bar

    def _build_nav_button(self, index: int, label: str) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("nav")
        button.clicked.connect(
            lambda _checked=False, page=index: self._select_page(page)
        )
        self._nav_buttons.append(button)
        return button

    def _add_page(self, widget: QWidget) -> None:
        self._stack.addWidget(widget)

    def _select_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for button_index, button in enumerate(self._nav_buttons):
            QtHelper.set_style_name(
                button, "navActive" if button_index == index else "nav"
            )

    @property
    def current_page(self) -> int:
        return self._stack.currentIndex()
