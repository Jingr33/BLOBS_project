import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from blobs_project.frontend.frames.footer_frame import FooterFrame

# The application must outlive every standalone frame created in these tests.
_APP = QApplication.instance() or QApplication([])


def test_footer_reports_no_running_regulation() -> None:
    footer = FooterFrame()

    assert footer.time_label.text() == "no regulation is running"


def test_footer_formats_the_regulation_time() -> None:
    footer = FooterFrame()

    footer.set_regulation_time(65.2)

    assert footer.time_label.text() == "Regulation: 01:05.2"

    footer.set_regulation_time(None)

    assert footer.time_label.text() == "no regulation is running"
