from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QMenu, QMenuBar, QWidgetAction, QSlider, QLabel
from pytide6 import HBoxPanel

from hspro.gui.app import App, WorkerMessage
from hspro.gui.read_out_options_dialog import ReadOutOptionsDialog
from hspro.gui.scene import SceneCheckpoint


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

        self.show_y_axis_labels = QAction("Show Y-Axis labels", self)
        self.show_y_axis_labels.setCheckable(True)
        self.show_y_axis_labels.setChecked(app.app_persistence.config.get_by_xpath("/show_y_axis_labels"))
        self.show_y_axis_labels.toggled.connect(self.set_show_y_axis_labels)
        self.addAction(self.show_y_axis_labels)

        self.show_grid = QAction("Show &Grid", self)
        self.show_grid.setCheckable(True)
        self.show_grid.setChecked(app.app_persistence.config.get_by_xpath("/show_grid"))
        self.show_grid.toggled.connect(self.set_show_grid_state)
        self.addAction(self.show_grid)

        ################### Grid Opacity
        grid_opacity = app.app_persistence.state.get_value("grid_opacity", "0.5")
        grid_opacity_slider_action = QWidgetAction(self)
        grid_opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        grid_opacity_slider.setMinimum(0)
        grid_opacity_slider.setMaximum(255)
        grid_opacity_slider.setValue(int(float(grid_opacity) * 255))
        grid_opacity_slider.valueChanged.connect(self.app.do_set_grid_opacity)
        m = HBoxPanel([HBoxPanel([QLabel("Grid Opacity")], margins=(10, 0, 0, 0)), grid_opacity_slider])
        grid_opacity_slider_action.setDefaultWidget(m)
        self.addAction(grid_opacity_slider_action)

        self.show_trig_level_line = QAction("Show &Trigger Level Line", self)
        self.show_trig_level_line.setCheckable(True)
        self.show_trig_level_line.setChecked(app.app_persistence.config.get_by_xpath("/show_trigger_level_line"))
        self.show_trig_level_line.toggled.connect(self.set_show_trigger_level_line)
        self.addAction(self.show_trig_level_line)

        self.show_trig_pos_line = QAction("Show &Trigger Position Line", self)
        self.show_trig_pos_line.setCheckable(True)
        self.show_trig_pos_line.setChecked(app.app_persistence.config.get_by_xpath("/show_trigger_position_line"))
        self.show_trig_pos_line.toggled.connect(self.set_show_trig_pos_line)
        self.addAction(self.show_trig_pos_line)

        self.show_zero_line = QAction("Show &Zero Line", self)
        self.show_zero_line.setCheckable(True)
        self.show_zero_line.setChecked(app.app_persistence.config.get_by_xpath("/show_zero_line"))
        self.show_zero_line.toggled.connect(self.set_show_zero_line_state)
        self.addAction(self.show_zero_line)

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

        def apply_checkpoint(cpt: SceneCheckpoint):
            match cpt.plot_color_scheme:
                case "light":
                    self.set_plot_color_scheme_light()
                case "dark":
                    self.set_plot_color_scheme_dark()

            self.show_trig_level_line.setChecked(cpt.show_trigger_level_line)
            self.show_trig_pos_line.setChecked(cpt.show_trigger_position_line)
            self.show_grid.setChecked(cpt.show_grid)
            self.show_y_axis_labels.setChecked(cpt.show_y_axis_labels)
            self.show_zero_line.setChecked(cpt.show_zero_line)

            app.worker.messages.put(WorkerMessage.SetHighres(cpt.highres))
            app.worker.messages.put(WorkerMessage.SetMemoryDepth(cpt.mem_depth))
            app.worker.messages.put(WorkerMessage.SetDelay(cpt.delay))
            app.worker.messages.put(WorkerMessage.SetFDelay(cpt.f_delay))

            # TODO: add visual_time_scale

        self.app.apply_checkpoint_to_trace_menu = apply_checkpoint

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

    def set_show_y_axis_labels(self, show_y_axis_labels: bool):
        self.app.set_show_y_axis_labels(show_y_axis_labels)

    def set_show_trigger_level_line(self, show_trig_level_line: bool):
        self.app.set_show_trigger_level_line(show_trig_level_line)

    def set_show_zero_line_state(self, show_zero_line: bool):
        self.app.set_show_zero_line(show_zero_line)

    def set_show_trig_pos_line(self, show_trig_pos_line: bool):
        self.app.set_show_trig_pos_line(show_trig_pos_line)

    def show_readout_options_dialog(self):
        ReadOutOptionsDialog(self.parent(), self.app).exec_()
