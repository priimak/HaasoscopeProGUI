import sys
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from sprats.config import AppPersistence

from hspro.gui.main_window import HSProMainWindow
from hspro.gui.model import ChannelCouplingModel, ChannelImpedanceModel


def main():
    app = QApplication(sys.argv)
    tt_png = Path(__file__).parent / "tt.png"
    app.setWindowIcon(QIcon(f"{tt_png.absolute()}"))

    # Will init main window size to be some fraction of the screen size unless defined elsewhere
    screen_dim: QSize = app.primaryScreen().size()
    screen_width, screen_height = screen_dim.width(), screen_dim.height()

    persistence = AppPersistence(
        app_name="hspro",
        init_config_data={
            "plot_color_scheme": "light",
            "general": {
                "highres": True,
                "mem_depth": 100
            },
            "trigger": {
                "on_channel": 0,
                "trigger_type": "Rising Edge",
                "tot": 2,
                "delta": 0,
                "level": 0.0,
                "position": 0.5
            },
            "channels": {
                "1": {
                    "active": True,
                    "color": "#ff0000",
                    "offset_V": 0.0,
                    "dV": 0.160,
                    "coupling": ChannelCouplingModel.DC.value,
                    "impedance": ChannelImpedanceModel.FIFTY_OHM.value,
                    "ten_x_probe": False,
                    "five_x_attenuation": False
                },
                "2": {
                    "active": False,
                    "color": "#0000ff",
                    "offset_V": 0.0,
                    "dV": 0.160,
                    "coupling": ChannelCouplingModel.DC.value,
                    "impedance": ChannelImpedanceModel.FIFTY_OHM.value,
                    "ten_x_probe": False,
                    "five_x_attenuation": False
                }
            }
        }
    )

    if persistence.config.get_by_xpath("/general/delay", int) is None:
        persistence.config.set_by_xpath("/general/delay", 0)

    if persistence.config.get_by_xpath("/general/f_delay", int) is None:
        persistence.config.set_by_xpath("/general/f_delay", 0)

    win = HSProMainWindow(screen_dim=(screen_width, screen_height), app_persistence=persistence)
    win.show()
    win.activateWindow()
    win.raise_()
    win.connect_to_board()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
