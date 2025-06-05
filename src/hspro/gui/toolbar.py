from PySide6.QtWidgets import QToolBar, QLabel
from pytide6 import PushButton

from hspro.gui.app import App, WorkerMessage


class MainToolBar(QToolBar):
    def __init__(self, app: App):
        super().__init__()
        self.setStyleSheet("QToolBar{ padding: 3px 3px 3px 3px; spacing: 5px; }")

        self.addWidget(
            QLabel("<b><h2 style=\"color: blue;\">Haasoscope<em style=\"color: red;\">Pro</em>&nbsp;&nbsp;</h2></b>"))

        self.current_selection = None
        self.buttons = []

        def mk_selector(b: PushButton):
            def select():
                if app.current_active_tool == b.text():
                    # deactivate this tool
                    app.current_active_tool = None
                    b.setStyleSheet("background-color: #ffffff; color: black;")
                else:
                    for btn in self.buttons:
                        if btn is b:
                            btn.setStyleSheet("background-color: #008800; color: white;")
                            app.current_active_tool = b.text()
                        else:
                            btn.setStyleSheet("background-color: #ffffff; color: black;")

            return select

        zoom_button = PushButton("Zoom", self)
        zoom_button.clicked.connect(mk_selector(zoom_button))
        self.buttons.append(zoom_button)
        self.addWidget(zoom_button)

        add_label_button = PushButton("Add Label", self)
        add_label_button.clicked.connect(mk_selector(add_label_button))
        self.buttons.append(add_label_button)
        self.addWidget(add_label_button)

        add_v_marker_button = PushButton("Add Vertical Marker", self)
        add_v_marker_button.clicked.connect(mk_selector(add_v_marker_button))
        self.buttons.append(add_v_marker_button)
        self.addWidget(add_v_marker_button)

        add_h_marker_button = PushButton("Add Horizontal Marker", self)
        add_h_marker_button.clicked.connect(mk_selector(add_h_marker_button))
        self.buttons.append(add_h_marker_button)
        self.addWidget(add_h_marker_button)

        self.addWidget(QLabel("        "))

        take_snapshot_button = PushButton("Take scene snapshot", self)
        take_snapshot_button.clicked.connect(app.record_state_in_scene)
        self.addWidget(take_snapshot_button)

        hold_release_button = PushButton("Hold", self)
        hide_held_button = PushButton("Hide", self)
        hide_held_button.setEnabled(False)

        def toggle_hold_release():
            if hold_release_button.text() == "Hold":
                hold_release_button.setText("Release")
                app.worker.messages.put(WorkerMessage.HoldWaveforms())
                hide_held_button.setEnabled(True)
            else:
                hold_release_button.setText("Hold")
                app.worker.messages.put(WorkerMessage.ReleaseWaveforms())
                hide_held_button.setEnabled(False)

        hold_release_button.clicked.connect(toggle_hold_release)
        self.addWidget(hold_release_button)

        def toggle_hide_held():
            if hide_held_button.text() == "Hide":
                app.worker.messages.put(WorkerMessage.ShowHideHeldWaveforms(False))
                hide_held_button.setText("Show")
            else:
                app.worker.messages.put(WorkerMessage.ShowHideHeldWaveforms(True))
                hide_held_button.setText("Hide")

        hide_held_button.clicked.connect(toggle_hide_held)
        self.addWidget(hide_held_button)
