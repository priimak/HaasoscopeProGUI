from typing import Callable

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtWidgets import QWidget
from pyqtgraph import GraphicsLayoutWidget, AxisItem, PlotDataItem, ViewBox
from pyqtgraph.graphicsItems.PlotItem import PlotItem
from pytide6 import Dialog, VBoxLayout, set_geometry

from hspro.gui.gui_ext.fn import mkPen


class ZoomPlotsPanel(GraphicsLayoutWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        from hspro.gui.app import App
        self.app: App = app

        self.app.waveforms_updated = self.waveforms_updated

        self.pens = [mkPen(ch.color) for ch in self.app.model.channel]
        self.traces = [PlotDataItem(), PlotDataItem()]

        self.plot: PlotItem = self.addPlot(0, 0)
        self.plot.setMenuEnabled(False)
        self.plot.yChanged.connect(self.zoom_y_bounds_changed)

        x_axis: AxisItem = self.plot.axes["bottom"]["item"]
        x_axis.setTicks([[], []])
        x_axis.showLabel(True)
        x_axis.setVisible(False)
        self.vbox: ViewBox = x_axis.linkedView()
        self.vbox.sigXRangeChanged.connect(self.zoom_x_bounds_changed)

        y_axis: AxisItem = self.plot.axes["left"]["item"]
        y_axis.setTicks([[], []])
        y_axis.showLabel(True)
        y_axis.setVisible(False)
        self.hbox: ViewBox = y_axis.linkedView()
        self.hbox.sigYRangeChanged.connect(self.zoom_y_bounds_changed)

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

        self.app.set_channel_color_in_zoom_window = self.channel_color_changed

    def update_zoom_bounds(self, view_bounds: QRectF):
        self.vbox.setXRange(view_bounds.left(), view_bounds.right(), padding=0)
        self.hbox.setYRange(view_bounds.top(), view_bounds.bottom(), padding=0)

    def zoom_x_bounds_changed(self, a: ViewBox, b):
        xmin, xmax = self.vbox.viewRange()[0]
        ymin, ymax = self.hbox.viewRange()[1]
        self.app.do_update_zoom_rect_on_main_plot(QRectF(QPointF(xmin, ymax), QPointF(xmax, ymin)))

    def zoom_y_bounds_changed(self, a, b):
        xmin, xmax = self.vbox.viewRange()[0]
        ymin, ymax = self.hbox.viewRange()[1]
        self.app.do_update_zoom_rect_on_main_plot(QRectF(QPointF(xmin, ymax), QPointF(xmax, ymin)))

    def waveforms_updated(self):
        for i, wf in enumerate(self.app.last_plotted_waveforms):
            if wf is None:
                self.traces[i].setVisible(False)
            else:
                self.traces[i].setData(wf.get_t_vec(self.app.model.visual_time_scale.time_unit), wf.vs)
                self.traces[i].setVisible(True)

    def channel_color_changed(self, channel: int, color: str, select_channel: bool):
        self.pens[channel].setColor(color)
        self.traces[channel].setPen(self.pens[channel])


class ZoomDialog(Dialog):
    def __init__(self, parent: QWidget, app, on_close: Callable[[], None]):
        super().__init__(parent, windowTitle="Zoom")
        from hspro.gui.app import App
        self.app: App = app
        self.on_close = on_close
        self.setObjectName("ZoomDialog")

        self.zoom_panel = ZoomPlotsPanel(self, app)
        self.setLayout(VBoxLayout([self.zoom_panel]))
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

    def update_zoom_bounds(self, view_bounds: QRectF):
        self.zoom_panel.update_zoom_bounds(view_bounds)

    def set_plot_color_scheme(self, plot_color_scheme: str):
        match plot_color_scheme:
            case "light":
                self.zoom_panel.setBackground("white")
            case "dark":
                self.zoom_panel.setBackground("black")

    def channel_color_changed(self, channel: int, color: str, select_channel: bool):
        self.zoom_panel.channel_color_changed(channel, color, select_channel)
