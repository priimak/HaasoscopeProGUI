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
        override_config_if_different_version=True,
        init_config_data={
            "config_version": 14,
            "plot_color_scheme": "dark",
            "show_trigger_level_line": False,
            "show_trigger_position_line": False,
            "show_grid": True,
            "show_y_axis_labels": True,
            "show_zero_line": True,
            "general": {
                "highres": True,
                "mem_depth": 100,
                "delay": 0,
                "f_delay": 0,
                "visual_time_scale": "1 us"
            },
            "trigger": {
                "on_channel": 0,
                "trigger_type": "Rising Edge",
                "tot": 2,
                "delta": 2,
                "level": 0.0,
                "position": 0.5,
                "auto_frequency": "5 Hz"
            },
            "channels": {
                "0": {
                    "active": True,
                    "color": "#ffee2e",
                    "offset_V": 0.0,
                    "dV": 0.2,
                    "coupling": ChannelCouplingModel.DC.value,
                    "impedance": ChannelImpedanceModel.FIFTY_OHM.value,
                    "ten_x_probe": False,
                    "five_x_attenuation": False
                },
                "1": {
                    "active": False,
                    "color": "#40cc1a",
                    "offset_V": 0.0,
                    "dV": 0.2,
                    "coupling": ChannelCouplingModel.DC.value,
                    "impedance": ChannelImpedanceModel.FIFTY_OHM.value,
                    "ten_x_probe": False,
                    "five_x_attenuation": False
                }
            }
        }
    )

    win = HSProMainWindow(screen_dim=(screen_width, screen_height), app_persistence=persistence)
    win.show()
    win.activateWindow()
    win.raise_()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
