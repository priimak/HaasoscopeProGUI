from functools import cache
from typing import Callable

from PySide6.QtGui import QPalette, QPen, Qt
from pytide6 import MainWindow
from sprats.config import AppPersistence

from hspro.gui.model import BoardModel


class App:
    app_persistence: AppPersistence
    model: BoardModel
    main_window: Callable[[], MainWindow] = lambda _: None
    exit_application: Callable[[], bool] = lambda: True
    set_connection_status_label: Callable[[str], None] = lambda _: None
    set_plot_color_scheme: Callable[[str], None] = lambda _: None
    channels: list[int] = [0, 1]
    set_trigger_level_from_side_controls: Callable[[float], None] = lambda _: None
    set_trigger_level_from_plot_line: Callable[[float], None] = lambda _: None
    set_trigger_pos_from_side_controls: Callable[[float], None] = lambda _: None
    set_trigger_pos_from_plot_line: Callable[[float], None] = lambda _: None
    set_channel_active_state: Callable[[int, bool], None] = lambda a, b: None
    set_channel_color: Callable[[int, str], None] = lambda a, b: None
    set_show_grid_state: Callable[[bool], None] = lambda _: None
    set_show_zero_line_state: Callable[[bool], None] = lambda _: None

    def init(self):
        plot_color_scheme: str | None = self.app_persistence.config.get_value("plot_color_scheme", str)
        if plot_color_scheme is None:
            plot_color_scheme = "light"
            self.app_persistence.config.set_value("plot_color_scheme", plot_color_scheme)
        self.set_plot_color_scheme(plot_color_scheme)

    @cache
    def side_pannels_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, "lightblue")
        return palette

    @cache
    def trigger_lines_pen_default(self) -> QPen:
        pen = QPen()
        pen.setCosmetic(True)
        pen.setColor("#0000FF")
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([4, 4])
        return pen
