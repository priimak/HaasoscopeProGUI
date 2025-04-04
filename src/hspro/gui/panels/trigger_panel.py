from PySide6.QtGui import QPalette, Qt
from PySide6.QtWidgets import QSpinBox, QSpacerItem, QSlider
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
        self.external_button = PushButton("  External  ")

        self.set_button_active_appearance(self.stop_button)

        self.stop_button.clicked.connect(lambda: self.set_button_active_appearance(self.stop_button))
        self.single_button.clicked.connect(lambda: self.set_button_active_appearance(self.single_button))
        self.normal_button.clicked.connect(lambda: self.set_button_active_appearance(self.normal_button))
        self.auto_button.clicked.connect(lambda: self.set_button_active_appearance(self.auto_button))
        self.external_button.clicked.connect(lambda: self.set_button_active_appearance(self.external_button))

        # layout.addWidget(Label("Trigger"))
        t_buttons = HBoxPanel(widgets=[
            W(
                VBoxPanel(
                    widgets=[
                        Label("Trigger"),
                        self.stop_button, self.single_button, self.normal_button, self.auto_button, self.external_button
                    ],
                    margins=0
                ),
                alignment=Qt.AlignmentFlag.AlignLeft
            ),
            QSpacerItem
        ], margins=0)
        main_panel = VBoxPanel(margins=0)
        # main_panel.setAutoFillBackground(True)
        # palette = QPalette()
        # palette.setColor(QPalette.ColorRole.Window, "orange")
        # main_panel.setPalette(palette)

        main_panel.addWidget(t_buttons)

        self.trigger_level = QSlider(Qt.Orientation.Vertical)
        self.trigger_level.setMaximum(0)
        self.trigger_level.setMaximum(255)
        self.trigger_level.setSliderPosition(255 * (app.model.trigger.level + 1) / 2)
        self.trigger_level.valueChanged.connect(self.trigger_level_callback)
        trig_level_panel = VBoxPanel([Label("Trig Level"), HBoxPanel([self.trigger_level], margins=0)], margins=0)
        layout.addWidget(HBoxPanel([main_panel, trig_level_panel], margins=0))

        main_panel.addWidget(HBoxPanel(
            widgets=[
                ComboBox(
                    items=["Channel 1", "Channel 2"],
                    current_selection=f"Channel {app.model.trigger.on_channel + 1}",
                    min_width=100,
                    on_text_change=self.trigger_channel_callback
                ),
            ],
            margins=(0, 30, 0, 0)
        ))

        main_panel.addWidget(HBoxPanel(
            widgets=[
                ComboBox(
                    items=["Rising Edge", "Falling Edge"],
                    current_selection=app.model.trigger.trigger_type.value,
                    min_width=100,
                    on_text_change=self.trigger_type_callback
                ),
            ],
            margins=0
        ))

        self.tot = QSpinBox(self)
        self.tot.setMaximum(0)
        self.tot.setMaximum(255)
        self.tot.setValue(app.model.trigger.tot)
        self.tot.valueChanged.connect(self.tot_change_callback)
        main_panel.addWidget(HBoxPanel([self.tot, Label("ToT")], margins=0))

        self.delta = QSpinBox(self)
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
        layout.addWidget(self.trigger_position)

        layout.addStretch(10)

        self.setAutoFillBackground(True)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, "lightblue")
        self.setPalette(palette)

    def set_button_active_appearance(self, button: PushButton) -> None:
        for b in [self.stop_button, self.single_button, self.normal_button, self.auto_button, self.external_button]:
            if b is button:
                b.setStyleSheet("background-color: lime; color: black")
            else:
                b.setStyleSheet("background-color: darkred; color: white")

    def trigger_channel_callback(self, channel: str):
        self.app.model.trigger.on_channel = int(0 if "1" in channel else 1)

    def trigger_type_callback(self, trigger_type: str):
        self.app.model.trigger.trigger_type = TriggerTypeModel.value_of(trigger_type)

    def tot_change_callback(self):
        self.app.model.trigger.tot = self.tot.value()

    def delta_change_callback(self):
        self.app.model.trigger.delta = self.delta.value()

    def trigger_position_callback(self):
        self.app.model.trigger.position = self.trigger_position.value() / 999.0

    def trigger_level_callback(self):
        self.app.model.trigger.level = self.trigger_level.value() * 2 / 255 - 1
