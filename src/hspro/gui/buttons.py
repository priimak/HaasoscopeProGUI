from typing import Callable

from PySide6.QtWidgets import QLabel


class CButton(QLabel):
    CSS1 = "QLabel {border: 1px solid black; background-color: #CACACA;} QLabel::hover {background-color: black; " \
           "color: white;}"
    CSS2 = "QLabel {background-color: #114cb9;  color: white;} QLabel::hover {background-color: white; color: black;}"

    def __init__(self, text: str, on_click: Callable[[], None], css=CSS1):
        super().__init__(None)
        self.on_click = on_click
        self.setText(text)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(css)

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        self.on_click()


class ZeroButton(CButton):
    def __init__(self, on_click: Callable[[], None]):
        super().__init__("∅", on_click)


class UpButton(CButton):
    def __init__(self, on_click: Callable[[], None]):
        super().__init__("▲", on_click, css=CButton.CSS2)
        self.setContentsMargins(5, 0, 5, 0)


class DownButton(CButton):
    def __init__(self, on_click: Callable[[], None]):
        super().__init__("▼", on_click, css=CButton.CSS2)
        self.setContentsMargins(5, 0, 5, 0)
