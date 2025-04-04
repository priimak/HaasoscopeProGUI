from PySide6.QtWidgets import QHBoxLayout, QLabel
from pytide6 import Panel, RichTextLabel

from hspro.gui.app import App


class InfoPanel(Panel[QHBoxLayout]):
    def __init__(self, app: App):
        super().__init__(QHBoxLayout())
        self.connection_status_label = RichTextLabel("Not connected")

        self.layout().addWidget(self.connection_status_label)
        self.layout().addStretch(stretch=1)
        self.layout().addWidget(QLabel(""))

        # connect dispatching methods in App to relevant functions
        app.set_connection_status_label = self.connection_status_label.setText
