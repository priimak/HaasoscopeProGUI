from PySide6.QtWidgets import QRadioButton, QLabel, QVBoxLayout
from hspro_api.board import Board
from pytide6 import Dialog, PushButton, W, HBoxPanel


class BoardSelectorDialog(Dialog):
    def __init__(self, parent, boards: list[Board]):
        super().__init__(parent, windowTitle="Select board to connect to", modal=True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Found multiple boards. Please select one to connect to."))

        self.selected_board: Board | None = None

        self.radio_buttons = []
        for board in boards:
            board_b = QRadioButton(f"#{board.board_num}")
            board_b.toggled.connect(self.handle_radio_button(board_b))
            self.radio_buttons.append(board_b)
            layout.addWidget(board_b)

        def on_ok():
            for rb in self.radio_buttons:
                if rb.isChecked():
                    board_num = int(rb.text().replace("#", ""))
                    for board in boards:
                        if board.board_num == board_num:
                            self.selected_board = board
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
