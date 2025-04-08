import math

from PyQt5.QtCore import QPointF
from PySide6.QtGui import QPen, Qt, QFontDatabase
from pyqtgraph import AxisItem, GraphicsLayoutWidget, InfiniteLine, PlotDataItem, TextItem
from pyqtgraph.graphicsItems.PlotItem import PlotItem
from pyqtgraph.graphicsItems.ViewBox import ViewBox

from hspro.gui.app import App


class PlotsPanel(GraphicsLayoutWidget):
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app
        self.app.set_plot_color_scheme = self.set_plot_color_scheme
        self.pens = [self.mkPen(ch.color) for ch in self.app.model.channel]

        self.plot: PlotItem = self.addPlot(0, 0)
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(True, True, 0.4)
        self.app.set_show_grid_state = lambda show_grid: self.plot.showGrid(show_grid, show_grid, 0.4)

        x_axis: AxisItem = self.plot.axes["bottom"]["item"]
        x_axis.setZValue(1)  # grid will appear above traces
        x_axis.setTicks(
            [[(1, ""), (2, ""), (3, ""), (4, ""), (5, ""), (6, ""), (7, ""), (8, ""), (9, ""), (10, "")], []]
        )

        y_axis: AxisItem = self.plot.axes["left"]["item"]
        y_axis.setRange(0, 9)
        y_axis.setZValue(1)  # grid will appear above traces
        y_axis.setTicks(
            [
                [(-5, ""), (-4, ""), (-3, ""), (-2, ""), (-1, ""), (0, ""), (1, ""), (2, ""), (3, ""), (4, ""),
                 (5, "")],
                []
            ]
        )

        vbox: ViewBox = x_axis.linkedView()
        vbox.setMouseEnabled(False, False)
        vbox.setRange(xRange=(0, 10), yRange=(-5, 5), padding=0)

        self.zero_h_line = InfiniteLine(pos=0, movable=False, angle=0, pen=(0, 0, 200), span=(0, 1))
        self.plot.addItem(self.zero_h_line)
        self.app.set_show_zero_line_state = lambda show_zero_line: self.zero_h_line.setVisible(show_zero_line)

        self.trigger_lines_pen = QPen()
        self.trigger_lines_pen.setCosmetic(True)
        self.trigger_lines_pen.setColor("#0000FF")
        self.trigger_lines_pen.setWidth(1)
        self.trigger_lines_pen.setStyle(Qt.PenStyle.CustomDashLine)
        self.trigger_lines_pen.setDashPattern([8, 8])

        self.trigger_pos_line = InfiniteLine(
            pos=10 * app.model.trigger.position,
            movable=True, angle=90, pen=self.trigger_lines_pen
        )
        self.plot.addItem(self.trigger_pos_line)
        self.trigger_pos_line.xChanged.connect(self.set_trigger_pos_from_plot_line)
        self.app.set_trigger_pos_from_side_controls = lambda pos: self.trigger_pos_line.setPos(10 * pos)

        self.trigger_level_line = InfiniteLine(
            pos=5 * app.model.trigger.level,
            movable=True, angle=0, pen=self.trigger_lines_pen
        )
        self.plot.addItem(self.trigger_level_line)
        self.trigger_level_line.yChanged.connect(self.set_trigger_level_from_plot_line)
        self.app.set_trigger_level_from_side_controls = lambda level: self.trigger_level_line.setPos(5 * level)
        self.app.set_trigger_level_line_visible = self.trigger_level_line.setVisible

        self.black_pen = QPen()
        self.black_pen.setCosmetic(True)
        self.black_pen.setColor("#000000")

        self.blue_pen = QPen()
        self.blue_pen.setCosmetic(True)
        self.blue_pen.setColor("#0000C8")

        x = [0.01 * i for i in range(-100, 3000)]
        y = [t / 4 * math.sin(t) for t in x]

        demo_trace_1 = PlotDataItem(x, y)
        demo_trace_1.setPen(self.pens[0])
        demo_trace_1.setVisible(app.model.channel[0].active)

        y = [(t + 1) / 4 * math.cos(t) for t in x]

        demo_trace_2 = PlotDataItem(x, y)
        demo_trace_2.setPen(self.pens[1])
        demo_trace_2.setVisible(app.model.channel[1].active)
        self.demo_trace = [demo_trace_1, demo_trace_2]
        self.plot.addItem(demo_trace_1)
        self.plot.addItem(demo_trace_2)

        self.app.set_channel_active_state = self.channel_active_state_changed
        self.app.set_channel_color = self.channel_color_changed

        self.value_label = TextItem("", color=(0, 0, 0), border=(0, 0, 0), fill=(255, 255, 255))
        self.value_label.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.value_label.setPos(0.1, 4.9)
        self.value_label.setZValue(5)
        self.value_label.setVisible(False)
        self.plot.addItem(self.value_label)

        self.setMouseTracking(True)
        self.plot.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.plot.setCursor(Qt.CursorShape.CrossCursor)
        self.plot.getAxis('bottom').setZValue(-1)

    def on_mouse_moved(self, evt: QPointF):
        pos = evt
        if self.plot.sceneBoundingRect().contains(pos):
            self.value_label.setVisible(True)
            mousePoint = self.plot.vb.mapSceneToView(pos)
            label = f"{mousePoint.x():.3}, {mousePoint.y():.3}"
            self.value_label.setText(label + " " * (13 - len(label)))
        else:
            self.value_label.setVisible(False)

    def leaveEvent(self, ev):
        super().leaveEvent(ev)
        self.value_label.setVisible(False)

    def set_plot_color_scheme(self, plot_color_scheme: str):
        match plot_color_scheme:
            case "light":
                self.setBackground("white")
                self.trigger_lines_pen.setColor("#0000FF")
                self.trigger_level_line.setPen(self.trigger_lines_pen)
                self.trigger_pos_line.setPen(self.trigger_lines_pen)
                self.zero_h_line.setPen(self.black_pen)
                self.app.app_persistence.config.set_value("plot_color_scheme", "light")
            case "dark":
                self.setBackground("black")
                self.trigger_lines_pen.setColor("#FFFFFF")
                self.trigger_level_line.setPen(self.trigger_lines_pen)
                self.trigger_pos_line.setPen(self.trigger_lines_pen)
                self.zero_h_line.setPen(self.blue_pen)
                self.app.app_persistence.config.set_value("plot_color_scheme", "dark")

    def set_trigger_level_from_plot_line(self):
        self.app.set_trigger_level_from_plot_line(self.trigger_level_line.y())

    def set_trigger_pos_from_plot_line(self):
        self.app.set_trigger_pos_from_plot_line(self.trigger_pos_line.x())

    def mkPen(self, color: str):
        pen = QPen()
        pen.setCosmetic(True)
        pen.setWidth(2)
        pen.setColor(color)
        return pen

    def channel_active_state_changed(self, channel: int, active: bool):
        self.demo_trace[channel].setVisible(active)

    def channel_color_changed(self, channel: int, color: str):
        self.pens[channel].setColor(color)
        self.demo_trace[channel].setPen(self.pens[channel])
