from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from blobs_project import config
from blobs_project.backend.regulation import RegulationService
from blobs_project.translations import tr

from .frames.footer_frame import FooterFrame
from .frames.header_frame import HeaderFrame
from .frames.regulation_frame import RegulationFrame
from .frames.visualization_frame import VisualizationFrame


class MainWindow(QMainWindow):
    def __init__(self, service: RegulationService) -> None:
        super().__init__()
        self._service = service
        self._previous_state: tuple[bool, bool] = (False, False)
        self.setWindowTitle(tr("window.title"))
        self.setMinimumSize(config.WINDOW_MINIMUM_WIDTH, config.WINDOW_MINIMUM_HEIGHT)
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setStyleSheet(config.STYLE_SHEET)
        self._build_ui()
        self._start_timer()

    def _build_ui(self) -> None:
        self._header = HeaderFrame()
        self._regulation_frame = RegulationFrame(self._service)
        self._visualization = VisualizationFrame()
        self._footer = FooterFrame()
        self._header.status_changed.connect(self._footer.set_status)
        self._header.force_reset_requested.connect(self._force_reset)
        self._regulation_frame.status_changed.connect(self._footer.set_status)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(16)
        layout.addWidget(self._header)
        layout.addLayout(self._build_content(), 1)
        layout.addWidget(self._footer)
        self.setCentralWidget(root)
        self._refresh_view()

    def _build_content(self) -> QHBoxLayout:
        content = QHBoxLayout()
        content.setSpacing(16)
        content.addWidget(self._regulation_frame, 1)
        content.addWidget(self._visualization, 3)
        return content

    def _start_timer(self) -> None:
        self._timer = QTimer(self)
        self._timer.setInterval(config.TICK_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self) -> None:
        self._service.tick(config.TICK_INTERVAL_MS / 1000.0)
        self._refresh_view()
        self._report_state_changes()

    def _force_reset(self) -> None:
        self._service.force_reset()
        self._previous_state = (False, False)
        self._refresh_view()

    def _refresh_view(self) -> None:
        self._regulation_frame.sync()
        self._visualization.update_process_data(
            self._service.tank2_actual_cm, self._service.tank2_desired_cm
        )
        if self._service.chart_started:
            samples = self._service.trend_points()
            desired_samples = self._service.desired_trend_points()
        else:
            samples = None
            desired_samples = None
        self._visualization.update_trend_samples(samples, desired_samples)
        self._footer.set_regulation_time(
            self._service.elapsed_s if self._service.is_running else None
        )

    def _report_state_changes(self) -> None:
        current = (self._service.regulation_active, self._service.self_driven_active)
        previous = self._previous_state
        self._previous_state = current
        if current == previous:
            return
        if previous[1] and not current[1]:
            key = (
                "status.profile_finished"
                if self._service.profile_finished
                else "status.self_driven_stopped"
            )
            self._footer.set_status(tr(key))
        elif current[1] and not previous[1]:
            self._footer.set_status(tr("status.self_driven_running"))
        elif previous[0] and not current[0]:
            self._footer.set_status(tr("status.regulation_stopped"))
        elif current[0] and not previous[0]:
            self._footer.set_status(tr("status.regulation_running"))
