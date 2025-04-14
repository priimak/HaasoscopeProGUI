from PySide6.QtWidgets import QSpinBox, QLabel
from pytide6 import Dialog, VBoxLayout, CheckBox, PushButton, HBoxPanel, W, ComboBox

from hspro.gui.app import App


class ReadOutOptionsDialog(Dialog):
    def __init__(self, parent, app: App):
        super().__init__(parent, windowTitle="Readout options", modal=True)

        highres_cb = CheckBox("Highres", self, checked=app.model.highres)

        delay_sb = QSpinBox()
        delay_sb.setMinimum(0)
        delay_sb.setMaximum(10)
        delay_sb.setSingleStep(1)
        delay_sb.setValue(app.model.delay)

        f_delay_sb = QSpinBox()
        f_delay_sb.setMinimum(0)
        f_delay_sb.setMaximum(10)
        f_delay_sb.setSingleStep(1)
        f_delay_sb.setValue(app.model.f_delay)

        mem_depth_sb = QSpinBox()
        mem_depth_sb.setMinimum(100)
        mem_depth_sb.setMaximum(1000)
        mem_depth_sb.setSingleStep(100)
        mem_depth_sb.setValue(app.model.mem_depth)

        auto_freq_cbox = ComboBox(
            items=["2 Hz", "5 Hz", "10 Hz"],
            current_selection=app.model.trigger.auto_frequency,
            min_width=50
        )

        def on_ok():
            if app.model.highres != highres_cb.isChecked():
                app.model.highres = highres_cb.isChecked()

            if app.model.delay != delay_sb.value():
                app.model.delay = delay_sb.value()

            if app.model.f_delay != f_delay_sb.value():
                app.model.f_delay = f_delay_sb.value()

            if app.model.mem_depth != mem_depth_sb.value():
                app.model.mem_depth = mem_depth_sb.value()

            if app.model.trigger.auto_frequency != auto_freq_cbox.currentText():
                app.model.trigger.auto_frequency = auto_freq_cbox.currentText()

            self.close()

        self.setLayout(VBoxLayout([
            highres_cb,
            HBoxPanel([delay_sb, QLabel("Delay")], margins=0),
            HBoxPanel([f_delay_sb, QLabel("F Delay")], margins=0),
            HBoxPanel([mem_depth_sb, QLabel("Memory depth")], margins=0),
            HBoxPanel([auto_freq_cbox, QLabel("Auto trig. min update frequency")], margins=0),

            HBoxPanel([
                W(HBoxPanel(), stretch=1),
                PushButton("Ok", on_clicked=on_ok),
                PushButton("Cancel", on_clicked=self.close)
            ])
        ]))
