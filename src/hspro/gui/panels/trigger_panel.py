from PySide6.QtGui import Qt
from PySide6.QtWidgets import QSpinBox, QSpacerItem, QSlider, QLabel
from pytide6 import VBoxPanel, VBoxLayout, PushButton, Label, HBoxPanel, ComboBox, W

from hspro.gui.app import App
from hspro.gui.model import TriggerTypeModel


class TriggerPanel(VBoxPanel):
    def __init__(self, app: App):
        super().__init__()
        self.app = app

        layout: VBoxLayout = self.layout()

        self.stop_button = PushButton("Stop")
        self.single_button = PushButton("Single")
        self.normal_button = PushButton("Normal")
        self.auto_button = PushButton("Auto")

        self.set_button_active_appearance(self.stop_button)

        self.stop_button.clicked.connect(lambda: self.set_button_active_appearance(self.stop_button))
        self.single_button.clicked.connect(lambda: self.set_button_active_appearance(self.single_button))
        self.normal_button.clicked.connect(lambda: self.set_button_active_appearance(self.normal_button))
        self.auto_button.clicked.connect(lambda: self.set_button_active_appearance(self.auto_button))

        # layout.addWidget(Label("Trigger"))
        t_buttons = HBoxPanel(widgets=[
            W(
                VBoxPanel(
                    widgets=[
                        Label("Trigger"),
                        self.stop_button, self.single_button, self.normal_button, self.auto_button
                    ],
                    margins=0
                ),
                alignment=Qt.AlignmentFlag.AlignLeft
            ),
            QSpacerItem
        ], margins=0)
        main_panel = VBoxPanel(margins=0)
        main_panel.addWidget(t_buttons)

        self.trigger_level = QSlider(Qt.Orientation.Vertical)
        self.trigger_level.setMaximum(0)
        self.trigger_level.setMaximum(255)
        self.trigger_level.setSliderPosition(255 * (app.model.trigger.level + 1) / 2)
        self.trigger_level.valueChanged.connect(self.trigger_level_callback)
        self.app.set_trigger_level_from_plot_line = self.set_trigger_level_from_plot_line
        trig_level_panel = VBoxPanel([Label("Trig Level"), HBoxPanel([self.trigger_level], margins=0)], margins=0)
        layout.addWidget(HBoxPanel([main_panel, trig_level_panel], margins=0))

        main_panel.addWidget(VBoxPanel([QLabel("Trigger on")], margins=(0, 40, 0, 0)))
        self.channel_selector = ComboBox(
            items=["Channel 1", "Channel 2"],
            current_selection=f"Channel {app.model.trigger.on_channel + 1}",
            min_width=100,
            on_text_change=self.trigger_channel_callback
        )
        self.tot = QSpinBox(self)
        self.delta = QSpinBox(self)

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

        self.tot.setMaximum(0)
        self.tot.setMaximum(255)
        self.tot.setValue(app.model.trigger.tot)
        self.tot.valueChanged.connect(self.tot_change_callback)
        main_panel.addWidget(HBoxPanel([self.tot, Label("ToT")], margins=0))

        self.delta.setMaximum(0)
        self.delta.setMaximum(100)
        self.delta.setValue(app.model.trigger.delta)
        self.delta.valueChanged.connect(self.delta_change_callback)
        main_panel.addWidget(HBoxPanel([self.delta, Label("Delta")], margins=0))

        tplabel = Label("Tigger Position")
        tplabel.setContentsMargins(0, 20, 0, 0)
        layout.addWidget(tplabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.trigger_position = QSlider(Qt.Orientation.Horizontal)
        self.trigger_position.setMaximum(0)
        self.trigger_position.setMaximum(999)
        self.trigger_position.setSliderPosition(int(app.model.trigger.position * 999))
        self.trigger_position.valueChanged.connect(self.trigger_position_callback)
        self.app.set_trigger_pos_from_plot_line = self.set_trigger_pos_from_plot_line
        layout.addWidget(self.trigger_position)

        layout.addStretch(10)

        self.setAutoFillBackground(True)
        self.setPalette(self.app.side_pannels_palette())

    def set_button_active_appearance(self, button: PushButton) -> None:
        for b in [self.stop_button, self.single_button, self.normal_button, self.auto_button]:
            if b is button:
                b.setStyleSheet("background-color: lime; color: black")
            else:
                b.setStyleSheet("background-color: darkred; color: white")

    def trigger_channel_callback(self, channel: str):
        self.app.model.trigger.on_channel = int(0 if "1" in channel else 1)

    def trigger_type_callback(self, trigger_type: str):
        self.app.model.trigger.trigger_type = TriggerTypeModel.value_of(trigger_type)
        if self.app.model.trigger.trigger_type == TriggerTypeModel.EXTERNAL_SIGNAL:
            self.trigger_level.setEnabled(False)
            self.channel_selector.setEnabled(False)
            self.tot.setEnabled(False)
            self.delta.setEnabled(False)
            self.set_trigger_level_line_visible(False)
        else:
            self.trigger_level.setEnabled(True)
            self.channel_selector.setEnabled(True)
            self.tot.setEnabled(True)
            self.delta.setEnabled(True)
            self.set_trigger_level_line_visible(True)

    def tot_change_callback(self):
        self.app.model.trigger.tot = self.tot.value()

    def delta_change_callback(self):
        self.app.model.trigger.delta = self.delta.value()

    def trigger_position_callback(self):
        self.app.model.trigger.position = self.trigger_position.value() / 999.0
        self.app.set_trigger_pos_from_side_controls(self.app.model.trigger.position)

    def trigger_level_callback(self):
        self.app.model.trigger.level = self.trigger_level.value() * 2 / 255 - 1
        self.app.set_trigger_level_from_side_controls(self.app.model.trigger.level)

    def set_trigger_level_from_plot_line(self, value):
        value = value / 5
        if value != self.app.model.trigger.level:
            self.app.model.trigger.level = value
            self.trigger_level.setSliderPosition(255 * (self.app.model.trigger.level + 1) / 2)

    def set_trigger_pos_from_plot_line(self, value):
        value = value / 10
        if value != self.app.model.trigger.position:
            self.app.model.trigger.position = value
            self.trigger_position.setSliderPosition(int(value * 999))

    def set_trigger_level_line_visible(self, visible: bool):
        self.app.set_trigger_level_line_visible(visible)
