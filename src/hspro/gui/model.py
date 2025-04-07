from dataclasses import dataclass
from enum import Enum
from functools import cache
from typing import Type, Callable

from sprats.config import AppPersistence
from unlib import Duration


@dataclass
class TimeScale:
    dT_per_division: Duration
    downsamplemerging: int
    downsample: int


class TriggerTypeModel(Enum):
    ON_RISING_EDGE = "Rising Edge"
    ON_FALLING_EDGE = "Falling Edge"

    @staticmethod
    def value_of(value: str) -> "TriggerTypeModel":
        match value:
            case "Rising Edge":
                return TriggerTypeModel.ON_RISING_EDGE
            case "Falling Edge":
                return TriggerTypeModel.ON_FALLING_EDGE
            case _:
                raise RuntimeError(f"Unknown trigger type: {value}")

    @staticmethod
    def to_str(value: "TriggerTypeModel") -> str:
        return value.value


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
        self.parent: BoardModel = parent

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
            self.parent.on_channel_active_change()

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

    @property
    def dV(self) -> float:
        return self.__dV.value

    @dV.setter
    def dV(self, value: float):
        self.__dV.value = self.__dV.setter(value)

    @property
    def coupling(self) -> ChannelCouplingModel:
        return self.__coupling.value

    @coupling.setter
    def coupling(self, value: ChannelCouplingModel) -> None:
        self.__coupling.value = self.__coupling.setter(value)

    @property
    def impedance(self) -> ChannelImpedanceModel:
        return self.__impedance.value

    @impedance.setter
    def impedance(self, value: ChannelImpedanceModel) -> None:
        self.__impedance.value = self.__impedance.setter(value)

    @property
    def ten_x_probe(self) -> bool:
        return self.__ten_x_probe.value

    @ten_x_probe.setter
    def ten_x_probe(self, value: bool):
        self.__ten_x_probe.value = self.__ten_x_probe.setter(value)

    @property
    def five_x_attenuation(self) -> bool:
        return self.__five_x_attenuation.value

    @five_x_attenuation.setter
    def five_x_attenuation(self, value: bool):
        self.__five_x_attenuation.value = self.__five_x_attenuation.setter(value)


class TriggerModel(ModelBase):
    def __init__(self, persistence: AppPersistence):
        super().__init__(persistence)

        self.__on_channel = self.get("/trigger/on_channel", int)
        self.__trigger_type = self.get(
            "/trigger/trigger_type", str, TriggerTypeModel.value_of, TriggerTypeModel.to_str
        )
        self.__tot = self.get("/trigger/tot", int)
        self.__delta = self.get("/trigger/delta", int)
        self.__level = self.get("/trigger/level", float)
        self.__position = self.get("/trigger/position", float)

    @property
    def on_channel(self) -> int:
        return self.__on_channel.value

    @on_channel.setter
    def on_channel(self, value: int):
        self.__on_channel.value = self.__on_channel.setter(value)

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

    @property
    def delta(self) -> int:
        return self.__delta.value

    @delta.setter
    def delta(self, value: int):
        self.__delta.value = self.__delta.setter(value)

    @property
    def level(self) -> float:
        return self.__level.value

    @level.setter
    def level(self, value: float):
        self.__level.value = self.__level.setter(value)

    @property
    def position(self) -> float:
        return self.__position.value

    @position.setter
    def position(self, value: float):
        self.__position.value = self.__position.setter(value)


class BoardModel(ModelBase):
    # TODO: Remove these constants and reuse them from HaasoscopeProPy
    VALID_DOWNSAMPLEMERGIN_VALUES_ONE_CHANNEL = [1, 2, 4, 8, 20, 40]
    VALID_DOWNSAMPLEMERGIN_VALUES_TWO_CHANNELS = [1, 2, 4, 10, 20]
    NATIVE_SAMPLE_PERIOD_S = 3.125e-10

    def __init__(self, persistence: AppPersistence):
        super().__init__(persistence)
        self.channel = [ChannelModel(self, 1, persistence), ChannelModel(self, 2, persistence)]
        self.trigger = TriggerModel(persistence)

        self.__highres = self.get(f"/general/highres", bool)
        self.__mem_depth = self.get(f"/general/mem_depth", int)
        self.__delay = self.get(f"/general/delay", int)
        self.__f_delay = self.get(f"/general/f_delay", int)

        self.on_memdepth_change: Callable[[], None] = lambda: None
        self.on_channel_active_change: Callable[[], None] = lambda: None

    @property
    def highres(self) -> bool:
        return self.__highres.value

    @highres.setter
    def highres(self, value: bool):
        self.__highres.value = self.__highres.setter(value)

    @property
    def mem_depth(self) -> int:
        return self.__mem_depth.value

    @mem_depth.setter
    def mem_depth(self, value: int):
        if self.mem_depth != value:
            self.__mem_depth.value = self.__mem_depth.setter(value)
            self.on_memdepth_change()

    @property
    def delay(self) -> int:
        return self.__delay.value

    @delay.setter
    def delay(self, value: int):
        self.__delay.value = self.__delay.setter(value)

    @property
    def f_delay(self) -> int:
        return self.__f_delay.value

    @f_delay.setter
    def f_delay(self, value: int):
        self.__f_delay.value = self.__f_delay.setter(value)

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

        def get_valid_downsamplemergin_values():
            if two_channel_operation:
                return BoardModel.VALID_DOWNSAMPLEMERGIN_VALUES_TWO_CHANNELS
            else:
                return BoardModel.VALID_DOWNSAMPLEMERGIN_VALUES_ONE_CHANNEL

        valid_downsamplemergin_values = get_valid_downsamplemergin_values()

        results = []
        for downsample in range(32):
            for downsamplemerging in valid_downsamplemergin_values:
                dt_s = BoardModel.NATIVE_SAMPLE_PERIOD_S * downsamplemerging * pow(2, downsample)
                results.append(Duration.value_of(f"{dt_s * num_samples_per_division} s").optimize())
        results = list(set(results))
        results.sort()
        return results

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
