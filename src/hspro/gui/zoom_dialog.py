from typing import Callable

from PySide6.QtWidgets import QWidget
from pyqtgraph import GraphicsLayoutWidget, AxisItem, PlotDataItem
from pyqtgraph.graphicsItems.PlotItem import PlotItem
from pytide6 import Dialog, VBoxLayout, set_geometry

from hspro.gui.gui_ext.fn import mkPen


class ZoomPlotsPanel(GraphicsLayoutWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        from hspro.gui.app import App
        self.app: App = app
        self.pens = [mkPen(ch.color) for ch in self.app.model.channel]
        self.traces = [PlotDataItem(), PlotDataItem()]

        self.plot: PlotItem = self.addPlot(0, 0)
        self.plot.setMenuEnabled(False)

        x_axis: AxisItem = self.plot.axes["bottom"]["item"]
        x_axis.setTicks([[], []])
        x_axis.showLabel(True)
        x_axis.setVisible(False)

        y_axis: AxisItem = self.plot.axes["left"]["item"]
        y_axis.setTicks([[], []])
        y_axis.showLabel(True)
        y_axis.setVisible(False)

        self.plot.autoBtn.setEnabled(False)
        self.plot.autoBtn.setVisible(False)
        self.plot.autoBtn.show = lambda: None
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(False, False)

        for i, trace in enumerate(self.traces):
            trace.setPen(self.pens[i])
            trace.setVisible(self.app.model.channel[i].active)
            self.plot.addItem(trace)
            wf = self.app.last_plotted_waveforms[i]
            if wf is not None:
                self.traces[i].setData(wf.get_t_vec(self.app.model.visual_time_scale.time_unit), wf.vs)


class ZoomDialog(Dialog):
    def __init__(self, parent: QWidget, app, on_close: Callable[[], None]):
        super().__init__(parent, windowTitle="Zoom")
        from hspro.gui.app import App
        self.app: App = app
        self.on_close = on_close
        self.setObjectName("ZoomDialog")

        zoom_panel = ZoomPlotsPanel(self, app)
        self.setLayout(VBoxLayout([zoom_panel]))
        set_geometry(app_state=app.app_persistence.state, widget=self, screen_dim=app.screen_dim, win_size_fraction=0.3)

    def moveEvent(self, event, /):
        super().moveEvent(event)
        self.app.app_persistence.state.save_geometry(self.objectName(), self.saveGeometry())

    def resizeEvent(self, arg__1, /):
        super().resizeEvent(arg__1)
        self.app.app_persistence.state.save_geometry(self.objectName(), self.saveGeometry())

    def closeEvent(self, arg__1, /):
        super().closeEvent(arg__1)
        self.on_close()

    def keyPressEvent(self, e, /):
        pass
