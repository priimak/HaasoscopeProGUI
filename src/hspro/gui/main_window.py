from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QScrollArea, QMessageBox, QProgressDialog, QProgressBar
from hspro_api.board import mk_board
from hspro_api.conn.connection import Connection
from pytide6 import MainWindow, set_geometry, VBoxPanel, W, HBoxPanel, Label
from sprats.config import AppPersistence

from hspro.gui.app import App, WorkerMessage
from hspro.gui.menus.menu_bar import MainMenuBar
from hspro.gui.model import BoardModel, TriggerTypeModel
from hspro.gui.panels.channels_panel import ChannelsPanel
from hspro.gui.panels.general_opts_panel import GeneralOptionsPanel
from hspro.gui.panels.info_panel import InfoPanel
from hspro.gui.panels.plots_panel import PlotsPanel
from hspro.gui.panels.trigger_panel import TriggerPanel
from hspro.gui.toolbar import MainToolBar


class HSProMainWindow(MainWindow):

    def __init__(self, screen_dim: tuple[int, int], app_persistence: AppPersistence):
        super().__init__(objectName="MainWindow", windowTitle="Haasoscope Pro GUI")

        self.setStyleSheet("QMainWindow { background-color: #000000; }")

        self.app = App()
        self.app.model = BoardModel(app_persistence)
        self.app.app_persistence = app_persistence
        self.app.main_window = lambda: self
        self.app.exit_application = self.close

        set_geometry(app_state=app_persistence.state, widget=self, screen_dim=screen_dim, win_size_fraction=0.7)

        self.menu_bar = self.setMenuBar(MainMenuBar(self.app))
        self.addToolBar(MainToolBar(self.app))

        self.glw = PlotsPanel(self, self.app)
        self.app.set_plot_color_scheme = self.color_scheme

        self.right_panel = VBoxPanel(
            widgets=[TriggerPanel(self.app), GeneralOptionsPanel(self.app), W(Label(""), stretch=10)],
            margins=0
        )
        self.right_panel.setAutoFillBackground(True)
        self.channels_area = QScrollArea()
        self.channels_area.setStyleSheet("border: none;")
        self.channels_panel = ChannelsPanel(self.app)
        self.channels_area.setWidget(self.channels_panel)
        self.channels_area.setMinimumWidth(ChannelsPanel.min_width + 15)
        self.channels_area.setWidgetResizable(True)
        self.channels_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.channels_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.top_controls_panel = HBoxPanel([self.channels_area, self.right_panel], margins=0)
        self.top_controls_panel.setAutoFillBackground(True)
        controls_panel = VBoxPanel([self.top_controls_panel], margins=0)

        self.setCentralWidget(
            VBoxPanel(
                widgets=[
                    W(
                        HBoxPanel(widgets=[W(self.glw, stretch=1), controls_panel]), stretch=1
                    ),
                    InfoPanel(self.app)
                ],
                spacing=0, margins=(0, 0, 0, 0)
            )
        )

        self.app.init()
        self.connect_to_board()
        self.app.model.init_board_from_model()
        self.app.worker.messages.put(
            WorkerMessage.ArmAuto(self.app.model.trigger.trigger_type.to_trigger_type(), drain_queue=False)
        )

        plot_color_scheme: str | None = self.app.app_persistence.config.get_value("plot_color_scheme", str)
        self.color_scheme(plot_color_scheme)

        # find channel to select and select it
        for i, ch in enumerate(self.app.model.channel):
            if ch.active:
                self.app.worker.messages.put(WorkerMessage.SelectChannel(i))
                break

        self.app.worker.messages.put(WorkerMessage.SetTriggerPosition(self.app.model.trigger.position_live))

        if self.app.model.trigger.trigger_type == TriggerTypeModel.EXTERNAL_SIGNAL:
            self.app.update_trigger_on_channel_label(-1)
        else:
            self.app.update_trigger_on_channel_label(self.app.model.trigger.on_channel)

    def color_scheme(self, color_scheme: str):
        self.glw.set_plot_color_scheme(color_scheme)
        match color_scheme:
            case "light":
                self.setStyleSheet("QMainWindow { background-color: #ffffff; }")
                self.channels_area.setStyleSheet("QScrollArea { background-color: #ffffff; }")
            case "dark":
                self.setStyleSheet("QMainWindow { background-color: #000000; }")
                self.channels_area.setStyleSheet("QScrollArea { background-color: #000000; }")

        self.channels_panel.set_color_scheme(color_scheme)
        match color_scheme:
            case "light":
                palette = QPalette()
                palette.setColor(QPalette.ColorRole.Window, "white")
                self.top_controls_panel.setPalette(palette)
                self.right_panel.setPalette(palette)

            case "dark":
                palette = QPalette()
                palette.setColor(QPalette.ColorRole.Window, "black")
                self.top_controls_panel.setPalette(palette)
                self.right_panel.setPalette(palette)

    def closeEvent(self, event):
        self.app.worker.messages.put(WorkerMessage.Quit())
        super().closeEvent(event)

    def connect_to_board(self):
        from hspro.gui.board_selector_dialog import BoardSelectorDialog
        from hspro_api.conn.connection_op import connect as raw_connect

        connections = raw_connect(debug=False)
        num_connections = len(connections)
        if num_connections == 0:
            res = QMessageBox.question(None, "Start in demo mode?", "No HaasoscopePro found. Start in \"demo\" mode?")
            if res != QMessageBox.StandardButton.Yes:
                self.exit_app()

        elif num_connections == 1:
            self.connect_to_selected_board(connections[0])

        elif num_connections > 1:
            # ask user to select one
            board_selector_dialog = BoardSelectorDialog(self, connections)
            board_selector_dialog.exec_()
            if board_selector_dialog.selected_connection is None:
                self.exit_app()
            else:
                self.connect_to_selected_board(board_selector_dialog.selected_connection)

    def connect_to_selected_board(self, connection: Connection):
        progress = QProgressDialog("Initializing oscilloscope", "Abort", 0, 0, None)
        progress.setWindowTitle("Initializing oscilloscope")
        bar = QProgressBar(progress)
        bar.setTextVisible(False)
        bar.setMaximum(0)
        bar.setMaximum(10)
        progress.setBar(bar)
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setValue(0)

        def close_app():
            if progress.wasCanceled():
                self.exit_app()

        progress.canceled.connect(close_app)

        self.app.model.link_to_live_board(
            mk_board(
                connection, debug=False, debug_spi=False, show_board_call_trace=False,
                progress_callback=lambda i: progress.setValue(i)
            )
        )
        self.app.set_connection_status_label("Connected")
        progress.wasCanceled = lambda: False
        progress.close()

    def exit_app(self):
        self.app.worker.messages.put(WorkerMessage.Quit())
        exit(1)
