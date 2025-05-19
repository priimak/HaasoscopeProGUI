from PySide6.QtCore import QStringListModel, QItemSelection
from PySide6.QtWidgets import QMenu, QMenuBar, QWidget, QListView, QAbstractItemView
from pytide6 import Dialog, VBoxLayout

from hspro.gui.app import App


# class SceneHistoryModel(QAbstractListModel):
#     def __init__(self, parent: QWidget, app: App):
#         super().__init__(parent)
#         self.app = app
#         # checkpoints = reversed(app.scene.data)
#
#     def rowCount(self):
#         return len(self.app.scene.data)
#
#     def data(self, index, /, role=...):
#         if role == Qt.DisplayRole:
#             idx = len(self.app.scene.data) - index.row()
#             return f"{idx}"

class SceneHistory(Dialog):
    def __init__(self, parent: QWidget, app: App):
        super().__init__(parent, windowTitle="Scene history")

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


class SceneMenu(QMenu):
    def __init__(self, parent: QMenuBar, app: App):
        super().__init__("&Scene", parent)
        self.app = app

        self.addAction("&New scene", app.create_new_scene)
        self.addAction("&Open scene", app.open_scene)
        self.addAction("Show scene &history", self.show_history)
        self.addAction("&Record state in scene", app.record_state_in_scene)

    def show_history(self):
        hist = SceneHistory(self, self.app)
        hist.show()
