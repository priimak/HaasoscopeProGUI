from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDoubleSpinBox, QWidget, QLineEdit
from pytide6 import HBoxLayout

from hspro.gui.app import App
from hspro.gui.buttons import UpButton, DownButton


class HSProDoubleSpinBox(QDoubleSpinBox):
    """ Suppresses all keyboard events except keys Up and Down. """

    def keyPressEvent(self, event, /):
        if event.key() in [Qt.Key.Key_Up, Qt.Key.Key_Down]:
            super().keyPressEvent(event)


class SpinnerLineEdit(QLineEdit):
    def __init__(self, parent, /):
        super().__init__()
        self.parent_spinbox = parent

    def keyPressEvent(self, event, /):
        match event.key():
            case Qt.Key.Key_Up:
                self.parent_spinbox.stepBy(1)
            case Qt.Key.Key_Down:
                self.parent_spinbox.stepBy(-1)

    def wheelEvent(self, event, /):
        super().wheelEvent(event)
        steps = int(event.angleDelta().y() / 64)
        self.parent_spinbox.stepBy(steps)


class HSProSpinBox(QWidget):
    def __init__(self, app: App):
        super().__init__()

        self.input = SpinnerLineEdit(self)
        self.setLayout(HBoxLayout(
            widgets=[
                self.input,
                UpButton(lambda: self.stepBy(1)),
                DownButton(lambda: self.stepBy(-1)),
            ],
            margins=(3, 0, 3, 0),
            spacing=3
        ))
        self.__suffix = ""
        self.__decimals = 0
        self.__format = "{value:.2f}"
        self.__value = 0
        self.__minimum = 0
        self.__maximum = 100
        self.setValue(0)
        self.setAutoFillBackground(True)
        self.setPalette(app.side_pannels_palette())

    def setDecimals(self, prec: int):
        self.__decimals = prec
        self.__format = "{value:" + f".{prec}f" + "}"

    def stepBy(self, steps) -> None:
        pass

    def setValue(self, value: float) -> None:
        self.__value = value
        self.input.setText(self.__format.format(value=value) + self.__suffix)

    def setSuffix(self, suffix: str) -> None:
        self.__suffix = suffix
        self.setValue(self.__value)

    def setMinimum(self, minimum: float) -> None:
        self.__minimum = minimum

    def setMaximum(self, maximum: float) -> None:
        self.__maximum = maximum
