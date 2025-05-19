from dataclasses import dataclass


@dataclass
class ChannelData:
    active: bool
    color: str
    offset_V: float
    dV: float
    coupling: str
    impedance: str
    ten_x_probe: bool
    t_s_0: float
    dt_s: float
    v: list[float]

    @classmethod
    def value_of(cls, json_data) -> "ChannelData":
        return ChannelData(
            active=json_data["active"],
            color=json_data["color"],
            offset_V=json_data["offset_V"],
            dV=json_data["dV"],
            coupling=json_data["coupling"],
            impedance=json_data["impedance"],
            ten_x_probe=json_data["ten_x_probe"],
            t_s_0=json_data["t_s_0"],
            dt_s=json_data["dt_s"],
            v=json_data["v"],
        )


@dataclass
class SceneCheckpoint:
    plot_color_scheme: str
    show_trigger_level_line: bool
    show_trigger_position_line: bool
    show_grid: bool
    show_y_axis_labels: bool
    show_zero_line: bool

    highres: bool
    mem_depth: int
    delay: int
    f_delay: int
    visual_time_scale: str

    trigger_on_channel: int
    trigger_type: str
    trigger_tot: int
    trigger_delta: int
    trigger_level: float
    trigger_position: float
    trigger_auto_frequency: str

    selected_channel: int

    channels: list[ChannelData]

    @classmethod
    def value_of(cls, json_data) -> "SceneCheckpoint":
        return SceneCheckpoint(
            plot_color_scheme=json_data["plot_color_scheme"],
            show_trigger_level_line=json_data["show_trigger_level_line"],
            show_trigger_position_line=json_data["show_trigger_position_line"],
            show_grid=json_data["show_grid"],
            show_y_axis_labels=json_data["show_y_axis_labels"],
            show_zero_line=json_data["show_zero_line"],
            highres=json_data["highres"],
            mem_depth=json_data["mem_depth"],
            delay=json_data["delay"],
            f_delay=json_data["f_delay"],
            visual_time_scale=json_data["visual_time_scale"],
            trigger_on_channel=json_data["trigger_on_channel"],
            trigger_type=json_data["trigger_type"],
            trigger_tot=json_data["trigger_tot"],
            trigger_delta=json_data["trigger_delta"],
            trigger_level=json_data["trigger_level"],
            trigger_position=json_data["trigger_position"],
            trigger_auto_frequency=json_data["trigger_auto_frequency"],
            selected_channel=json_data["selected_channel"],
            channels=[ChannelData.value_of(cd) for cd in json_data["channels"]],
        )


@dataclass
class Scene:
    name: str
    version: int
    data: list[SceneCheckpoint]

    @classmethod
    def value_of(cls, json_data) -> "Scene":
        return Scene(
            name=json_data["name"],
            version=json_data["version"],
            data=[SceneCheckpoint.value_of(sc) for sc in json_data["data"]]
        )
