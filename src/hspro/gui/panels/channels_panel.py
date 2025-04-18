from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QMouseEvent
from PySide6.QtWidgets import QSpacerItem, QDoubleSpinBox, QColorDialog
from pytide6 import VBoxPanel, CheckBox, ComboBox, Label, HBoxPanel, W
from unlib import MetricValue, Scale

from hspro.gui.app import App, WorkerMessage
from hspro.gui.buttons import ZeroButton
from hspro.gui.model import ChannelCouplingModel, ChannelImpedanceModel


class VperDivSpinner(QDoubleSpinBox):
    def __init__(self, channel: int, app: App):
        super().__init__()
        self.channel = channel
        self.app = app
        self.setMinimum(0)
        self.setMaximum(1000)
        self.setMaximumWidth(200)
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
            WorkerMessage.SetVoltagePerDiv(self.channel, self.voltage_per_division.to_float(Scale.UNIT))
        )

        self.setValue(self.voltage_per_division.value)
        self.setSuffix(f" {self.voltage_per_division.scale.to_str()}V/div")

    def update_due_to_10x_change(self):
        if self.app.model.channel[self.channel].ten_x_probe:
            self.voltage_per_division *= 10
        else:
            self.voltage_per_division /= 10
        self.setValue(self.voltage_per_division.value)
        self.setSuffix(f" {self.voltage_per_division.scale.to_str()}V/div")


class VoltageOffsetSpinner(QDoubleSpinBox):
    def __init__(self, channel: int, app: App):
        super().__init__()
        self.channel = channel
        self.app = app
        self.setMinimum(-1_000_000_000)
        self.setMaximum(1_000_000_000)
        self.setDecimals(2)
        self.setMaximumWidth(120)
        self.offset = MetricValue.value_of(f"{app.model.channel[channel].offset_V} V").optimize()
        self.setValue(self.offset.value)
        self.setSuffix(f" {self.offset.scale.to_str()}V")

    def stepBy(self, steps):
        self.offset: MetricValue = self.app.model.get_next_valid_offset_value(
            dV=self.app.model.channel[self.channel].dV,
            do_oversample=False,
            current_offset=self.offset,
            index_offset=steps
        )
        self.app.worker.messages.put(WorkerMessage.SetChannelOffset(self.channel, self.offset.to_float(Scale.UNIT)))
        self.setValue(self.offset.value)
        self.setSuffix(f" {self.offset.scale.to_str()}V")

    def resetToZero(self):
        self.offset = MetricValue.value_of("0 V")
        self.setValue(self.offset.value)
        self.setSuffix(f" {self.offset.scale.to_str()}V")
        self.app.worker.messages.put(WorkerMessage.SetChannelOffset(self.channel, 0))

    def correctOffsetValue(self):
        offset_V = self.app.model.channel[self.channel].offset_V
        self.offset: MetricValue = self.app.model.get_next_valid_offset_value(
            dV=self.app.model.channel[self.channel].dV,
            do_oversample=False,
            current_offset=MetricValue.value_of(f"{offset_V} V"),
            index_offset=0
        )
        self.setValue(self.offset.value)
        self.setSuffix(f" {self.offset.scale.to_str()}V")


class ChannelsPanel(VBoxPanel):
    min_width = 230

    def __init__(self, app: App):
        super().__init__(margins=0)
        self.app = app

        vdiv_spinners = []
        offset_spinners = []
        for channel in app.channels:
            channel_name = f"Ch #{channel}"

            channel_color_selector = Label(" ")
            channel_color_selector.setMinimumWidth(100)
            channel_color_selector.setMaximumWidth(100)

            def mk_color_selector(color_selector: Label, channel: int):
                def select_color(ev: QMouseEvent):
                    cdialog = QColorDialog(self)
                    cdialog.setCurrentColor(app.model.channel[channel].color)
                    if cdialog.exec_():
                        new_color = cdialog.currentColor().name()
                        color_selector.setStyleSheet(
                            f"background-color: {new_color}; border: 1px solid black;"
                        )
                        color_selector.color = new_color
                        app.model.channel[channel].color = new_color
                        app.set_channel_color(channel, new_color)
                        app.update_trigger_lines_color(app.model.trigger.on_channel)

                return select_color

            channel_color_selector.mousePressEvent = mk_color_selector(channel_color_selector, channel)
            channel_color_selector.setStyleSheet(
                f"background-color:{app.model.channel[channel].color}; border: 1px solid black;"
            )
            channel_color_selector.channel = channel

            vdiv = VperDivSpinner(channel, app)
            vdiv_spinners.append(vdiv)
            voffset = VoltageOffsetSpinner(channel, app)
            offset_spinners.append(voffset)

            channel_config_panel = VBoxPanel(widgets=[
                HBoxPanel(widgets=[vdiv, W(Label("Scale"), stretch=10)], margins=0),
                HBoxPanel(
                    widgets=[voffset, ZeroButton(voffset.resetToZero), W(Label("Offset"), stretch=10)],
                    margins=0
                ),
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
        self.app.correct_offset = lambda channel: offset_spinners[channel].correctOffsetValue()
        self.app.correct_dV = lambda channel: vdiv_spinners[channel].update_due_to_10x_change()

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

    def coupling_change_callback(self, channel: int) -> Callable[[str], None]:
        def coupling_change(coupling: str):
            self.app.worker.messages.put(
                WorkerMessage.SetChannelCoupling(channel, ChannelCouplingModel.value_of(coupling))
            )

        return coupling_change

    def impedance_change_callback(self, channel: int) -> Callable[[str], None]:
        def impedance_change(impedance: str):
            self.app.model.channel[channel].impedance = ChannelImpedanceModel.value_of(impedance)

        return impedance_change
