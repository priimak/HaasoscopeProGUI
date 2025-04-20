from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDoubleSpinBox, QLabel
from pytide6 import VBoxPanel, HBoxPanel, W

from hspro.gui.app import App, WorkerMessage


class TimeScaleSpinner(QDoubleSpinBox):
    def __init__(self, app: App):
        super().__init__()
        self.app = app
        self.setMinimum(0)
        self.setMaximum(1_000_000_000_000.0)
        self.setDecimals(0)
        self.dT = app.model.visual_time_scale
        self.setValue(self.dT.value)
        self.setSuffix(f" {self.dT.time_unit.to_str()}/div")

    def stepBy(self, steps):
        self.dT = self.app.model.get_next_valid_visual_time_scale(current_value=self.dT, index_offset=steps)
        self.app.worker.messages.put(WorkerMessage.SetTimeScale(self.dT))
        self.setValue(self.dT.value)
        self.setSuffix(f" {self.dT.time_unit.to_str()}/div")

    def dependencies_changed(self):
        self.dT = self.app.model.get_next_valid_visual_time_scale(current_value=self.dT, index_offset=0)
        self.setValue(self.dT.value)
        self.setSuffix(f" {self.dT.time_unit.to_str()}/div")


class GeneralOptionsPanel(VBoxPanel):
    def __init__(self, app: App):
        super().__init__()
        self.app = app

        time_scale_input = TimeScaleSpinner(app)
        time_scale_input.setMaximumWidth(200)
        self.app.model.on_memdepth_change = time_scale_input.dependencies_changed
        self.app.model.on_channel_active_change = time_scale_input.dependencies_changed

        self.layout().addWidget(QLabel("Time scale"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(HBoxPanel([W(time_scale_input, alignment=Qt.AlignmentFlag.AlignCenter)], margins=0))

        # slower_b = PushButton("Slower", on_clicked=lambda: time_scale_input.stepBy(-1))
        # faster_b = PushButton("Faster", on_clicked=lambda: time_scale_input.stepBy(1))
        # self.layout().addWidget(HBoxPanel([
        #     W(slower_b, alignment=Qt.AlignmentFlag.AlignLeft),
        #     W(faster_b, alignment=Qt.AlignmentFlag.AlignRight)
        # ], margins=0))

        self.setAutoFillBackground(True)
        self.setPalette(app.side_pannels_palette())
