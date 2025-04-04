from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMenuBar

from hspro.gui.app import App


class ViewMenu(QMenu):
    def __init__(self, parent: QMenuBar, app: App):
        super().__init__("&View", parent)
        self.app = app

        plot_color_scheme_menu = self.addMenu("Plot color scheme")

        self.plot_color_scheme_light = QAction("Light", self)
        self.plot_color_scheme_light.setCheckable(True)
        plot_color_scheme_menu.addAction(self.plot_color_scheme_light)
        self.plot_color_scheme_light.triggered.connect(self.set_plot_color_scheme_light)

        self.plot_color_scheme_dark = QAction("Dark", self)
        self.plot_color_scheme_dark.setCheckable(True)
        plot_color_scheme_menu.addAction(self.plot_color_scheme_dark)
        self.plot_color_scheme_dark.triggered.connect(self.set_plot_color_scheme_dark)

        plot_color_scheme = app.app_persistence.config.get_value("plot_color_scheme")
        self.plot_color_scheme_light.setChecked(plot_color_scheme == "light")
        self.plot_color_scheme_dark.setChecked(plot_color_scheme == "dark")

    def set_plot_color_scheme_light(self):
        self.plot_color_scheme_light.setChecked(True)
        self.plot_color_scheme_dark.setChecked(False)
        self.app.set_plot_color_scheme("light")

    def set_plot_color_scheme_dark(self):
        self.plot_color_scheme_light.setChecked(False)
        self.plot_color_scheme_dark.setChecked(True)
        self.app.set_plot_color_scheme("dark")


