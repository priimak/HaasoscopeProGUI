from PySide6.QtWidgets import QLabel
from pytide6 import Dialog, VBoxLayout, HBoxPanel, PushButton, W, ComboBox

from hspro.gui.app import App


class SettingsDialog(Dialog):
    def __init__(self, parent, app: App):
        super().__init__(parent, windowTitle="General Settings", modal=True)

        trigger_lines_width = [app.trigger_lines_width]

        def set_trigger_lines_width(value):
            trigger_lines_width.clear()
            trigger_lines_width.append(value)

        trigger_lines_color_map = [app.trigger_lines_color_map]

        def set_trigger_lines_color_map(value):
            trigger_lines_color_map.clear()
            trigger_lines_color_map.append(value)

        def on_ok():
            app.trigger_lines_width = int(trigger_lines_width[0])
            app.trigger_lines_color_map = trigger_lines_color_map[0]

            app.set_trigger_lines_width(int(app.trigger_lines_width))
            app.set_trigger_lines_color_map(app.trigger_lines_color_map)
            app.update_trigger_lines_color(app.model.trigger.on_channel)
            self.close()

        self.setLayout(VBoxLayout([
            HBoxPanel([
                QLabel("Trigger lines width"),
                ComboBox(
                    items=["1", "2", "3"],
                    current_selection=f"{trigger_lines_width[0]}",
                    on_text_change=set_trigger_lines_width
                )
            ], margins=0),
            HBoxPanel([
                QLabel("Trigger lines color"),
                ComboBox(
                    items=["Default", "Matching Trigger Channel"],
                    current_selection=trigger_lines_color_map[0],
                    on_text_change=set_trigger_lines_color_map
                )
            ], margins=0),
            HBoxPanel([
                W(HBoxPanel(), stretch=1),
                PushButton("Ok", on_clicked=on_ok),
                PushButton("Cancel", on_clicked=self.close)
            ])
        ]))
