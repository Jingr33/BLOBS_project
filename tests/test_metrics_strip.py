import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel

from blobs_project import config
from blobs_project.backend.dtos import RegulationValues
from blobs_project.frontend.widgets.metric_card import MetricCard
from blobs_project.frontend.widgets.metrics_strip import MetricsStrip

# The application must outlive every standalone widget created in these tests.
_APP = QApplication.instance() or QApplication([])


def test_every_metric_shows_its_numeric_value_under_the_caption() -> None:
    strip = MetricsStrip()
    strip.show()
    _APP.processEvents()
    cards = strip.findChildren(MetricCard)

    assert [caption(card).text() for card in cards] == [
        "Pump power [W]",
        "Pump voltage [V]",
        "Actual height [cm]",
        "Flow [L/min]",
    ]
    for card in cards:
        assert caption(card).y() < value(card).y()


def test_values_follow_the_process_data() -> None:
    strip = MetricsStrip()
    values = RegulationValues.default()
    values.pump_power_w = 1.25
    values.pump_voltage_v = 3.5
    values.flow_l_min = 2.0
    values.tank2_actual_cm = 17.9

    strip.set_process_data(values)
    cards = strip.findChildren(MetricCard)

    assert [value(card).text() for card in cards] == ["1.25", "3.50", "17.9 cm", "2.0"]


def test_pump_related_values_turn_green_while_the_pump_runs() -> None:
    strip = MetricsStrip()
    values = RegulationValues.default()
    values.pump_power_w = 1.0

    strip.set_process_data(values)
    cards = strip.findChildren(MetricCard)

    assert config.GREEN in value(cards[0]).styleSheet()
    assert config.GREEN in value(cards[1]).styleSheet()
    assert config.GREEN in value(cards[3]).styleSheet()
    assert value(cards[2]).styleSheet() == ""


def caption(card: MetricCard) -> QLabel:
    labels = card.findChildren(QLabel)
    return labels[0]


def value(card: MetricCard) -> QLabel:
    labels = card.findChildren(QLabel)
    return labels[1]
