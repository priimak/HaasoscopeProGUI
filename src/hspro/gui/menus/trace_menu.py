from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMenuBar

from hspro.gui.app import App
from hspro.gui.read_out_options_dialog import ReadOutOptionsDialog


class TraceMenu(QMenu):
    def __init__(self, parent: QMenuBar, app: App):
        super().__init__("&Trace", parent)
        self.app = app

        self.read_out_options = QAction("&Readout options", self)
        self.read_out_options.triggered.connect(self.show_readout_options_dialog)
        self.addAction(self.read_out_options)

        self.advanced_settings = QAction("&Advanced settings", self)
        self.advanced_settings.setEnabled(False)
        self.addAction(self.advanced_settings)

        self.addSeparator()

        self.show_fft = QAction("Show &FFT", self)
        self.show_fft.setEnabled(False)
        self.addAction(self.show_fft)

        self.show_persist = QAction("Show &Persist", self)
        self.show_persist.setCheckable(True)
        self.show_persist.setChecked(False)
        self.show_persist.setEnabled(False)
        self.addAction(self.show_persist)

        self.show_grid = QAction("Show &Grid", self)
        self.show_grid.setCheckable(True)
        self.show_grid.setChecked(app.app_persistence.config.get_by_xpath("/show_grid"))
        self.show_grid.triggered.connect(self.set_show_grid_state)
        self.addAction(self.show_grid)

        self.show_trig_level_line = QAction("Show &Trigger Level Line", self)
        self.show_trig_level_line.setCheckable(True)
        self.show_trig_level_line.setChecked(app.app_persistence.config.get_by_xpath("/show_trigger_level_line"))
        self.show_trig_level_line.triggered.connect(self.set_show_trigger_level_line)
        self.addAction(self.show_trig_level_line)

        self.show_trig_pos_line = QAction("Show &Trigger Position Line", self)
        self.show_trig_pos_line.setCheckable(True)
        self.show_trig_pos_line.setChecked(app.app_persistence.config.get_by_xpath("/show_trigger_position_line"))
        self.show_trig_pos_line.triggered.connect(self.set_show_trig_pos_line)
        self.addAction(self.show_trig_pos_line)

        # self.show_zero_line = QAction("Show &Central Line", self)
        # self.show_zero_line.setCheckable(True)
        # self.show_zero_line.setChecked(True)
        # self.show_zero_line.triggered.connect(self.set_show_zero_line_state)
        # self.addAction(self.show_zero_line)

        plot_color_scheme_menu = self.addMenu("Color &Scheme")

        self.plot_color_scheme_light = QAction("&Light", self)
        self.plot_color_scheme_light.setCheckable(True)
        plot_color_scheme_menu.addAction(self.plot_color_scheme_light)
        self.plot_color_scheme_light.triggered.connect(self.set_plot_color_scheme_light)

        self.plot_color_scheme_dark = QAction("&Dark", self)
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
        self.app.plot_color_scheme = "light"

    def set_plot_color_scheme_dark(self):
        self.plot_color_scheme_light.setChecked(False)
        self.plot_color_scheme_dark.setChecked(True)
        self.app.set_plot_color_scheme("dark")
        self.app.plot_color_scheme = "dark"

    def set_show_grid_state(self, show_grid: bool):
        self.app.set_show_grid_state(show_grid)

    # def set_show_zero_line_state(self, show_zero_line: bool):
    #     self.app.set_show_zero_line_state(show_zero_line)

    def set_show_trigger_level_line(self, show_trig_level_line: bool):
        self.app.set_show_trigger_level_line(show_trig_level_line)

    def set_show_trig_pos_line(self, show_trig_pos_line: bool):
        self.app.set_show_trig_pos_line(show_trig_pos_line)

    def show_readout_options_dialog(self):
        ReadOutOptionsDialog(self.parent(), self.app).exec_()
