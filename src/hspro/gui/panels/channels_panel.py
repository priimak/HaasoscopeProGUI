from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QMouseEvent
from PySide6.QtWidgets import QSpacerItem, QDoubleSpinBox, QColorDialog
from pytide6 import VBoxPanel, CheckBox, ComboBox, Label, HBoxPanel, W
from unlib import MetricValue, Scale

from hspro.gui.app import App, WorkerMessage
from hspro.gui.model import ChannelCouplingModel, ChannelImpedanceModel


class VperDivSpinner(QDoubleSpinBox):
    def __init__(self, channel: int, app: App):
        super().__init__()
        self.channel = channel
        self.app = app
        self.setMinimum(0)
        self.setMaximum(1000)
        self.setDecimals(0)
        self.voltage_per_division = MetricValue.value_of(f"{app.model.channel[channel].dV} V").optimize()
        self.setValue(self.voltage_per_division.value)
        self.setSuffix(f" {self.voltage_per_division.scale.to_str()}V/div")

    def stepBy(self, steps):
        self.voltage_per_division = self.app.model.get_next_valid_voltage_scale(
            current_voltage_scale=self.voltage_per_division,
            do_oversample=False,
            ten_x_probe=self.app.model.channel[self.channel].ten_x_probe,
            index_offset=-steps
        )
        self.app.worker.messages.put(
            WorkerMessage.SetVoltagePerDiv(self.channel, self.voltage_per_division.to_float(Scale.UNIT)))

        # read it back is it might have changed/clipped in the board
        # self.voltage_per_division = MetricValue.value_of(f"{self.app.model.channel[self.channel].dV} V").optimize()
        self.setValue(self.voltage_per_division.value)
        self.setSuffix(f" {self.voltage_per_division.scale.to_str()}V/div")


class VoltageOffsetSpinner(QDoubleSpinBox):
    def __init__(self, channel: int, app: App):
        super().__init__()
        self.channel = channel
        self.app = app
        # self.setDecimals(4)
        self.setValue(app.model.channel[channel].offset_V)

    def stepBy(self, steps):
        new_val = self.value() + (steps * 0.1)
        self.app.model.channel[self.channel].offset_V = new_val
        self.setValue(new_val)


class ChannelsPanel(VBoxPanel):
    min_width = 230

    def __init__(self, app: App):
        super().__init__(margins=0)
        self.app = app

        for channel in app.channels:
            channel_name = f"Ch #{channel}"

            channel_color_selector = Label(" ")
            channel_color_selector.setMinimumWidth(100)
            channel_color_selector.setMaximumWidth(100)

            def mk_color_selector(color_selector: Label):
                def select_color(ev: QMouseEvent):
                    cdialog = QColorDialog(self)
                    cdialog.setCurrentColor(app.model.channel[color_selector.channel].color)
                    if cdialog.exec_():
                        new_color = cdialog.currentColor().name()
                        color_selector.setStyleSheet(
                            f"background-color: {new_color}; border: 1px solid black;"
                        )
                        color_selector.color = new_color
                        app.model.channel[color_selector.channel].color = new_color
                        app.set_channel_color(color_selector.channel, new_color)
                        app.update_trigger_lines_color()

                return select_color

            channel_color_selector.mousePressEvent = mk_color_selector(channel_color_selector)
            channel_color_selector.setStyleSheet(
                f"background-color:{app.model.channel[channel].color}; border: 1px solid black;"
            )
            channel_color_selector.channel = channel

            vdiv = VperDivSpinner(channel, app)
            voffset = VoltageOffsetSpinner(channel, app)
            voffset.setEnabled(False)  # TODO: Re-enable me

            channel_config_panel = VBoxPanel(widgets=[
                HBoxPanel(widgets=[vdiv, W(Label("Scale"), stretch=10)], margins=0),
                HBoxPanel(widgets=[voffset, W(Label("V (Offset)"), stretch=10)], margins=0),
                HBoxPanel(
                    widgets=[
                        ComboBox(
                            items=[ChannelCouplingModel.DC.value, ChannelCouplingModel.AC.value],
                            current_selection=app.model.channel[channel].coupling.value,
                            min_width=100,
                            on_text_change=self.coupling_change_callback(channel),
                        ),
                        Label("Coupling"),
                        QSpacerItem
                    ],
                    margins=0
                ),
                HBoxPanel(
                    widgets=[
                        ComboBox(
                            items=[ChannelImpedanceModel.FIFTY_OHM.value, ChannelImpedanceModel.ONE_MEGA_OHM.value],
                            current_selection=app.model.channel[channel].impedance.value,
                            min_width=100,
                            on_text_change=self.impedance_change_callback(channel),
                        ),
                        Label("Impedance"),
                        QSpacerItem
                    ],
                    margins=0
                ),
                HBoxPanel(widgets=[
                    CheckBox(on_change=self.ten_x_callback(channel), checked=app.model.channel[channel].ten_x_probe),
                    W(Label("10x probe"), stretch=10, alignment=Qt.AlignmentFlag.AlignLeft)
                ], margins=(0, 5, 0, 0)),
                # HBoxPanel(widgets=[
                #     CheckBox(
                #         on_change=self.five_x_callback(channel), checked=app.model.channel[channel].five_x_attenuation
                #     ),
                #     W(Label("5x attenuation"), stretch=10, alignment=Qt.AlignmentFlag.AlignLeft)
                # ], margins=(0, 5, 0, 0)),
            ])

            channel_panel = VBoxPanel(widgets=[
                HBoxPanel([Label(channel_name), channel_color_selector], margins=0),
                CheckBox(
                    "Active",
                    on_change=self.channel_active_callback(channel, channel_config_panel),
                    checked=app.model.channel[channel].active
                ),
                channel_config_panel]
            )
            if not app.model.channel[channel].active:
                channel_config_panel.setVisible(False)
            channel_panel.setMinimumWidth(ChannelsPanel.min_width)

            channel_panel.setObjectName("ChannelPanel")
            channel_panel.setAutoFillBackground(True)
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, "lightblue")
            channel_panel.setPalette(palette)
            self.layout().addWidget(channel_panel)

        self.layout().addStretch(10)

    def channel_active_callback(self, channel: int, channel_config_panel: VBoxPanel) -> Callable[[bool], None]:
        def channel_active(active: bool):
            self.app.worker.messages.put(WorkerMessage.SetChannelActive(channel, active))
            channel_config_panel.setVisible(active)
            self.app.set_channel_active_state(channel, active)

        return channel_active

    def ten_x_callback(self, channel: int) -> Callable[[bool], None]:
        def ten_x_probe(active: bool):
            self.app.worker.messages.put(WorkerMessage.SetChannel10x(channel, ten_x=active))

        return ten_x_probe

    def five_x_callback(self, channel: int) -> Callable[[bool], None]:
        def five_x_probe(attenuation: bool):
            self.app.model.channel[channel].five_x_attenuation = attenuation

        return five_x_probe

    def coupling_change_callback(self, channel: int) -> Callable[[str], None]:
        def coupling_change(coupling: str):
            self.app.model.channel[channel].coupling = ChannelCouplingModel.value_of(coupling)

        return coupling_change

    def impedance_change_callback(self, channel: int) -> Callable[[str], None]:
        def impedance_change(impedance: str):
            self.app.model.channel[channel].impedance = ChannelImpedanceModel.value_of(impedance)

        return impedance_change
