from PySide6.QtWidgets import QMenuBar

from hspro.gui.app import App
from hspro.gui.menus.file_menu import FileMenu
from hspro.gui.menus.help_menu import HelpMenu
from hspro.gui.menus.trace_menu import TraceMenu


class MainMenuBar(QMenuBar):
    def __init__(self, app: App):
        super().__init__(None)

        self.file_menu = FileMenu(self, app)
        self.trace_menu = TraceMenu(self, app)
        self.help_menu = HelpMenu(self)

        self.addMenu(self.file_menu)
        self.addMenu(self.trace_menu)
        self.addMenu(self.help_menu)

        self.setStyleSheet(
            """
            QMenu {
                background-color: #ebeff4;
            }
            
            QMenu::item:selected {
                background-color: #3daee9;
                color: white;
            }
            """
        )
