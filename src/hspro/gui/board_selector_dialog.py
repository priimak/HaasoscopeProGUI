from PySide6.QtWidgets import QRadioButton, QLabel, QVBoxLayout
from hspro_api.conn.connection import Connection
from pytide6 import Dialog, PushButton, W, HBoxPanel


class BoardSelectorDialog(Dialog):
    def __init__(self, parent, connections: list[Connection]):
        super().__init__(parent, windowTitle="Select board to connect to", modal=True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Found multiple boards. Please select one to connect to."))

        self.selected_connection: Connection | None = None

        self.radio_buttons = []
        for connection in connections:
            board_b = QRadioButton(f"#{connection.board}")
            board_b.toggled.connect(self.handle_radio_button(board_b))
            self.radio_buttons.append(board_b)
            layout.addWidget(board_b)

        def on_ok():
            for rb in self.radio_buttons:
                if rb.isChecked():
                    board_num = int(rb.text().replace("#", ""))
                    for connection in connections:
                        if connection.board == board_num:
                            self.selected_connection = connection
                            break
                    break
            self.close()

        layout.addWidget(HBoxPanel([
            W(HBoxPanel(), stretch=1),
            PushButton("Ok", on_clicked=on_ok),
            PushButton("Cancel", on_clicked=self.close)
        ]))

    def handle_radio_button(self, b: QRadioButton):
        def do_handle():
            all_other_buttons_state = not b.isChecked()

            for radio_button in self.radio_buttons:
                if radio_button != b:
                    radio_button.setChecked(all_other_buttons_state)

        return do_handle
