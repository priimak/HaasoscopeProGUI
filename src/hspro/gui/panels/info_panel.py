from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QHBoxLayout, QLabel
from pytide6 import Panel, RichTextLabel

from hspro.gui.app import App


class InfoPanel(Panel[QHBoxLayout]):
    def __init__(self, app: App):
        super().__init__(QHBoxLayout())
        self.connection_status_label = RichTextLabel("Not connected")
        self.scene_label = RichTextLabel(f"Scene \"{app.scene.name}\" #{len(app.scene.data)}")
        self.live_info_label = QLabel()

        self.layout().addWidget(self.connection_status_label)
        self.layout().addWidget(QLabel("  |  "))
        self.layout().addWidget(self.scene_label)
        self.layout().addStretch(stretch=1)
        self.layout().addWidget(self.live_info_label)

        # connect dispatching methods in App to relevant functions
        app.set_connection_status_label = self.connection_status_label.setText
        app.set_live_info_label = self.live_info_label.setText
        app.update_scene_data = lambda scene: self.scene_label.setText(f"Scene \"{scene.name}\" #{len(scene.data)}")

        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, "white")
        self.setPalette(p)
        self.setAutoFillBackground(True)
