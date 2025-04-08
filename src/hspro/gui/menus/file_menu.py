from PySide6.QtWidgets import QMenu, QMenuBar

from hspro.gui.app import App


class FileMenu(QMenu):
    def __init__(self, parent: QMenuBar, app: App):
        super().__init__("&File", parent)

        self.addAction("&Export waveforms").setEnabled(False)
        self.addAction("&Open saved waveforms").setEnabled(False)
        self.addSeparator()
        self.addAction("&Quit", lambda: app.exit_application())
