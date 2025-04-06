from PySide6.QtWidgets import QMenu, QMenuBar, QMessageBox


class HelpMenu(QMenu):
    def __init__(self, parent: QMenuBar):
        super().__init__("&Help", parent)

        # In QMessageBox.about(parent = None, ...) will place message window at the center of the screen
        self.addAction(
            "&About",
            lambda: QMessageBox.about(
                None,
                "About",
                f"<html><H2><em>Haasoscope Pro GUI</em></H2><br/>"
                "<p style=\"font-size:14px;\">“We are at the very beginning of time for the human race. "
                "It is not unreasonable that we grapple with problems. But there are tens of thousands of "
                "years in the future. Our responsibility is to do what we can, learn what we can, improve "
                "the solutions, and pass them on.”  "
                "</br>&nbsp;&nbsp;&nbsp;&nbsp;- <em>Richard P. Feynman </em></p></html>"
            )
        )
