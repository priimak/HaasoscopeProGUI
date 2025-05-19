from typing import Callable

from PySide6.QtCore import QStringListModel, QItemSelection
from PySide6.QtWidgets import QMenu, QMenuBar, QWidget, QListView, QAbstractItemView
from pytide6 import Dialog, VBoxLayout

from hspro.gui.app import App
from hspro.gui.scene import Scene


class SceneHistory(Dialog):
    def __init__(self, parent: QWidget, app: App, on_close: Callable[[], None]):
        super().__init__(parent, windowTitle="Scene history")
        self.on_close = on_close
        self.hist_model = QStringListModel()

        num_checkpoints = len(app.scene.data)
        items = [f"Checkpoint #{num_checkpoints - i}" for i in range(len(app.scene.data))]
        self.hist_model.setStringList(items)

        self.lst_view = QListView()
        self.lst_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lst_view.setModel(self.hist_model)
        self.lst_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        def selectionChanged(selected: QItemSelection, _):
            if selected.count() > 0:
                selected_row = selected.first().indexes()[0].row()
                app.activate_scene_checkpoint(len(app.get_scene().data) - selected_row)

        self.lst_view.selectionModel().selectionChanged.connect(selectionChanged)
        self.setLayout(VBoxLayout([self.lst_view]))

    def closeEvent(self, arg__1, /):
        super().closeEvent(arg__1)
        self.on_close()


class SceneMenu(QMenu):
    def __init__(self, parent: QMenuBar, app: App):
        super().__init__("&Scene", parent)
        self.app = app

        self.addAction("&New scene", app.create_new_scene)
        self.addAction("&Open scene", app.open_scene)
        self.addAction("&Show scene history", self.show_history)
        self.addAction("&Take scene snapshot", app.record_state_in_scene)
        self.scene_history_windows: list[SceneHistory] = []

        self.app.update_scene_history_dialog = self.update_scene_history_dialog

        def show_and_update_scene_history():
            self.show_history()
            self.update_scene_history_dialog(self.app.scene)

        self.app.show_scene_history = show_and_update_scene_history

    def show_history(self):
        if self.scene_history_windows == []:
            hist = SceneHistory(self.app.main_window(), self.app, on_close=self.scene_history_windows.clear)
            self.scene_history_windows.append(hist)
            hist.show()
        else:
            self.scene_history_windows[0].showNormal()
            self.scene_history_windows[0].activateWindow()
            self.scene_history_windows[0].raise_()

    def update_scene_history_dialog(self, scene: Scene):
        if self.scene_history_windows != []:
            num_checkpoints = len(scene.data)
            items = [f"Checkpoint #{num_checkpoints - i}" for i in range(len(scene.data))]
            self.scene_history_windows[0].hist_model.setStringList(items)
