from PySide6.QtWidgets import QMenu, QMenuBar, QWidget

from hspro.gui.app import App


class FileMenu(QMenu):
    def __init__(self, parent: QMenuBar, app: App):
        super().__init__("&File", parent)

        self.addSeparator()
        self.addAction("&Quit", lambda: app.exit_application())