from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDoubleSpinBox


class HSProDoubleSpinBox(QDoubleSpinBox):
    """ Suppresses all keyboard events except keys Up and Down. """

    def keyPressEvent(self, event, /):
        if event.key() in [Qt.Key.Key_Up, Qt.Key.Key_Down]:
            super().keyPressEvent(event)
