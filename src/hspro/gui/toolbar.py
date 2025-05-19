from PySide6.QtWidgets import QToolBar, QLabel
from pytide6 import PushButton

from hspro.gui.app import App


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
        self.buttons.append(take_snapshot_button)
        self.addWidget(take_snapshot_button)
