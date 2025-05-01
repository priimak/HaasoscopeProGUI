from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QMessageBox, QProgressDialog, QProgressBar
from hspro_api.board import mk_board
from hspro_api.conn.connection import Connection
from pytide6 import MainWindow, set_geometry, VBoxPanel, W, HBoxPanel, Label
from sprats.config import AppPersistence

from hspro.gui.app import App, WorkerMessage
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

        set_geometry(app_state=app_persistence.state, widget=self, screen_dim=screen_dim, win_size_fraction=0.7)

        self.menu_bar = self.setMenuBar(MainMenuBar(self.app))

        self.glw = PlotsPanel(self, self.app)

        right_panel = VBoxPanel(
            widgets=[TriggerPanel(self.app), GeneralOptionsPanel(self.app), W(Label(""), stretch=10)],
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
        self.connect_to_board()
        self.app.model.init_board_from_model()
        self.app.worker.messages.put(
            WorkerMessage.ArmAuto(self.app.model.trigger.trigger_type.to_trigger_type(), drain_queue=False)
        )
        self.app.worker.messages.put(WorkerMessage.SetTriggerPosition(self.app.model.trigger.position_live))

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
