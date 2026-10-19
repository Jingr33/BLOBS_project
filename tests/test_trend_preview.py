import os
from collections.abc import Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication

from blobs_project.frontend.widgets.trend_preview import TrendPreview

# The application must outlive every standalone widget created in these tests.
_APP = QApplication.instance() or QApplication([])


def test_desired_line_is_drawn_in_red() -> None:
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
    red = _count_pixels(image, lambda color: color.red() > 200 and color.green() < 150)
    cyan = _count_pixels(
        image,
        lambda color: color.red() < 120 and color.green() > 170 and color.blue() > 170,
    )
    flow = _count_pixels(
        image,
        lambda color: (
            color.red() > 220 and 100 < color.green() < 210 and color.blue() < 140
        ),
    )
    power = _count_pixels(
        image,
        lambda color: (
            120 < color.red() < 210 and color.green() < 180 and color.blue() > 220
        ),
    )

    assert red > 40
    assert cyan > 30
    assert flow > 4
    assert power > 5


def _count_pixels(image: QImage, predicate: Callable[[QColor], bool]) -> int:
    count = 0
    for x in range(image.width()):
        for y in range(image.height()):
            if predicate(image.pixelColor(x, y)):
                count += 1
    return count
