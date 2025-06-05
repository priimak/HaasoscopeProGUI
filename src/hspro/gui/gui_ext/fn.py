from PySide6.QtGui import QPen


def mkPen(color: str) -> QPen:
    pen = QPen()
    pen.setCosmetic(True)
    pen.setWidth(2)
    pen.setColor(color)
    return pen
