import time
from functools import cache
from queue import Queue
from typing import Callable, Optional

from PySide6.QtCore import QThreadPool, QRunnable, Signal, QObject
from PySide6.QtGui import QPalette, QPen, Qt
from hspro_api import TriggerType, WaveformAvailable, Waveform
from pytide6 import MainWindow
from sprats.config import AppPersistence

from hspro.gui.model import BoardModel


class App:
    app_persistence: AppPersistence
    model: BoardModel
    main_window: Callable[[], MainWindow] = lambda _: None
    exit_application: Callable[[], bool] = lambda: True
    set_connection_status_label: Callable[[str], None] = lambda _: None
    set_live_info_label: Callable[[str], None] = lambda _: None
    set_plot_color_scheme: Callable[[str], None] = lambda _: None
    channels: list[int] = [0, 1]
    set_trigger_level_from_side_controls: Callable[[float], None] = lambda _: None
    set_trigger_level_from_plot_line: Callable[[float], None] = lambda _: None
    set_trigger_pos_from_side_controls: Callable[[float], None] = lambda _: None
    set_trigger_pos_from_plot_line: Callable[[float], None] = lambda _: None
    set_channel_active_state: Callable[[int, bool], None] = lambda a, b: None
    set_channel_color: Callable[[int, str], None] = lambda a, b: None
    set_show_grid_state: Callable[[bool], None] = lambda _: None
    set_show_zero_line_state: Callable[[bool], None] = lambda _: None
    set_trigger_level_line_visible: Callable[[bool], None] = lambda _: None
    disarm_trigger: Callable[[], None] = lambda _: None
    arm_single: Callable[[], None] = lambda _: None
    arm_normal: Callable[[], None] = lambda _: None
    arm_auto: Callable[[], None] = lambda _: None
    plot_waveforms: Callable[[tuple[Optional[Waveform], Optional[Waveform]]], None] = lambda _: None

    set_trigger_lines_width: Callable[[int], None] = lambda _: None
    update_trigger_lines_color: Callable[[], None] = lambda _: None
    set_trigger_lines_color_map: Callable[[str], None] = lambda _: None

    board_thread_pool: QThreadPool
    gui_worker: "GUIWorker"

    trigger_lines_width: int = 1
    trigger_lines_color_map: str = "Blue"
    plot_color_scheme: str = "light"

    def init(self):
        plot_color_scheme: str | None = self.app_persistence.config.get_value("plot_color_scheme", str)
        if plot_color_scheme is None:
            plot_color_scheme = "light"
            self.app_persistence.config.set_value("plot_color_scheme", plot_color_scheme)
        self.set_plot_color_scheme(plot_color_scheme)
        self.plot_color_scheme = plot_color_scheme

        self.board_thread_pool = QThreadPool()
        self.gui_worker = GUIWorker(self)
        self.gui_worker.msg_out.disarm_trigger.connect(self.do_disarm_trigger)
        self.gui_worker.msg_out.arm_single.connect(self.do_arm_single)
        self.gui_worker.msg_out.arm_normal.connect(self.do_arm_normal)
        self.gui_worker.msg_out.arm_auto.connect(self.do_arm_auto)
        self.gui_worker.msg_out.plot_waveforms.connect(self.do_plot_waveforms)
        self.board_thread_pool.start(self.gui_worker)

    @cache
    def side_pannels_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, "lightblue")
        return palette

    @cache
    def trigger_lines_pen_default(self) -> QPen:
        pen = QPen()
        pen.setCosmetic(True)
        pen.setColor("#0000FF")
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([4, 4])
        return pen

    def do_disarm_trigger(self):
        self.disarm_trigger()

    def do_arm_single(self):
        self.arm_single()

    def do_arm_normal(self):
        self.arm_normal()

    def do_arm_auto(self):
        self.arm_auto()

    def do_plot_waveforms(self, ws: tuple[Optional[Waveform], Optional[Waveform]]):
        self.plot_waveforms(ws)


class WorkerMessage:
    class ArmSingle:
        __match_args__ = ("trigger_type",)

        def __init__(self, trigger_type: TriggerType):
            self.trigger_type = trigger_type

    class ArmNormal:
        __match_args__ = ("trigger_type", "drain_queue")

        def __init__(self, trigger_type: TriggerType, drain_queue: bool = True):
            self.trigger_type = trigger_type
            self.drain_queue = drain_queue

    class ArmAuto:
        __match_args__ = ("drain_queue",)

        def __init__(self, drain_queue: bool = True):
            self.drain_queue = drain_queue

    class PlotAndRearmNormal:
        __match_args__ = ("trigger_type",)

        def __init__(self, trigger_type: TriggerType):
            self.trigger_type = trigger_type

    class PlotAndRearmAuto:
        pass

    class Disarm:
        pass

    class PlotAndDisarm:
        pass

    class Quit:
        pass


class MessagesFromGUIWorker(QObject):
    disarm_trigger = Signal()
    arm_single = Signal()
    arm_normal = Signal()
    arm_auto = Signal()
    plot_waveforms = Signal(tuple)


class GUIWorker(QRunnable, ):
    def __init__(self, app: App):
        super().__init__()
        self.messages = Queue()
        self.app = app
        self.msg_out = MessagesFromGUIWorker()

    def drain_queue(self) -> bool:
        quit = False
        while not self.messages.empty():
            if isinstance(self.messages.get(), WorkerMessage.Quit):
                quit = True
        return quit

    def run(self):
        is_armed = False
        while True:
            message = self.messages.get()
            match message:
                case WorkerMessage.ArmSingle(trigger_type):
                    if self.drain_queue():
                        break
                    self.app.model.trigger.force_arm_trigger(trigger_type)
                    self.messages.put(WorkerMessage.PlotAndDisarm())
                    self.msg_out.arm_single.emit()
                    is_armed = True

                case WorkerMessage.ArmNormal(trigger_type, drain_queue):
                    if drain_queue and self.drain_queue():
                        break

                    self.app.model.trigger.force_arm_trigger(trigger_type)
                    self.messages.put(WorkerMessage.PlotAndRearmNormal(trigger_type))
                    if drain_queue:
                        self.msg_out.arm_normal.emit()
                    is_armed = True

                case WorkerMessage.ArmAuto(drain_queue):
                    if drain_queue and self.drain_queue():
                        break
                    self.app.model.trigger.force_arm_trigger(TriggerType.AUTO)
                    self.messages.put(WorkerMessage.PlotAndRearmAuto())
                    if drain_queue:
                        self.msg_out.arm_auto.emit()
                    is_armed = True

                case WorkerMessage.PlotAndRearmNormal(trigger_type):
                    if is_armed:
                        match self.app.model.is_capture_available():
                            case WaveformAvailable():
                                w1, w2 = self.app.model.get_waveforms()
                                self.msg_out.plot_waveforms.emit((w1, w2))
                                self.messages.put(WorkerMessage.ArmNormal(trigger_type, False))
                                is_armed = False

                            case _:
                                self.messages.put(WorkerMessage.PlotAndRearmNormal(trigger_type))
                        time.sleep(0.02)

                case WorkerMessage.PlotAndRearmAuto():
                    if is_armed:
                        match self.app.model.is_capture_available():
                            case WaveformAvailable():
                                w1, w2 = self.app.model.get_waveforms()
                                self.msg_out.plot_waveforms.emit((w1, w2))
                                self.messages.put(WorkerMessage.ArmAuto(False))
                                is_armed = False

                            case _:
                                self.messages.put(WorkerMessage.PlotAndRearmAuto())
                        time.sleep(0.02)

                case WorkerMessage.Disarm():
                    is_armed = False
                    self.msg_out.disarm_trigger.emit()

                case WorkerMessage.PlotAndDisarm():
                    if is_armed:
                        available = self.app.model.is_capture_available()
                        match available:
                            case WaveformAvailable():
                                w1, w2 = self.app.model.get_waveforms()
                                self.msg_out.plot_waveforms.emit((w1, w2))
                                self.messages.put(WorkerMessage.Disarm())
                                is_armed = False

                            case _:
                                time.sleep(0.02)
                                self.messages.put(WorkerMessage.PlotAndDisarm())

                case WorkerMessage.Quit():
                    break
