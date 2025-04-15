import time
from enum import Enum, auto
from functools import cache
from queue import Queue
from typing import Callable, Optional

from PySide6.QtCore import QThreadPool, QRunnable, Signal, QObject
from PySide6.QtGui import QPalette, QPen, Qt
from hspro_api import TriggerType, WaveformAvailable, Waveform
from pytide6 import MainWindow
from sprats.config import AppPersistence
from unlib import Duration

from hspro.gui.model import BoardModel, ChannelCouplingModel, ChannelImpedanceModel


class App:
    app_persistence: AppPersistence
    model: BoardModel
    main_window: Callable[[], MainWindow] = lambda _: None
    exit_application: Callable[[], bool] = lambda: True
    set_connection_status_label: Callable[[str], None] = lambda _: None
    set_live_info_label: Callable[[str], None] = lambda _: None
    set_plot_color_scheme: Callable[[str], None] = lambda _: None
    channels: list[int] = [0, 1]
    set_trigger_level_from_plot_line: Callable[[float], None] = lambda _: None
    set_trigger_pos_from_plot_line: Callable[[float], None] = lambda _: None
    set_channel_active_state: Callable[[int, bool], None] = lambda a, b: None
    set_channel_color: Callable[[int, str], None] = lambda a, b: None
    set_show_grid_state: Callable[[bool], None] = lambda _: None
    set_show_zero_line_state: Callable[[bool], None] = lambda _: None
    set_trigger_level_line_visible: Callable[[bool], None] = lambda _: None
    trigger_disarmed: Callable[[], None] = lambda _: None
    trigger_armed_single: Callable[[], None] = lambda _: None
    trigger_armed_normal: Callable[[], None] = lambda _: None
    trigger_armed_auto: Callable[[], None] = lambda _: None
    trigger_force_acq: Callable[[], None] = lambda _: None
    correct_trigger_position: Callable[[float], None] = lambda _: None
    correct_trigger_level: Callable[[float], None] = lambda _: None
    plot_waveforms: Callable[[tuple[Optional[Waveform], Optional[Waveform]]], None] = lambda _: None

    set_trigger_lines_width: Callable[[int], None] = lambda _: None
    update_trigger_lines_color: Callable[[int], None] = lambda _: None
    set_trigger_lines_color_map: Callable[[str], None] = lambda _: None

    board_thread_pool: QThreadPool
    worker: "GUIWorker"

    trigger_lines_width: int = 1
    trigger_lines_color_map: str = "Blue"
    plot_color_scheme: str = "light"

    def __init__(self):
        self.board_thread_pool = QThreadPool()
        self.worker = GUIWorker(self)
        self.worker.msg_out.disarm_trigger.connect(self.do_disarm_trigger)
        self.worker.msg_out.trigger_armed_single.connect(self.do_trigger_armed_single)
        self.worker.msg_out.trigger_armed_normal.connect(self.do_trigger_armed_normal)
        self.worker.msg_out.trigger_armed_auto.connect(self.do_trigger_armed_auto)
        self.worker.msg_out.trigger_armed_forced_acq.connect(self.do_trigger_armed_forced_acq)
        self.worker.msg_out.plot_waveforms.connect(self.do_plot_waveforms, Qt.ConnectionType.QueuedConnection)
        self.worker.msg_out.correct_trigger_position.connect(self.do_correct_trigger_position)
        self.worker.msg_out.correct_trigger_level.connect(self.do_correct_trigger_level)
        self.board_thread_pool.start(self.worker)

    def init(self):
        plot_color_scheme: str | None = self.app_persistence.config.get_value("plot_color_scheme", str)
        if plot_color_scheme is None:
            plot_color_scheme = "light"
            self.app_persistence.config.set_value("plot_color_scheme", plot_color_scheme)
        self.set_plot_color_scheme(plot_color_scheme)
        self.plot_color_scheme = plot_color_scheme

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
        self.trigger_disarmed()

    def do_trigger_armed_single(self):
        self.trigger_armed_single()

    def do_trigger_armed_normal(self):
        self.trigger_armed_normal()

    def do_trigger_armed_auto(self):
        self.trigger_armed_auto()

    def do_trigger_armed_forced_acq(self):
        self.trigger_force_acq()

    def do_plot_waveforms(self, ws: tuple[Optional[Waveform], Optional[Waveform]]):
        self.plot_waveforms(ws)

    def do_correct_trigger_position(self, position: float):
        self.correct_trigger_position(position)

    def do_correct_trigger_level(self, level: float):
        self.correct_trigger_level(level)


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
        __match_args__ = ("trigger_type", "drain_queue",)

        def __init__(self, trigger_type: TriggerType, drain_queue: bool = True):
            self.trigger_type = trigger_type
            self.drain_queue = drain_queue

    class ArmForceAcq:
        pass

    class PlotAndRearmNormal:
        __match_args__ = ("notify_gui",)

        def __init__(self, notify_gui: bool = False):
            self.notify_gui = notify_gui

    class PlotAndRearmAuto:
        __match_args__ = ("notify_gui",)

        def __init__(self, notify_gui: bool = False):
            self.notify_gui = notify_gui

    class PlotAndRearmSingle:
        __match_args__ = ("notify_gui",)

        def __init__(self, notify_gui: bool = False):
            self.notify_gui = notify_gui

    class Disarm:
        pass

    class PlotAndDisarm:
        pass

    class SetTriggerPosition:
        __match_args__ = ("trigger_position",)

        def __init__(self, trigger_position: float):
            self.trigger_position = trigger_position

    class SetTriggerLevel:
        __match_args__ = ("trigger_level",)

        def __init__(self, trigger_level: float):
            self.trigger_level = trigger_level

    class SetTriggerType:
        __match_args__ = ("trigger_type",)

        def __init__(self, trigger_type: TriggerType):
            self.trigger_type = trigger_type

    class SetTriggerOnChannel:
        __match_args__ = ("channel",)

        def __init__(self, channel: int):
            self.channel = channel

    class SetTriggerToT:
        __match_args__ = ("tot",)

        def __init__(self, tot: int):
            self.tot = tot

    class SetTriggerDelta:
        __match_args__ = ("delta",)

        def __init__(self, delta: int):
            self.delta = delta

    class SetTimeScale:
        __match_args__ = ("dt_per_division",)

        def __init__(self, dt_per_division: Duration):
            self.dt_per_division = dt_per_division

    class SetVoltagePerDiv:
        __match_args__ = ("channel", "dV",)

        def __init__(self, channel: int, dV: float):
            self.channel = channel
            self.dV = dV

    class SetChannel10x:
        __match_args__ = ("channel", "ten_x",)

        def __init__(self, channel: int, ten_x: bool):
            self.channel = channel
            self.ten_x = ten_x

    class SetChannelActive:
        __match_args__ = ("channel", "active",)

        def __init__(self, channel: int, active: bool):
            self.channel = channel
            self.active = active

    class SetChannelCoupling:
        __match_args__ = ("channel", "coupling",)

        def __init__(self, channel: int, coupling: ChannelCouplingModel):
            self.channel = channel
            self.coupling = coupling

    class SetChannelImpedance:
        __match_args__ = ("channel", "impedance",)

        def __init__(self, channel: int, impedance: ChannelImpedanceModel):
            self.channel = channel
            self.impedance = impedance

    class SetMemoryDepth:
        __match_args__ = ("mem_depth",)

        def __init__(self, mem_depth: int):
            self.mem_depth = mem_depth

    class Quit:
        pass


class MessagesFromGUIWorker(QObject):
    disarm_trigger = Signal()
    plot_waveforms = Signal(tuple)
    correct_trigger_position = Signal(float)
    correct_trigger_level = Signal(float)
    trigger_armed_single = Signal()
    trigger_armed_normal = Signal()
    trigger_armed_auto = Signal()
    trigger_armed_forced_acq = Signal()


class ArmType(Enum):
    SINGLE = auto()
    NORMAL = auto()
    AUTO = auto()
    DISARMED = auto()


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
        arm_type = ArmType.DISARMED
        current_trigger_type = TriggerType.DISABLED
        last_auto_armed_at_s = 0.0

        def disarm_if_armed():
            if is_armed:
                self.app.model.trigger.force_arm_trigger(TriggerType.DISABLED)

        def rearm_if_required():
            if is_armed:
                # rearm
                match arm_type:
                    case ArmType.SINGLE:
                        self.messages.put(WorkerMessage.ArmSingle(current_trigger_type))
                    case ArmType.NORMAL:
                        self.messages.put(WorkerMessage.ArmNormal(current_trigger_type, True))
                    case ArmType.AUTO:
                        self.messages.put(WorkerMessage.ArmAuto(current_trigger_type, True))

        while True:
            message = self.messages.get()
            match message:
                case WorkerMessage.ArmSingle(trigger_type):
                    if self.drain_queue():
                        break
                    arm_type = ArmType.SINGLE
                    current_trigger_type = trigger_type
                    self.app.model.trigger.force_arm_trigger(trigger_type)
                    self.messages.put(WorkerMessage.PlotAndDisarm())
                    self.msg_out.trigger_armed_single.emit()
                    is_armed = True

                case WorkerMessage.ArmNormal(trigger_type, drain_queue):
                    if drain_queue:
                        if self.drain_queue():
                            break
                        else:
                            self.msg_out.trigger_armed_normal.emit()
                    arm_type = ArmType.NORMAL
                    current_trigger_type = trigger_type
                    self.app.model.trigger.force_arm_trigger(trigger_type)
                    self.messages.put(WorkerMessage.PlotAndRearmNormal())
                    is_armed = True

                case WorkerMessage.ArmAuto(trigger_type, drain_queue):
                    if drain_queue:
                        if self.drain_queue():
                            break
                        else:
                            self.msg_out.trigger_armed_auto.emit()

                    arm_type = ArmType.AUTO
                    current_trigger_type = trigger_type
                    self.app.model.trigger.force_arm_trigger(trigger_type)
                    last_auto_armed_at_s = time.time()
                    self.messages.put(WorkerMessage.PlotAndRearmAuto())
                    is_armed = True

                case WorkerMessage.ArmForceAcq():
                    if self.drain_queue():
                        break
                    self.msg_out.trigger_armed_forced_acq.emit()
                    self.app.model.trigger.force_arm_trigger(TriggerType.AUTO)
                    is_armed = True
                    match arm_type:
                        case ArmType.DISARMED:
                            self.messages.put(WorkerMessage.PlotAndDisarm())
                        case ArmType.SINGLE:
                            self.messages.put(WorkerMessage.PlotAndRearmSingle(True))
                        case ArmType.NORMAL:
                            self.messages.put(WorkerMessage.PlotAndRearmNormal(True))
                        case ArmType.AUTO:
                            self.messages.put(WorkerMessage.PlotAndRearmAuto(True))

                case WorkerMessage.PlotAndRearmSingle():
                    if is_armed:
                        match self.app.model.is_capture_available():
                            case WaveformAvailable():
                                w1, w2 = self.app.model.get_waveforms()
                                self.msg_out.plot_waveforms.emit((w1, w2))
                                self.messages.put(WorkerMessage.ArmSingle(current_trigger_type))

                            case _:
                                self.messages.put(WorkerMessage.PlotAndRearmNormal())

                case WorkerMessage.PlotAndRearmNormal(notify_gui):
                    if is_armed:
                        match self.app.model.is_capture_available():
                            case WaveformAvailable():
                                w1, w2 = self.app.model.get_waveforms()
                                self.msg_out.plot_waveforms.emit((w1, w2))
                                if notify_gui:
                                    self.msg_out.trigger_armed_normal.emit()
                                self.messages.put(WorkerMessage.ArmNormal(current_trigger_type, False))

                            case _:
                                self.messages.put(WorkerMessage.PlotAndRearmNormal())

                case WorkerMessage.PlotAndRearmAuto(notify_gui):
                    if is_armed:
                        match self.app.model.is_capture_available():
                            case WaveformAvailable():
                                w1, w2 = self.app.model.get_waveforms()
                                self.msg_out.plot_waveforms.emit((w1, w2))
                                if notify_gui:
                                    self.msg_out.trigger_armed_auto.emit()
                                self.messages.put(WorkerMessage.ArmAuto(current_trigger_type, False))

                            case _:
                                if (time.time() - last_auto_armed_at_s) > self.app.model.trigger.max_dt_auto_trig_s:
                                    self.app.model.trigger.force_arm_trigger(TriggerType.AUTO)
                                    last_auto_armed_at_s = time.time()

                                self.messages.put(WorkerMessage.PlotAndRearmAuto())
                        time.sleep(0.01)

                case WorkerMessage.Disarm():
                    if self.drain_queue():
                        break
                    is_armed = False
                    arm_type = ArmType.DISARMED
                    current_trigger_type = TriggerType.DISABLED
                    self.app.model.trigger.force_arm_trigger(TriggerType.DISABLED)
                    self.msg_out.disarm_trigger.emit()

                case WorkerMessage.PlotAndDisarm():
                    if is_armed:
                        available = self.app.model.is_capture_available()
                        match available:
                            case WaveformAvailable():
                                w1, w2 = self.app.model.get_waveforms()
                                self.msg_out.plot_waveforms.emit((w1, w2))
                                self.app.model.trigger.force_arm_trigger(TriggerType.DISABLED)
                                self.msg_out.disarm_trigger.emit()
                                arm_type = ArmType.DISARMED
                                is_armed = False

                            case _:
                                time.sleep(0.01)
                                self.messages.put(WorkerMessage.PlotAndDisarm())

                case WorkerMessage.SetTriggerPosition(trigger_position):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.trigger.position = trigger_position
                    self.msg_out.correct_trigger_position.emit(self.app.model.trigger.position_live)
                    rearm_if_required()

                case WorkerMessage.SetTriggerLevel(trigger_level):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.trigger.level = trigger_level
                    self.msg_out.correct_trigger_level.emit(self.app.model.trigger.level)
                    rearm_if_required()

                case WorkerMessage.SetTriggerType(trigger_type):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    current_trigger_type = trigger_type
                    rearm_if_required()

                case WorkerMessage.SetTriggerOnChannel(channel):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.trigger.on_channel = channel
                    rearm_if_required()

                case WorkerMessage.SetTriggerToT(tot):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.trigger.tot = tot
                    rearm_if_required()

                case WorkerMessage.SetTriggerDelta(delta):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.trigger.delta = delta
                    rearm_if_required()

                case WorkerMessage.SetTimeScale(dt_per_division):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.time_scale = dt_per_division
                    rearm_if_required()

                case WorkerMessage.SetVoltagePerDiv(channel, dV):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.channel[channel].dV = dV
                    rearm_if_required()

                case WorkerMessage.SetChannel10x(channel, ten_x):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.channel[channel].ten_x_probe = ten_x
                    rearm_if_required()

                case WorkerMessage.SetChannelActive(channel, active):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.channel[channel].active = active
                    rearm_if_required()

                case WorkerMessage.SetChannelCoupling(channel, coupling):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.channel[channel].coupling = coupling
                    rearm_if_required()

                case WorkerMessage.SetChannelImpedance(channel, impedance):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.channel[channel].impedance = impedance
                    rearm_if_required()

                case WorkerMessage.SetMemoryDepth(mem_depth):
                    if self.drain_queue():
                        break
                    disarm_if_armed()
                    self.app.model.mem_depth = mem_depth
                    self.app.model.trigger.update_live_trigger_properties()
                    self.msg_out.correct_trigger_position.emit(self.app.model.trigger.position_live)
                    rearm_if_required()

                case WorkerMessage.Quit():
                    break
