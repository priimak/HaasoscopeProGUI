import math
import time
from dataclasses import dataclass
from enum import Enum
from functools import cache
from random import random
from typing import Type, Callable, Optional

from hspro_api import TriggerType, Waveform
from hspro_api.board import Board, ChannelCoupling, InputImpedance, WaveformAvailability, WaveformAvailable, \
    WaveformUnavailable
from hspro_api.time_constants import TimeConstants
from sprats.config import AppPersistence
from unlib import Duration, MetricValue, TimeUnit

from hspro.gui.scene import SceneCheckpoint

VISUAL_TIME_PER_DIVISION = [
    Duration(1, TimeUnit.NS),
    Duration(2, TimeUnit.NS),
    Duration(5, TimeUnit.NS),
    Duration(10, TimeUnit.NS),
    Duration(20, TimeUnit.NS),
    Duration(50, TimeUnit.NS),
    Duration(100, TimeUnit.NS),
    Duration(200, TimeUnit.NS),
    Duration(500, TimeUnit.NS),
    Duration(1, TimeUnit.US),
    Duration(2, TimeUnit.US),
    Duration(5, TimeUnit.US),
    Duration(10, TimeUnit.US),
    Duration(20, TimeUnit.US),
    Duration(50, TimeUnit.US),
    Duration(100, TimeUnit.US),
    Duration(200, TimeUnit.US),
    Duration(500, TimeUnit.US),
    Duration(1, TimeUnit.MS),
    Duration(2, TimeUnit.MS),
    Duration(5, TimeUnit.MS),
    Duration(10, TimeUnit.MS),
    Duration(20, TimeUnit.MS),
    Duration(50, TimeUnit.MS),
    Duration(100, TimeUnit.MS),
    Duration(200, TimeUnit.MS),
    Duration(500, TimeUnit.MS),
    Duration(1, TimeUnit.S),
    Duration(2, TimeUnit.S)
]


@dataclass
class TimeScale:
    dT_per_division: Duration
    downsamplemerging: int
    downsample: int


class TriggerTypeModel(Enum):
    ON_RISING_EDGE = "Rising Edge"
    ON_FALLING_EDGE = "Falling Edge"
    EXTERNAL_SIGNAL = "External Signal"

    @staticmethod
    def value_of(value: str) -> "TriggerTypeModel":
        match value:
            case "Rising Edge":
                return TriggerTypeModel.ON_RISING_EDGE
            case "Falling Edge":
                return TriggerTypeModel.ON_FALLING_EDGE
            case "External Signal":
                return TriggerTypeModel.EXTERNAL_SIGNAL
            case _:
                raise RuntimeError(f"Unknown trigger type: {value}")

    @staticmethod
    def to_str(value: "TriggerTypeModel") -> str:
        return value.value

    def to_trigger_type(self) -> TriggerType:
        match self:
            case TriggerTypeModel.ON_RISING_EDGE:
                return TriggerType.ON_RISING_EDGE
            case TriggerTypeModel.ON_FALLING_EDGE:
                return TriggerType.ON_FALLING_EDGE
            case TriggerTypeModel.EXTERNAL_SIGNAL:
                return TriggerType.EXTERNAL
            case _:
                raise RuntimeError(f"Unknown trigger type: {self}")


class ChannelCouplingModel(Enum):
    AC = "AC"
    DC = "DC"

    @staticmethod
    def value_of(value: str) -> "ChannelCouplingModel":
        match value:
            case "AC":
                return ChannelCouplingModel.AC
            case "DC":
                return ChannelCouplingModel.DC
            case _:
                raise ValueError(f"Invalid channel coupling {value}")

    @staticmethod
    def to_str(value: "ChannelCouplingModel") -> str:
        return value.value


class ChannelImpedanceModel(Enum):
    FIFTY_OHM = "50 Ohm"
    ONE_MEGA_OHM = "1 MOhm"

    @staticmethod
    def value_of(value: str) -> "ChannelImpedanceModel":
        match value:
            case "50 Ohm":
                return ChannelImpedanceModel.FIFTY_OHM
            case "1 MOhm":
                return ChannelImpedanceModel.ONE_MEGA_OHM
            case _:
                raise ValueError(f"Invalid channel impedance {value}")

    @staticmethod
    def to_str(value: "ChannelImpedanceModel") -> str:
        return value.value


@dataclass
class SettableValue[V]:
    value: V
    setter: Callable[[V], V]


class ModelBase:
    def __init__(self, persistence: AppPersistence):
        self.persistence = persistence

    def get[T, V](
            self,
            xpath: str,
            clazz: Type[T],
            f_tr: Callable[[T], V] = lambda v: v,
            b_tr: Callable[[V], T] = lambda v: v
    ) -> SettableValue[V]:
        value = self.persistence.config.get_by_xpath(xpath, clazz)
        if value is None:
            raise RuntimeError(f"XPath {xpath} not found")
        real_value: V = f_tr(value)

        def setter(val: V) -> V:
            self.persistence.config.set_by_xpath(xpath, b_tr(val))
            return val

        return SettableValue(real_value, setter)


class ChannelModel(ModelBase):
    def __init__(self, parent, channel_num: int, persistence: AppPersistence):
        super().__init__(persistence)
        self.board_model: BoardModel = parent
        self.channel_num: int = channel_num

        self.__active = self.get(f"/channels/{channel_num}/active", bool)
        self.__color = self.get(f"/channels/{channel_num}/color", str)
        self.__offset_V = self.get(f"/channels/{channel_num}/offset_V", float)
        self.__dV = self.get(f"/channels/{channel_num}/dV", float)
        self.__coupling = self.get(
            f"/channels/{channel_num}/coupling", str, ChannelCouplingModel.value_of, ChannelCouplingModel.to_str
        )
        self.__impedance = self.get(
            f"/channels/{channel_num}/impedance", str, ChannelImpedanceModel.value_of, ChannelImpedanceModel.to_str
        )
        self.__ten_x_probe = self.get(f"/channels/{channel_num}/ten_x_probe", bool)
        self.__five_x_attenuation = self.get(f"/channels/{channel_num}/five_x_attenuation", bool)

    @property
    def active(self) -> bool:
        return self.__active.value

    @active.setter
    def active(self, value: bool):
        if self.__active.value != value:
            self.__active.value = self.__active.setter(value)
            self.board_model.on_channel_active_change()
        if self.channel_num == 1 and self.board_model.board is not None:
            self.board_model.board.enable_two_channels(value)

    @property
    def color(self) -> str:
        return self.__color.value

    @color.setter
    def color(self, value: str):
        self.__color.value = self.__color.setter(value)

    @property
    def offset_V(self) -> float:
        return self.__offset_V.value

    @offset_V.setter
    def offset_V(self, value: float):
        self.__offset_V.value = self.__offset_V.setter(value)
        if self.board_model.board is not None:
            self.__offset_V.value = self.board_model.board.set_channel_offset_V(self.channel_num, self.__offset_V.value)

    @property
    def dV(self) -> float:
        return self.__dV.value

    @dV.setter
    def dV(self, value: float):
        self.__dV.value = self.__dV.setter(value)
        if self.board_model.board is not None:
            self.__dV.value = self.board_model.board.set_channel_voltage_div(self.channel_num, self.__dV.value)

    @property
    def coupling(self) -> ChannelCouplingModel:
        return self.__coupling.value

    @coupling.setter
    def coupling(self, value: ChannelCouplingModel) -> None:
        self.__coupling.value = self.__coupling.setter(value)
        if self.board_model.board is not None:
            match value:
                case ChannelCouplingModel.AC:
                    self.board_model.board.set_channel_coupling(self.channel_num, ChannelCoupling.AC)
                case ChannelCouplingModel.DC:
                    self.board_model.board.set_channel_coupling(self.channel_num, ChannelCoupling.DC)
                case _:
                    raise RuntimeError(f"Invalid channel coupling {value}")

    @property
    def impedance(self) -> ChannelImpedanceModel:
        return self.__impedance.value

    @impedance.setter
    def impedance(self, value: ChannelImpedanceModel) -> None:
        self.__impedance.value = self.__impedance.setter(value)
        if self.board_model.board is not None:
            match value:
                case ChannelImpedanceModel.FIFTY_OHM:
                    self.board_model.board.set_channel_input_impedance(
                        channel=self.channel_num, impedance=InputImpedance.FIFTY_OHM
                    )
                case ChannelImpedanceModel.ONE_MEGA_OHM:
                    self.board_model.board.set_channel_input_impedance(
                        channel=self.channel_num, impedance=InputImpedance.ONE_MEGA_OHM
                    )
                case _:
                    raise RuntimeError(f"Invalid channel impedance value {value}")

    @property
    def ten_x_probe(self) -> bool:
        return self.__ten_x_probe.value

    @ten_x_probe.setter
    def ten_x_probe(self, value: bool):
        original_ten_x_probe_value = self.__ten_x_probe.value
        self.__ten_x_probe.value = self.__ten_x_probe.setter(value)
        if self.board_model.board is None:
            if original_ten_x_probe_value != value:
                if value:
                    self.__dV.value = self.__dV.value * 10
                else:
                    self.__dV.value = self.__dV.value / 10
        else:
            self.board_model.board.set_channel_10x_probe(self.channel_num, value)

    @property
    def five_x_attenuation(self) -> bool:
        return self.__five_x_attenuation.value

    @five_x_attenuation.setter
    def five_x_attenuation(self, value: bool):
        raise RuntimeError("This operation is to be removed")
        # self.__five_x_attenuation.value = self.__five_x_attenuation.setter(value)

    def get_demo_waveform(self) -> Waveform | None:
        if not self.active:
            return None
        else:
            x = [0.01 * i for i in range(-100, 3000)]
            offset = random()
            x_scale = 1 + 0.05 * random()
            y = [x_scale * t / 4 * math.sin(t * (1 + 0.1 * offset)) * (1 + 0.09 * math.sin(100 * t) * random()) for t in
                 x]
            return Waveform(0.01, y, trigger_pos=100, dV=1, trigger_level_V=0)


class TriggerModel(ModelBase):
    def __init__(self, parent, persistence: AppPersistence):
        super().__init__(persistence)
        self.board_model: BoardModel = parent

        self.__on_channel = self.get("/trigger/on_channel", int)
        self.__trigger_type = self.get(
            "/trigger/trigger_type", str, TriggerTypeModel.value_of, TriggerTypeModel.to_str
        )
        self.__tot = self.get("/trigger/tot", int)
        self.__delta = self.get("/trigger/delta", int)
        self.__level = self.get("/trigger/level", float)
        self.__position = self.get("/trigger/position", float)
        self.__auto_frequency = self.get("/trigger/auto_frequency", str)
        self.__max_dt_between_auto_trig_s = self.__auto_freq_to_dt(self.__auto_frequency.value)

        # Used only when running without a board in demo mode
        self._model_trigger_type = TriggerType.DISABLED

    def update_live_trigger_properties(self):
        if self.board_model.board is not None:
            self.__level.value = self.board_model.board.set_trigger_props(
                trigger_level=self.level,
                trigger_delta=self.delta,
                trigger_pos=self.position,
                tot=self.tot,
                trigger_on_channel=self.__on_channel.value
            )
            self.__position.value = self.board_model.board.state.trigger_pos

    def __auto_freq_to_dt(self, freq_str: str) -> float:
        match freq_str:
            case "2 Hz":
                return 0.5
            case "5 Hz":
                return 0.2
            case "10 Hz":
                return 0.1
            case _:
                return 0.5

    @property
    def auto_frequency(self) -> str:
        return self.__auto_frequency.value

    @auto_frequency.setter
    def auto_frequency(self, value: str):
        self.__auto_frequency.value = self.__auto_frequency.setter(value)
        self.__max_dt_between_auto_trig_s = self.__auto_freq_to_dt(self.__auto_frequency.value)

    @property
    def max_dt_auto_trig_s(self) -> float:
        return self.__max_dt_between_auto_trig_s

    @property
    def on_channel(self) -> int:
        return self.__on_channel.value

    @on_channel.setter
    def on_channel(self, value: int):
        self.__on_channel.value = self.__on_channel.setter(value)
        self.update_live_trigger_properties()

    @property
    def trigger_type(self) -> TriggerTypeModel:
        return self.__trigger_type.value

    @trigger_type.setter
    def trigger_type(self, value: TriggerTypeModel):
        self.__trigger_type.value = self.__trigger_type.setter(value)

    @property
    def tot(self) -> int:
        return self.__tot.value

    @tot.setter
    def tot(self, value: int):
        self.__tot.value = self.__tot.setter(value)
        self.update_live_trigger_properties()

    @property
    def delta(self) -> int:
        return self.__delta.value

    @delta.setter
    def delta(self, value: int):
        self.__delta.value = self.__delta.setter(value)
        self.update_live_trigger_properties()

    @property
    def level(self) -> float:
        return self.__level.value

    @level.setter
    def level(self, value: float):
        self.__level.value = self.__level.setter(value)
        self.update_live_trigger_properties()

    @property
    def position(self) -> float:
        return self.__position.value

    @property
    def position_live(self) -> float:
        if self.board_model.board is None:
            return self.__position.value
        else:
            return self.board_model.board.state.trigger_pos_live

    @position.setter
    def position(self, value: float):
        self.__position.value = self.__position.setter(value)
        self.update_live_trigger_properties()

    def force_arm_trigger(self, trigger_type: TriggerType) -> bool:
        if self.board_model.board is None:
            if trigger_type != TriggerType.DISABLED:
                self._model_trigger_type = trigger_type
            return True
        else:
            return self.board_model.board.force_arm_trigger(trigger_type)


class BoardModel(ModelBase):
    # TODO: Remove these constants and reuse them from HaasoscopeProPy
    VALID_DOWNSAMPLEMERGIN_VALUES_ONE_CHANNEL = [1, 2, 4, 8, 20, 40]
    VALID_DOWNSAMPLEMERGIN_VALUES_TWO_CHANNELS = [1, 2, 4, 10, 20]
    NATIVE_SAMPLE_PERIOD_S = 3.125e-10

    def __init__(self, persistence: AppPersistence):
        super().__init__(persistence)
        self.channel = [ChannelModel(self, 0, persistence), ChannelModel(self, 1, persistence)]
        self.trigger = TriggerModel(self, persistence)

        self.__highres = self.get("/general/highres", bool)
        self.__mem_depth = self.get("/general/mem_depth", int)
        self.__delay = self.get("/general/delay", int)
        self.__f_delay = self.get("/general/f_delay", int)

        self.on_memdepth_change: Callable[[], None] = lambda: None
        self.on_channel_active_change: Callable[[], None] = lambda: None
        self.board: Board | None = None

        self.__visual_time_scale = Duration.value_of(
            self.persistence.config.get_by_xpath("/general/visual_time_scale", str)
        )
        self.__demo_last_time_waveform_available = time.time()
        self.__time_scale = Duration.value_of("0s")
        self.checkpoint: SceneCheckpoint | None = None
        self.cached_waveforms: tuple[Optional[Waveform], Optional[Waveform]] = (None, None)

    def cleanup(self):
        if self.board is not None:
            self.board.cleanup()

    def link_to_live_board(self, board: Board):
        self.board = board

    @property
    def time_scale(self) -> Duration:
        return self.__time_scale

    @time_scale.setter
    def time_scale(self, value: Duration):
        if self.board is not None:
            value = (self.board.set_time_scale(value) * self.board.num_samples_per_division()).optimize()

        self.__time_scale = value

    @property
    def visual_time_scale(self) -> Duration:
        return self.__visual_time_scale

    @visual_time_scale.setter
    def visual_time_scale(self, value: Duration):
        self.__visual_time_scale = value
        self.persistence.config.set_by_xpath("/general/visual_time_scale", f"{self.__visual_time_scale}")

    @property
    def highres(self) -> bool:
        return self.__highres.value

    @highres.setter
    def highres(self, value: bool):
        self.__highres.value = self.__highres.setter(value)
        if self.board is not None:
            self.board.set_highres_capture_mode(value)

    @property
    def mem_depth(self) -> int:
        return self.__mem_depth.value

    @mem_depth.setter
    def mem_depth(self, value: int):
        if self.mem_depth != value:
            self.__mem_depth.value = self.__mem_depth.setter(value)
            self.on_memdepth_change()
            if self.board is not None:
                self.board.set_memory_depth(value)

    @property
    def delay(self) -> int:
        return self.__delay.value

    @delay.setter
    def delay(self, value: int):
        self.__delay.value = self.__delay.setter(value)
        # TODO: Add control in live board API
        self.board

    @property
    def f_delay(self) -> int:
        return self.__f_delay.value

    @f_delay.setter
    def f_delay(self, value: int):
        self.__f_delay.value = self.__f_delay.setter(value)
        # TODO: Add control in live board API

    def _get_first_valid_time_scale(self) -> Duration:
        return self.get_next_valid_time_scale(
            two_channel_operation=self.channel[1].active,
            mem_depth=self.mem_depth,
            current_value=Duration.value_of("0 s"),
            index_offset=0
        )

    @cache
    def get_next_valid_time_scale(
            self,
            two_channel_operation: int,
            mem_depth: int,
            current_value: Duration,
            index_offset: int
    ) -> Duration:
        valid_values: list[Duration] = self.get_valid_time_scales(two_channel_operation, mem_depth)

        def current_index():
            for i, d in enumerate(valid_values):
                if d >= current_value:
                    return i
            return 0

        current_index = current_index()
        next_index = min(max(current_index + index_offset, 0), len(valid_values) - 1)
        return valid_values[next_index]

    @cache
    def get_valid_time_scales(self, two_channel_operation: int, mem_depth: int) -> list[Duration]:
        """
        Returns list of valid durations for horizontal division. This is intended to be used
        in GUI to construct valid time base element.
        """
        samples_per_row_per_waveform = 20 if two_channel_operation else 40
        num_samples_per_division = samples_per_row_per_waveform * mem_depth / 10

        if two_channel_operation:
            return [(a[2] * num_samples_per_division).optimize() for a in TimeConstants.dt_two_ch]
        else:
            return [(a[2] * num_samples_per_division).optimize() for a in TimeConstants.dt_one_ch]

    @cache
    def get_time_scale_from_board_parameters(
            self,
            two_channel_operation: int,
            mem_depth: int,
            downsample: int,
            downsamplemerging: int
    ) -> Duration:
        samples_per_row_per_waveform = 20 if two_channel_operation else 40
        num_samples_per_division = samples_per_row_per_waveform * mem_depth / 10
        dt_s = BoardModel.NATIVE_SAMPLE_PERIOD_S * downsamplemerging * pow(2, downsample)
        return Duration.value_of(f"{dt_s * num_samples_per_division} s").optimize()

    @cache
    def get_valid_offset_values(self, dV: float, do_oversample: bool) -> list[MetricValue]:
        scaling = 1.5 * dV / 160 * (2 if do_oversample else 1)  # compare to 0 dB gain
        return [MetricValue.value_of(f"{scaling * n} V").optimize() for n in range(-990, 990, 10)]

    @cache
    def get_next_valid_offset_value(
            self,
            dV: float,
            do_oversample: bool,
            current_offset: MetricValue,
            index_offset: int
    ) -> MetricValue:
        valid_values: list[MetricValue] = self.get_valid_offset_values(dV, do_oversample)

        def current_index():
            for i, d in enumerate(valid_values):
                if d >= current_offset:
                    return i
            return 0

        current_index = current_index()
        next_index = min(max(current_index + index_offset, 0), len(valid_values) - 1)
        return valid_values[next_index]

    @cache
    def get_valid_dv_values(self, do_oversample: bool, ten_x_probe: bool) -> list[MetricValue]:
        if ten_x_probe:
            return [
                MetricValue.value_of("4 V"), MetricValue.value_of("2 V"), MetricValue.value_of("1 V"),
                MetricValue.value_of("500 mV"), MetricValue.value_of("250 mV"), MetricValue.value_of("100 mV")
            ]
        else:
            return [
                MetricValue.value_of("400 mV"), MetricValue.value_of("200 mV"), MetricValue.value_of("100 mV"),
                MetricValue.value_of("50 mV"), MetricValue.value_of("25 mV"), MetricValue.value_of("10 mV")
            ]

    @cache
    def get_next_valid_voltage_scale(
            self,
            current_voltage_scale: MetricValue,
            do_oversample: bool,
            ten_x_probe: bool,
            index_offset: int
    ) -> MetricValue:
        valid_values: list[MetricValue] = self.get_valid_dv_values(do_oversample, ten_x_probe)

        def current_index():
            for i, d in enumerate(valid_values):
                if d <= current_voltage_scale:
                    return i
            return 0

        current_index = current_index()
        next_index = min(max(current_index + index_offset, 0), len(valid_values) - 1)
        return valid_values[next_index]

    def init_board_from_model(self) -> None:
        if self.board is not None:
            # Our auto trigger does not rely on rolling trigger section in the firmware; hence we disable it.
            # Later this code should be removed after corresponding block in the firmware deleted.
            self.board.comm.set_rolling(False)

            # set last memory depth
            self.board.state.expect_samples = self.mem_depth

            # Following seemingly meaningless code will trigger board write operations if live board is connected.

            self.highres = self.highres
            self.mem_depth = self.mem_depth
            self.delay = self.delay
            self.f_delay = self.f_delay

            board_dt_per_division = self.get_next_valid_time_scale(
                two_channel_operation=self.channel[1].active,
                mem_depth=self.mem_depth,
                current_value=self.visual_time_scale,
                index_offset=0
            )
            self.time_scale = board_dt_per_division
            self.trigger.position = self.trigger.position
            self.trigger.update_live_trigger_properties()
            for ch in self.channel:
                ch.active = ch.active

            for ch in self.channel:
                ch.offset_V = ch.offset_V
                ch.dV = ch.dV
                ch.coupling = ch.coupling
                ch.impedance = ch.impedance
                ch.ten_x_probe = ch.ten_x_probe

    def is_capture_available(self) -> WaveformAvailability:
        if self.board is None:
            match self.trigger._model_trigger_type:
                case TriggerType.AUTO:
                    return WaveformAvailable(0)
                case TriggerType.DISABLED:
                    return WaveformUnavailable()
                case _:
                    c_time = time.time()
                    if c_time - self.__demo_last_time_waveform_available > 1:
                        self.__demo_last_time_waveform_available = c_time
                        return WaveformAvailable(0)
                    else:
                        return WaveformUnavailable()
        else:
            return self.board.wait_for_waveform(0)

    def get_checkpoint_waveforms(self) -> tuple[Optional[Waveform], Optional[Waveform]]:
        if self.checkpoint is None:
            return None, None
        else:
            waveforms = []
            for cdata in self.checkpoint.channels:
                if not cdata.active:
                    waveforms.append(None)
                else:

                    waveforms.append(Waveform(
                        dt_s=cdata.dt_s,
                        vs=cdata.v,

                        # the rest is ignored for plotting
                        trigger_pos=0,
                        dV=0,
                        trigger_level_V=0
                    ))
            return tuple(waveforms)

    def get_waveforms(self, use_last_shown_waveform: bool = False) -> tuple[Optional[Waveform], Optional[Waveform]]:
        if not use_last_shown_waveform:
            self.cached_waveforms = self.__get_waveforms()
        return self.cached_waveforms

    def __get_waveforms(self) -> tuple[Optional[Waveform], Optional[Waveform]]:
        if self.board is None:
            return self.channel[0].get_demo_waveform(), self.channel[0].get_demo_waveform()
        else:
            ws = self.board.get_waveforms()
            retval: list[Optional[Waveform]] = []
            for i, c in enumerate(self.channel):
                if c.active:
                    retval.append(ws[i])
                else:
                    retval.append(None)
            return tuple(retval)

    @cache
    def get_next_valid_visual_time_scale(self, current_value: Duration, index_offset: int) -> Duration:
        def current_index():
            for i, d in enumerate(VISUAL_TIME_PER_DIVISION):
                if d >= current_value:
                    return i
            return 0

        current_index = current_index()
        next_index = min(max(current_index + index_offset, 0), len(VISUAL_TIME_PER_DIVISION) - 1)
        return VISUAL_TIME_PER_DIVISION[next_index]
