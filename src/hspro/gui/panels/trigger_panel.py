from threading import Lock

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QSpacerItem, QSlider, QLabel
from pytide6 import VBoxPanel, VBoxLayout, PushButton, Label, HBoxPanel, ComboBox, W

from hspro.gui.app import App, WorkerMessage
from hspro.gui.buttons import ZeroButton
from hspro.gui.model import TriggerTypeModel


class TrigLevelSlider(QSlider):
    def __init__(self, app: App):
        super().__init__(Qt.Orientation.Vertical)
        self.app = app

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        self.app.make_trig_level_line_visible_temp(True)

    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)
        self.app.make_trig_level_line_visible_temp(False)


class TrigPosSlider(QSlider):
    def __init__(self, app: App):
        super().__init__(Qt.Orientation.Horizontal)
        self.app = app

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        self.app.make_trig_pos_line_visible_temp(True)

    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)
        self.app.make_trig_pos_line_visible_temp(False)


class TriggerPanel(VBoxPanel):
    def __init__(self, app: App):
        super().__init__()
        self.app = app

        layout: VBoxLayout = self.layout()

        self.selected_button: str = "Stop"
        self.selected_button_lock = Lock()

        self.stop_button = PushButton("Stop")
        self.single_button = PushButton("Single")
        self.normal_button = PushButton("Normal")
        self.auto_button = PushButton("Auto")
        self.force_acq_button = PushButton("Force Acq")

        self.set_button_active_appearance(self.stop_button)
        self.stop_button.clicked.connect(self.disarm)
        self.single_button.clicked.connect(self.arm_single)
        self.normal_button.clicked.connect(self.arm_normal)
        self.auto_button.clicked.connect(self.arm_auto)
        self.force_acq_button.clicked.connect(self.arm_force_acq)

        # layout.addWidget(Label("Trigger"))
        t_buttons = HBoxPanel(widgets=[
            W(
                VBoxPanel(
                    widgets=[
                        Label("Trigger"),
                        self.stop_button, self.single_button, self.normal_button,
                        self.auto_button, self.force_acq_button
                    ],
                    margins=0
                ),
                alignment=Qt.AlignmentFlag.AlignLeft
            ),
            QSpacerItem
        ], margins=0)
        main_panel = VBoxPanel(margins=0)
        main_panel.addWidget(t_buttons)

        self.trigger_level = TrigLevelSlider(app)
        self.trigger_level.setMaximum(0)
        self.trigger_level.setMaximum(255)
        self.trigger_level.setSliderPosition(255 * (app.model.trigger.level + 1) / 2)
        self.trigger_level.valueChanged.connect(self.trigger_level_callback)
        self.app.set_trigger_level_from_plot_line = \
            lambda value: self.trigger_level.setSliderPosition(255 * (value + 1) / 2)
        trig_level_panel = VBoxPanel([
            Label("Trig Level"),
            HBoxPanel([
                self.trigger_level,
                VBoxPanel([
                    W(QLabel(), stretch=1),
                    ZeroButton(lambda: self.app.set_trigger_level_from_plot_line(0)),
                    W(QLabel(), stretch=1)
                ], margins=0),
                W(QLabel(), stretch=1)
            ], margins=0)
        ], margins=0)
        layout.addWidget(HBoxPanel([main_panel, trig_level_panel], margins=0))

        main_panel.addWidget(VBoxPanel([QLabel("Trigger on")], margins=(0, 70, 0, 0)))
        self.channel_selector = ComboBox(
            items=["Channel 0", "Channel 1"],
            current_selection=f"Channel {app.model.trigger.on_channel}",
            min_width=100,
            on_text_change=self.trigger_channel_callback
        )

        main_panel.addWidget(HBoxPanel(
            widgets=[
                ComboBox(
                    items=["Rising Edge", "Falling Edge", "External Signal"],
                    current_selection=app.model.trigger.trigger_type.value,
                    min_width=100,
                    on_text_change=self.trigger_type_callback
                ),
            ],
            margins=0
        ))
        main_panel.addWidget(HBoxPanel(widgets=[self.channel_selector], margins=0))

        tplabel = Label("Tigger Position")
        tplabel.setContentsMargins(0, 20, 0, 0)
        layout.addWidget(tplabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.trigger_position_slider = TrigPosSlider(app)
        self.trigger_position_slider.setMaximum(0)
        self.trigger_position_slider.setMaximum(3999)
        self.trigger_position_slider.setSliderPosition(int(app.model.trigger.position * 3999))
        self.trigger_position_slider.valueChanged.connect(self.trigger_position_callback)
        self.app.set_trigger_pos_from_plot_line = self.set_trigger_pos_from_plot_line
        layout.addWidget(self.trigger_position_slider)
        layout.addWidget(HBoxPanel(
            widgets=[
                W(QLabel(), stretch=1),
                ZeroButton(lambda: self.set_trigger_pos_from_plot_line(0.5)),
                W(QLabel(), stretch=1)
            ],
            margins=0
        ))

        layout.addStretch(10)

        self.setAutoFillBackground(True)
        self.setPalette(self.app.side_pannels_palette())

        self.app.trigger_disarmed = self.trigger_disarmed
        self.app.trigger_armed_single = self.trigger_armed_single
        self.app.trigger_armed_normal = self.trigger_armed_normal
        self.app.trigger_armed_auto = self.trigger_armed_auto
        self.app.trigger_force_acq = self.trigger_force_acq

    def trigger_armed_single(self):
        with self.selected_button_lock:
            if self.selected_button != self.single_button.text():
                self.set_button_active_appearance(self.single_button)
                self.selected_button = self.single_button.text()

    def trigger_armed_normal(self):
        with self.selected_button_lock:
            if self.selected_button != self.normal_button.text():
                self.set_button_active_appearance(self.normal_button)
                self.selected_button = self.normal_button.text()

    def trigger_armed_auto(self):
        with self.selected_button_lock:
            if self.selected_button != self.auto_button.text():
                self.set_button_active_appearance(self.auto_button)
                self.selected_button = self.auto_button.text()

    def trigger_force_acq(self):
        with self.selected_button_lock:
            if self.selected_button != self.force_acq_button.text():
                self.set_button_active_appearance(self.force_acq_button)
                self.selected_button = self.force_acq_button.text()

    def trigger_disarmed(self) -> None:
        with self.selected_button_lock:
            if self.selected_button != self.stop_button.text():
                self.set_button_active_appearance(self.stop_button)
                self.selected_button = self.stop_button.text()

    def set_button_active_appearance(self, button: PushButton) -> None:
        for b in [self.stop_button, self.single_button, self.normal_button, self.auto_button, self.force_acq_button]:
            if b is button:
                b.setStyleSheet("background-color: lime; color: black")
            else:
                b.setStyleSheet("background-color: darkred; color: white")

    def trigger_channel_callback(self, channel: str):
        on_channel = int(channel.replace("Channel", "").strip())
        self.app.worker.messages.put(WorkerMessage.SetTriggerOnChannel(on_channel))
        self.app.update_trigger_lines_color(on_channel)

    def trigger_type_callback(self, trigger_type: str):
        self.app.model.trigger.trigger_type = TriggerTypeModel.value_of(trigger_type)
        self.app.worker.messages.put(WorkerMessage.SetTriggerType(
            self.app.model.trigger.trigger_type.to_trigger_type()
        ))
        if self.app.model.trigger.trigger_type == TriggerTypeModel.EXTERNAL_SIGNAL:
            self.trigger_level.setEnabled(False)
            self.channel_selector.setEnabled(False)
            self.set_trigger_level_line_visible(False)
        else:
            self.trigger_level.setEnabled(True)
            self.channel_selector.setEnabled(True)
            self.set_trigger_level_line_visible(True)

    def trigger_position_callback(self):
        self.app.worker.messages.put(
            WorkerMessage.SetTriggerPosition(self.trigger_position_slider.value() / 3999.0)
        )

    def trigger_level_callback(self):
        self.app.worker.messages.put(WorkerMessage.SetTriggerLevel(self.trigger_level.value() * 2 / 255 - 1))

    def set_trigger_pos_from_plot_line(self, value):
        if value != self.app.model.trigger.position:
            self.trigger_position_slider.setSliderPosition(int(value * 3999))

    def set_trigger_level_line_visible(self, visible: bool):
        self.app.set_trigger_level_line_visible(visible)

    def disarm(self):
        with self.selected_button_lock:
            if self.selected_button != self.stop_button.text():
                self.app.worker.messages.put(WorkerMessage.Disarm())

    def arm_single(self):
        with self.selected_button_lock:
            if self.selected_button != self.single_button.text():
                self.app.worker.messages.put(
                    WorkerMessage.ArmSingle(self.app.model.trigger.trigger_type.to_trigger_type())
                )

    def arm_normal(self):
        with self.selected_button_lock:
            if self.selected_button != self.normal_button.text():
                self.app.worker.messages.put(
                    WorkerMessage.ArmNormal(self.app.model.trigger.trigger_type.to_trigger_type())
                )

    def arm_auto(self):
        with self.selected_button_lock:
            if self.selected_button != self.auto_button.text():
                self.app.worker.messages.put(WorkerMessage.ArmAuto(
                    self.app.model.trigger.trigger_type.to_trigger_type()
                ))

    def arm_force_acq(self):
        with self.selected_button_lock:
            if self.selected_button != self.force_acq_button.text():
                self.app.worker.messages.put(WorkerMessage.ArmForceAcq())
