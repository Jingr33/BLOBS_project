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
    preview.resize(700, 260)
    preview.set_samples([(0.0, 10.0), (120.0, 10.0)], [(0.0, 25.0), (120.0, 25.0)])
    preview.show()
    _APP.processEvents()

    image = preview.grab().toImage()
    red = _count_pixels(image, lambda color: color.red() > 200 and color.green() < 150)
    cyan = _count_pixels(
        image,
        lambda color: color.red() < 120 and color.green() > 170 and color.blue() > 170,
    )

    assert red > 50
    assert cyan > 50


def _count_pixels(image: QImage, predicate: Callable[[QColor], bool]) -> int:
    count = 0
    for x in range(image.width()):
        for y in range(image.height()):
            if predicate(image.pixelColor(x, y)):
                count += 1
    return count
