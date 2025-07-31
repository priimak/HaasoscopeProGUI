from PySide6.QtGui import QAction
from PySide6.QtGui import QPalette
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from pytide6 import Panel
from pytide6.palette import Palette

from hspro.gui.app import App, WorkerMessage
from hspro.gui.gui_ext.container import ValueContainer


class MainToolBar(Panel[QHBoxLayout]):
    def __init__(self, app: App):
        super().__init__(QHBoxLayout())
        self.setObjectName("MainToolBar")
        self.setPalette(Palette(QPalette.ColorRole.Window, "#fafafa"))
        self.setAutoFillBackground(True)

        self.addWidget(QLabel(
            "<b><h1 style=\"color: blue;\">Haasoscope<em style=\"color: red;\">Pro</em>&nbsp;&nbsp;</h1></b>"
        ))

        self.current_selection = None
        self.buttons = []

        icon_zoom = ValueContainer(app.icon_zoom_inactive_svg)
        icon_zoom_hoover = ValueContainer(app.icon_zoom_inactive_hoover_svg)
        icon_zoom_pressed = ValueContainer(app.icon_zoom_inactive_pressed_svg)

        zoom_button = QSvgWidget(None)
        zoom_button.load(icon_zoom())

        zoom_button.setToolTip("Enable/Disable zoom operation")
        zoom_button.setToolTipDuration(3000)

        zoom_button.enterEvent = lambda _: zoom_button.load(icon_zoom_hoover())
        zoom_button.leaveEvent = lambda _: zoom_button.load(icon_zoom())
        zoom_button.mousePressEvent = lambda _: zoom_button.load(icon_zoom_pressed())

        def toggle_zoom(_):
            match app.current_active_tool:
                case "Zoom":
                    app.current_active_tool = ""
                    icon_zoom.value = app.icon_zoom_inactive_svg
                    icon_zoom_hoover.value = app.icon_zoom_inactive_hoover_svg
                    icon_zoom_pressed.value = app.icon_zoom_inactive_pressed_svg
                case _:
                    app.current_active_tool = "Zoom"
                    icon_zoom.value = app.icon_zoom_active_svg
                    icon_zoom_hoover.value = app.icon_zoom_active_hoover_svg
                    icon_zoom_pressed.value = app.icon_zoom_active_pressed_svg
            zoom_button.load(icon_zoom_hoover())

        zoom_button.mouseReleaseEvent = toggle_zoom

        self.buttons.append(zoom_button)
        self.addWidget(zoom_button)

        self.layout().addWidget(QLabel("        "))

        take_snapshot_button = QSvgWidget(None)
        take_snapshot_button.load(app.icon_snapshot_svg)
        take_snapshot_button.enterEvent = lambda _: take_snapshot_button.load(app.icon_snapshot_hoover_svg)
        take_snapshot_button.leaveEvent = lambda _: take_snapshot_button.load(app.icon_snapshot_svg)
        take_snapshot_button.mousePressEvent = lambda _: take_snapshot_button.load(app.icon_snapshot_pressed_svg)

        def releaseEvent(_):
            take_snapshot_button.load(app.icon_snapshot_hoover_svg)
            app.record_state_in_scene()

        take_snapshot_button.mouseReleaseEvent = releaseEvent
        take_snapshot_button.setToolTip("Take scene snapshot")
        take_snapshot_button.setToolTipDuration(3000)

        self.addWidget(take_snapshot_button)

        icon_hold_release = ValueContainer(app.icon_released_svg)
        icon_hold_release_hoover = ValueContainer(app.icon_released_hoover_svg)
        icon_hold_release_pressed = ValueContainer(app.icon_released_pressed_svg)

        show_hide_button_action: ValueContainer[QAction] = ValueContainer(None)
        icon_show_hide = ValueContainer(app.icon_shown_svg)
        icon_show_hide_hoover = ValueContainer(app.icon_shown_hoover_svg)
        icon_show_hide_pressed = ValueContainer(app.icon_shown_pressed_svg)

        show_hide_button = QSvgWidget(None)
        show_hide_button.setToolTip("Show/Hide held traces")
        hold_release_button = QSvgWidget(None)
        hold_release_button.setToolTip("Hold/Release traces")
        hold_release_button.load(icon_hold_release())
        hold_release_button.enterEvent = lambda _: hold_release_button.load(icon_hold_release_hoover())
        hold_release_button.leaveEvent = lambda _: hold_release_button.load(icon_hold_release())
        hold_release_button.mousePressEvent = lambda _: hold_release_button.load(icon_hold_release_pressed())

        show_hide_button.load(icon_show_hide())
        show_hide_button.enterEvent = lambda _: show_hide_button.load(icon_show_hide_hoover())
        show_hide_button.mousePressEvent = lambda _: show_hide_button.load(icon_show_hide_pressed())

        def toggle_show_hide(_):
            if app.showing_holding_traces:
                icon_show_hide.value = app.icon_hidden_svg
                icon_show_hide_hoover.value = app.icon_hidden_hoover_svg
                icon_show_hide_pressed.value = app.icon_hidden_pressed_svg
                app.worker.messages.put(WorkerMessage.ShowHideHeldWaveforms(False))
                app.showing_holding_traces = False
            else:
                icon_show_hide.value = app.icon_shown_svg
                icon_show_hide_hoover.value = app.icon_shown_hoover_svg
                icon_show_hide_pressed.value = app.icon_shown_pressed_svg
                app.worker.messages.put(WorkerMessage.ShowHideHeldWaveforms(True))
                app.showing_holding_traces = True

            show_hide_button.load(icon_show_hide())

        def toggle_hold_release(_):
            if app.holding:
                icon_hold_release.value = app.icon_released_svg
                icon_hold_release_hoover.value = app.icon_released_hoover_svg
                icon_hold_release_pressed.value = app.icon_released_pressed_svg
                app.holding = False
                app.worker.messages.put(WorkerMessage.ReleaseWaveforms())
                show_hide_button_action().setVisible(False)
            else:
                icon_hold_release.value = app.icon_holding_svg
                icon_hold_release_hoover.value = app.icon_holding_hoover_svg
                icon_hold_release_pressed.value = app.icon_holding_pressed_svg
                app.holding = True
                app.worker.messages.put(WorkerMessage.HoldWaveforms())
                if not app.showing_holding_traces:
                    toggle_show_hide(None)
                show_hide_button_action().setVisible(True)

            hold_release_button.load(icon_hold_release_hoover())

        hold_release_button.mouseReleaseEvent = toggle_hold_release
        self.addWidget(hold_release_button)

        show_hide_button.mouseReleaseEvent = toggle_show_hide
        self.addWidget(show_hide_button)
        show_hide_button_action.value = show_hide_button
        show_hide_button_action().setVisible(False)

        self.layout().addWidget(QLabel(""), stretch=10)
