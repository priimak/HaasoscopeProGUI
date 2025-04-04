from PyQt5.QtWidgets import QDoubleSpinBox
from pytide6 import VBoxPanel, HBoxPanel

from hspro.gui.app import App

class TimeScaleSpinner(QDoubleSpinBox):
    def __init__(self, app: App):
        super().__init__()
        self.app = app
        # self.setDecimals(4)
        # self.setValue(app.model.channel[channel].dV)

    def stepBy(self, steps):
        new_val = self.value() * (1.0 + steps * 0.1)
        self.app.model.channel[self.channel].dV = new_val
        self.setValue(new_val)

class GeneralOptionsPanel(VBoxPanel):
    def __init__(self, app: App):
        super().__init__(margins=0)
        self.app = app

        self.layout().addWidget(HBoxPanel([], margins=0))
