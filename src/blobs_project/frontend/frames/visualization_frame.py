from collections.abc import Sequence

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ...translations import tr
from ..widgets.tank_diagram import TankDiagram
from ..widgets.trend_preview import TrendPreview


class VisualizationFrame(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("panel")
        self._stack = QStackedWidget()
        self._nav_buttons: list[QPushButton] = []
        self._tank_diagram = TankDiagram()
        self._trend_preview = TrendPreview()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)
        layout.addLayout(self._build_nav_bar())
        layout.addWidget(self._stack, 1)
        self._add_page(self._tank_diagram)
        self._add_page(self._trend_preview)
        self._select_page(0)

    def update_process_data(
        self, tank2_actual_cm: float, tank2_desired_cm: float
    ) -> None:
        self._tank_diagram.set_process_data(tank2_actual_cm, tank2_desired_cm)

    def update_trend_samples(
        self,
        samples: Sequence[tuple[float, float]] | None,
        desired_samples: Sequence[tuple[float, float]] | None = None,
    ) -> None:
        self._trend_preview.set_samples(samples, desired_samples)

    def _build_nav_bar(self) -> QHBoxLayout:
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(8)
        for index, key in enumerate(("nav.overview", "nav.chart")):
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
            button.setObjectName("navActive" if button_index == index else "nav")
            style = button.style()
            if style is not None:
                style.unpolish(button)
                style.polish(button)

    @property
    def current_page(self) -> int:
        return self._stack.currentIndex()
