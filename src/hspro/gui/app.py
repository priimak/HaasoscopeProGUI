from typing import Callable

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

    # trigger_

    def init(self):
        plot_color_scheme: str | None = self.app_persistence.config.get_value("plot_color_scheme", str)
        if plot_color_scheme is None:
            plot_color_scheme = "light"
            self.app_persistence.config.set_value("plot_color_scheme", plot_color_scheme)
        self.set_plot_color_scheme(plot_color_scheme)
