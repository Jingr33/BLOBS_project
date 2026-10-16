from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from blobs_project import config
from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.regulation import RegulationService
from blobs_project.translations import tr

from .actions import ActionDispatcher, ActionId
from .frames.footer_frame import FooterFrame
from .frames.header_frame import HeaderFrame
from .frames.regulation_frame import RegulationFrame
from .frames.visualization_frame import VisualizationFrame
from .style import STYLE_SHEET


class MainWindow(QMainWindow):
    def __init__(
        self, regulation_service: RegulationService, csv_service: CsvService
    ) -> None:
        super().__init__()
        self._regulation_service = regulation_service
        self._previous_state: tuple[bool, bool] = (False, False)
        self._action_dispatcher = ActionDispatcher(regulation_service, csv_service)
        self.setWindowTitle(tr("window.title"))
        self.setMinimumSize(config.WINDOW_MINIMUM_WIDTH, config.WINDOW_MINIMUM_HEIGHT)
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setStyleSheet(STYLE_SHEET)
        self._build_ui()
        self._start_timer()

    def _build_ui(self) -> None:
        self._header = HeaderFrame()
        self._regulation_frame = RegulationFrame(self._regulation_service)
        self._visualization = VisualizationFrame()
        self._footer = FooterFrame()
        self._header.action_requested.connect(self._handle_action_requested)
        self._regulation_frame.action_requested.connect(self._handle_action_requested)
        self._regulation_frame.status_changed.connect(self._footer.set_status)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(16)
        layout.addWidget(self._header)
        layout.addLayout(self._build_content(), 1)
        layout.addWidget(self._footer)
        self._footer.set_connection(self._regulation_service.simulated)
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
        self._regulation_service.tick(config.TICK_INTERVAL_MS / 1000.0)
        self._refresh_view()
        self._report_state_changes()

    def _handle_action_requested(self, action_id: ActionId) -> None:
        message = self._action_dispatcher.execute(action_id, self)
        if message is not None:
            self._footer.set_status(message)
        self._refresh_view()
        self._previous_state = (
            self._regulation_service.regulation_active,
            self._regulation_service.self_driven_active,
        )

    def _refresh_view(self) -> None:
        self._regulation_frame.sync()
        self._visualization.update_process_data(
            self._regulation_service.regulation_values
        )
        if self._regulation_service.chart_started:
            samples = self._regulation_service.trend_points()
            desired_samples = self._regulation_service.desired_trend_points()
        else:
            samples = None
            desired_samples = None
        self._visualization.update_trend_samples(
            samples,
            desired_samples,
            self._regulation_service.flow_trend_points(),
            self._regulation_service.pump_power_trend_points(),
        )
        self._footer.set_regulation_time(
            self._regulation_service.elapsed_s
            if self._regulation_service.is_running
            else None
        )
        self._footer.set_remaining_time(self._regulation_service.remaining_s)

    def _report_state_changes(self) -> None:
        current = (
            self._regulation_service.regulation_active,
            self._regulation_service.self_driven_active,
        )
        previous = self._previous_state
        self._previous_state = current
        if current == previous:
            return
        fault = self._regulation_service.fault
        if any(previous) and not any(current) and fault is not None:
            self._footer.set_status(tr("status.fault", reason=fault), alert=True)
        elif previous[1] and not current[1]:
            key = (
                "status.profile_finished"
                if self._regulation_service.profile_finished
                else "status.automatic_stopped"
            )
            self._footer.set_status(tr(key))
        elif current[1] and not previous[1]:
            self._footer.set_status(tr("status.automatic_running"))
        elif previous[0] and not current[0]:
            self._footer.set_status(tr("status.regulation_stopped"))
        elif current[0] and not previous[0]:
            self._footer.set_status(tr("status.regulation_running"))
