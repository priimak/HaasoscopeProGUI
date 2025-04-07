import math

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea
from pytide6 import MainWindow, set_geometry, VBoxPanel, W, HBoxPanel, Label
from sprats.config import AppPersistence

from hspro.gui.app import App
from hspro.gui.menus.menu_bar import MainMenuBar
from hspro.gui.model import BoardModel
from hspro.gui.panels.channels_panel import ChannelsPanel
from hspro.gui.panels.general_opts_panel import GeneralOptionsPanel
from hspro.gui.panels.info_panel import InfoPanel
from hspro.gui.panels.plots_panel import PlotsPanel
from hspro.gui.panels.trigger_panel import TriggerPanel


class HSProMainWindow(MainWindow):

    def __init__(self, screen_dim: tuple[int, int], app_persistence: AppPersistence):
        super().__init__(objectName="MainWindow", windowTitle="Haasoscope Pro GUI")

        self.app = App()
        self.app.model = BoardModel(app_persistence)
        self.app.app_persistence = app_persistence
        self.app.main_window = lambda: self
        self.app.exit_application = self.close
        # self.app.set_plot_color_scheme = self.set_plot_color_scheme

        set_geometry(app_state=app_persistence.state, widget=self, screen_dim=screen_dim, win_size_fraction=0.7)

        self.menu_bar = self.setMenuBar(MainMenuBar(self.app))

        self.glw = PlotsPanel(self, self.app)

        x = [0.01 * i for i in range(-100, 3000)]
        y = [math.sin(t) for t in x]

        # grid = GridItem()
        # grid.setTickSpacing(x = [1.0], y = [1.0])
        # self.plot.addItem(grid)

        # axis = AxisItem("bottom")
        # axis.setVisible(False)
        # self.plot.addItem(axis)

        # pp: PlotDataItem = self.plot.plot(x, y)
        # self.plot.setXRange(0, 10, padding=0.0)
        # self.plot.setYRange(-5, 5, padding=0.0)

        # plot_item.plot(x, y)
        # print(pp.name())
        # self.plot.addItem(plot_item)

        right_panel = VBoxPanel(
            widgets=[
                # TriggerPanel(self.app), W(Label(""), stretch=10)
                TriggerPanel(self.app), GeneralOptionsPanel(self.app), W(Label(""), stretch=10)
            ],
            margins=0
        )
        channels_area = QScrollArea()
        channels_area.setWidget(ChannelsPanel(self.app))
        channels_area.setMinimumWidth(ChannelsPanel.min_width + 15)
        channels_area.setWidgetResizable(True)
        channels_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        channels_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        top_controls_panel = HBoxPanel([channels_area, right_panel], margins=0)
        controls_panel = VBoxPanel([top_controls_panel], margins=0)

        main_panel = HBoxPanel(widgets=[
            W(self.glw, stretch=1), controls_panel
        ])
        self.setCentralWidget(
            VBoxPanel(
                widgets=[W(main_panel, stretch=1), InfoPanel(self.app)],
                spacing=0, margins=(5, 5, 5, 1)
            )
        )

        self.app.init()
