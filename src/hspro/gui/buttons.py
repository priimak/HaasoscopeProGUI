from typing import Callable

from PySide6.QtWidgets import QLabel


class CButton(QLabel):
    def __init__(self, text: str, on_click: Callable[[], None]):
        super().__init__(None)
        self.on_click = on_click
        self.setText(text)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(
            "QLabel {border: 1px solid black; background-color: #CACACA;}"
            "QLabel::hover {background-color: black; color: white;}"
        )

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        self.on_click()


class ZeroButton(CButton):
    def __init__(self, on_click: Callable[[], None]):
        super().__init__("∅", on_click)
