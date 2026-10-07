from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDoubleSpinBox, QFrame, QGridLayout, QLabel

from blobs_project import config
from blobs_project.translations import tr


class TankControl(QFrame):
    desired_changed = pyqtSignal(float)

    def __init__(self, title: str, color: str) -> None:
        super().__init__()
        self._build_ui(title, color)

    def _build_ui(self, title: str, color: str) -> None:
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setVerticalSpacing(8)
        layout.setHorizontalSpacing(12)

        layout.addWidget(self._pill(title, color), 0, 0, 1, 2)
        layout.addWidget(self._caption(tr("regulation.desired")), 1, 0)
        layout.addWidget(self._build_desired_spin(), 1, 1)
        layout.addWidget(self._caption(tr("regulation.actual")), 2, 0)
        self._actual_label = self._value_label()
        layout.addWidget(self._actual_label, 2, 1)
        layout.addWidget(self._caption(tr("regulation.deviation")), 3, 0)
        self._deviation_label = self._value_label()
        layout.addWidget(self._deviation_label, 3, 1)
        layout.setColumnStretch(1, 1)

    @staticmethod
    def _pill(title: str, color: str) -> QLabel:
        pill = QLabel(title)
        pill.setStyleSheet(
            f"background: {color}; color: {config.PRIMARY_TEXT}; "
            "border-radius: 10px; padding: 4px 12px; font-weight: 700;"
        )
        pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return pill

    @staticmethod
    def _caption(text: str) -> QLabel:
        caption = QLabel(text)
        caption.setObjectName("muted")
        return caption

    @staticmethod
    def _value_label() -> QLabel:
        label = QLabel("—")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _build_desired_spin(self) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.0, config.TANK_LEVEL_MAX_CM)
        spin.setDecimals(1)
        spin.setSingleStep(0.1)
        spin.setValue(config.TANK_DESIRED_LEVEL_CM)
        spin.valueChanged.connect(self.desired_changed.emit)
        self._desired_spin = spin
        return spin

    @property
    def desired_spin(self) -> QDoubleSpinBox:
        return self._desired_spin

    def set_values(
        self,
        actual_cm: float | None,
        desired_cm: float,
        deviation_percent: float | None,
    ) -> None:
        self._desired_spin.blockSignals(True)
        self._desired_spin.setValue(desired_cm)
        self._desired_spin.blockSignals(False)

        if actual_cm is None or deviation_percent is None:
            self._actual_label.setText(tr("regulation.no_sensor"))
            self._actual_label.setStyleSheet(f"color: {config.MUTED};")
            self._deviation_label.setText("—")
            self._deviation_label.setStyleSheet(f"color: {config.MUTED};")
            return

        self._actual_label.setText(tr("common.value_cm", value=f"{actual_cm:.1f}"))
        self._actual_label.setStyleSheet(f"color: {config.TEXT};")
        within_limits = abs(deviation_percent) <= config.DEVIATION_OK_PERCENT
        arrow = "▲" if deviation_percent >= 0 else "▼"
        self._deviation_label.setText(f"{arrow} {deviation_percent:+.1f} %")
        self._deviation_label.setStyleSheet(
            f"color: {config.GREEN if within_limits else config.RED}; font-weight: 700;"
        )

    def set_desired_editable(self, editable: bool) -> None:
        self._desired_spin.setEnabled(editable)
