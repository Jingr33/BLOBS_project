import os
from collections.abc import Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication

from blobs_project import config
from blobs_project.frontend.widgets.trend_preview import TrendPreview

# The application must outlive every standalone widget created in these tests.
_APP = QApplication.instance() or QApplication([])


def test_series_are_drawn_in_their_configured_colours() -> None:
    preview = TrendPreview()
    preview.resize(700, 320)
    preview.set_samples(
        [(0.0, 10.0), (120.0, 10.0)],
        [(0.0, 25.0), (120.0, 25.0)],
        [(0.0, 1.0), (120.0, 1.5)],
        [(0.0, 0.04), (120.0, 0.08)],
    )
    preview.show()
    _APP.processEvents()

    image = preview.grab().toImage()
    for color in (
        config.TREND_ACTUAL_COLOR,
        config.TREND_DESIRED_COLOR,
        config.TREND_FLOW_COLOR,
        config.TREND_POWER_COLOR,
    ):
        assert _color_pixels(image, color) > 40


def test_energy_label_is_only_painted_when_enabled() -> None:
    assert _energy_pixels(show_energy=True) > 50
    assert _energy_pixels(show_energy=False) == 0


def _energy_pixels(show_energy: bool) -> int:
    """Count pixels of the energy label text in the render."""
    preview = TrendPreview(show_energy=show_energy)
    preview.resize(500, 300)
    preview.set_total_energy(12.5)
    preview.show()
    _APP.processEvents()

    image = preview.grab().toImage()
    count = _color_pixels(image, config.TEXT)
    preview.close()
    return count


def _color_pixels(image: QImage, color: str) -> int:
    target = QColor(color)
    return _count_pixels(image, lambda pixel: pixel == target)


def _count_pixels(image: QImage, predicate: Callable[[QColor], bool]) -> int:
    count = 0
    for x in range(image.width()):
        for y in range(image.height()):
            if predicate(image.pixelColor(x, y)):
                count += 1
    return count
