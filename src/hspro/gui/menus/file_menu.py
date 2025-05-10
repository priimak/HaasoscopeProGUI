from PySide6.QtWidgets import QMenu, QMenuBar

from hspro.gui.app import App
from hspro.gui.settings_dialog import SettingsDialog


class FileMenu(QMenu):
    def __init__(self, parent: QMenuBar, app: App):
        super().__init__("&File", parent)
        self.app = app

        self.addAction("&Take screenshot", app.take_screenshot)
        self.addAction("&Save session")
        self.addAction("&Open session")
        self.addSeparator()
        self.addAction("&Settings", self.show_settings_dialog)
        self.addAction("&Quit", lambda: app.exit_application())

    def show_settings_dialog(self):
        SettingsDialog(self.app.main_window(), self.app).exec_()
