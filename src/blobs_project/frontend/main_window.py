from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from blobs_project import config
from blobs_project.backend.csv_management import CsvService
from blobs_project.backend.events import EventLog, EventSeverity
from blobs_project.backend.regulation import RegulationService
from blobs_project.translations import tr

from .actions import ActionDispatcher, ActionId
from .frames.footer_frame import FooterFrame
from .frames.header_frame import HeaderFrame
from .frames.regulation_frame import RegulationFrame
from .frames.visualization_frame import VisualizationFrame
from .style import STYLE_SHEET
from .widgets.automatic_controls import AutomaticControls

RunState = tuple[bool, bool, str | None, bool]


class MainWindow(QMainWindow):
    def __init__(
        self, regulation_service: RegulationService, csv_service: CsvService
    ) -> None:
        super().__init__()
        self._regulation_service = regulation_service
        self._previous_state: RunState = (False, False, None, False)
        self._event_log = EventLog()
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
        self._automatic_controls = AutomaticControls(self._regulation_service)
        self._visualization = VisualizationFrame(
            self._regulation_frame, self._automatic_controls
        )
        self._footer = FooterFrame()
        self._header.action_requested.connect(self._handle_action_requested)
        self._header.emergency_stop_requested.connect(self._handle_emergency_stop)
        self._visualization.action_requested.connect(self._handle_action_requested)
        self._automatic_controls.status_changed.connect(self._footer.set_status)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(16)
        layout.addWidget(self._header)
        layout.addWidget(self._visualization, 1)
        layout.addWidget(self._footer)
        self._footer.set_connection(self._regulation_service.simulated)
        self.setCentralWidget(root)
        self._refresh_view()

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
        self._previous_state = self._current_state()

    def _handle_emergency_stop(self) -> None:
        self._regulation_service.emergency_stop()
        self._report_state_changes()
        fault = self._regulation_service.fault
        if fault is not None:
            self._footer.set_status(tr("status.fault", reason=fault), alert=True)
        self._refresh_view()

    def _refresh_view(self) -> None:
        self._regulation_frame.sync()
        self._automatic_controls.sync()
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
        self._visualization.update_statistics(self._regulation_service.statistics)
        self._visualization.update_alert_entries(self._event_log.entries)

    def _current_state(self) -> RunState:
        regulation_service = self._regulation_service
        return (
            regulation_service.regulation_active,
            regulation_service.self_driven_active,
            regulation_service.fault,
            regulation_service.overflow_warning,
        )

    def _report_state_changes(self) -> None:
        current = self._current_state()
        previous = self._previous_state
        self._previous_state = current
        if current == previous:
            return
        self._log_events(current, previous)
        self._report_footer_status(current, previous)

    def _log_events(self, current: RunState, previous: RunState) -> None:
        regulation, automatic, fault, overflow = current
        was_regulation, was_automatic, was_fault, was_overflow = previous
        if fault is not None and fault != was_fault:
            self._event_log.append(
                EventSeverity.FAULT, tr("status.fault", reason=fault)
            )
        if overflow and not was_overflow:
            self._event_log.append(
                EventSeverity.WARNING, tr("regulation.overflow_warning")
            )
        if automatic and not was_automatic:
            self._event_log.append(EventSeverity.INFO, tr("status.automatic_running"))
        elif was_automatic and not automatic:
            key = (
                "status.profile_finished"
                if self._regulation_service.profile_finished
                else "status.automatic_stopped"
            )
            self._event_log.append(EventSeverity.INFO, tr(key))
        if regulation and not was_regulation:
            self._event_log.append(EventSeverity.INFO, tr("status.regulation_running"))
        elif was_regulation and not regulation and not automatic:
            self._event_log.append(EventSeverity.INFO, tr("status.regulation_stopped"))

    def _report_footer_status(self, current: RunState, previous: RunState) -> None:
        regulation, automatic, fault, _overflow = current
        was_regulation, was_automatic, _was_fault, _was_overflow = previous
        if (
            any((was_regulation, was_automatic))
            and not any((regulation, automatic))
            and fault is not None
        ):
            self._footer.set_status(tr("status.fault", reason=fault), alert=True)
        elif was_automatic and not automatic:
            key = (
                "status.profile_finished"
                if self._regulation_service.profile_finished
                else "status.automatic_stopped"
            )
            self._footer.set_status(tr(key))
        elif automatic and not was_automatic:
            self._footer.set_status(tr("status.automatic_running"))
        elif was_regulation and not regulation:
            self._footer.set_status(tr("status.regulation_stopped"))
        elif regulation and not was_regulation:
            self._footer.set_status(tr("status.regulation_running"))
