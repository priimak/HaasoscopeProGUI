import time
from functools import cache
from typing import Optional

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, Qt, QFontDatabase, QColor, QBrush
from hspro_api import Waveform
from pyqtgraph import AxisItem, GraphicsLayoutWidget, InfiniteLine, PlotDataItem, TextItem, ArrowItem
from pyqtgraph.graphicsItems.PlotItem import PlotItem
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from unlib import Duration

from hspro.gui.app import App, WorkerMessage
from hspro.gui.gui_ext.arrows import XArrowItem


class TriggerPositionLine(InfiniteLine):
    def __init__(self, pen: QPen):
        super().__init__(pos=0, movable=True, angle=90, pen=pen)
        self.setZValue(10)


class PlotsPanel(GraphicsLayoutWidget):
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app
        self.app.set_plot_color_scheme = self.set_plot_color_scheme
        self.pens = [self.mkPen(ch.color) for ch in self.app.model.channel]
        self.brushes = [QBrush(ch.color) for ch in self.app.model.channel]
        self.do_show_trig_level_line = self.app.app_persistence.config.get_by_xpath("/show_trigger_level_line", bool)
        self.do_show_trig_pos_line = self.app.app_persistence.config.get_by_xpath("/show_trigger_position_line", bool)
        self.corrected_trigger_position = [0.0]

        self.trigger_lines_color_map = "Matching Trigger Channel"
        # self.setContentsMargins(30, 30, 30, 30)

        self.plot: PlotItem = self.addPlot(0, 0)
        self.plot.setMenuEnabled(False)

        show_grid_p = self.app.app_persistence.config.get_by_xpath("/show_grid")
        self.plot.showGrid(show_grid_p, show_grid_p, 0.4)

        def show_grid(show: bool):
            self.plot.showGrid(show, show, 0.4)
            self.app.app_persistence.config.set_by_xpath("/show_grid", show)

        self.app.set_show_grid_state = show_grid

        self.x_axis: AxisItem = self.plot.axes["bottom"]["item"]
        self.x_axis.setZValue(1)  # grid will appear above traces
        self.x_axis.setTicks(
            [[(1, ""), (2, ""), (3, ""), (4, ""), (5, ""), (6, ""), (7, ""), (8, ""), (9, ""), (10, "")], []]
        )
        self.x_axis.showLabel(True)
        self.x_axis.setLabel("ms")

        self.y_axis: AxisItem = self.plot.axes["left"]["item"]
        self.y_axis.setRange(0, 9)
        self.y_axis.setZValue(1)  # grid will appear above traces
        self.y_axis.setTicks(
            [
                [(-5, ""), (-4, ""), (-3, ""), (-2, ""), (-1, ""), (0, ""), (1, ""), (2, ""), (3, ""), (4, ""),
                 (5, "")],
                []
            ]
        )
        # self.y_axis.showLabel(True)
        # self.y_axis.setLabel("V")

        self.vbox: ViewBox = self.x_axis.linkedView()
        self.vbox.setMouseEnabled(False, False)
        self.vbox.setRange(xRange=(0, 10), yRange=(-5, 5), padding=0)

        # self.zero_h_line = InfiniteLine(pos=0, movable=False, angle=0, pen=(0, 0, 200), span=(0, 1))
        # self.plot.addItem(self.zero_h_line)
        # self.app.set_show_zero_line_state = lambda show_zero_line: self.zero_h_line.setVisible(show_zero_line)

        self.trigger_lines_pen = QPen()
        self.trigger_lines_pen.setCosmetic(True)
        self.trigger_lines_pen.setColor(QColor(0, 0, 0xff, 100))
        self.trigger_lines_pen.setWidth(1)
        self.trigger_lines_pen.setStyle(Qt.PenStyle.CustomDashLine)
        self.trigger_lines_pen.setDashPattern([8, 8])
        self.trigger_marker_brush = QBrush("white")

        self.trigger_pos_line = TriggerPositionLine(pen=self.trigger_lines_pen)
        self.trigger_pos_line.setVisible(self.do_show_trig_pos_line)
        self.plot.addItem(self.trigger_pos_line)

        def correct_trigger_position(pos: float):
            self.corrected_trigger_position.clear()
            self.corrected_trigger_position.append(pos)
            self.trigger_pos_marker.setPos(
                self.plot.getViewBox().x() + self.y_axis.getViewBox().x() +
                self.corrected_trigger_position[0] * self.x_axis.width(),
                0
            )

        self.app.correct_trigger_position = correct_trigger_position
        self.trigger_pos_line.sigPositionChangeFinished.connect(self.set_trigger_pos_from_plot_line)

        self.trigger_lines_hpen = QPen()
        self.trigger_lines_hpen.setCosmetic(True)
        self.trigger_lines_hpen.setColor(QColor(0, 0, 0xff, 255))
        self.trigger_lines_hpen.setWidth(1)
        self.trigger_lines_hpen.setStyle(Qt.PenStyle.SolidLine)

        self.trigger_level_line = InfiniteLine(
            pos=5 * app.model.trigger.level,
            movable=True, angle=0, pen=self.trigger_lines_pen,
            hoverPen=self.trigger_lines_hpen
        )
        self.trigger_level_line.setVisible(self.do_show_trig_level_line)
        self.plot.addItem(self.trigger_level_line)

        self.trigger_level_line.sigPositionChangeFinished.connect(self.set_trigger_level_from_plot_line)

        self.app.set_trigger_level_line_visible = self.make_trigger_line_visible
        self.app.set_show_trigger_level_line = self.set_show_trigger_level_line
        self.app.set_show_trig_pos_line = self.set_show_trig_pos_line

        def trig_level_line_temp_vis(visible: bool):
            if visible or not self.do_show_trig_level_line:
                self.trigger_level_line.setVisible(visible)

        self.app.make_trig_level_line_visible_temp = trig_level_line_temp_vis

        def trig_pos_line_temp_vis(visible: bool):
            if visible or not self.do_show_trig_pos_line:
                self.trigger_pos_line.setVisible(visible)

        self.app.make_trig_pos_line_visible_temp = trig_pos_line_temp_vis

        self.app.set_trigger_lines_width = self.set_trigger_lines_width
        self.app.update_trigger_lines_color = self.update_trigger_lines_color
        self.app.set_trigger_lines_color_map = self.set_trigger_lines_color_map

        self.black_pen = QPen()
        self.black_pen.setCosmetic(True)
        self.black_pen.setColor("#000000")

        self.blue_pen = QPen()
        self.blue_pen.setCosmetic(True)
        self.blue_pen.setColor("#0000C8")

        self.traces = [PlotDataItem(), PlotDataItem()]
        # self.zero_markers = [ArrowItem(pos=(1, 1), angle=0, headLen=15, headWidth=10)]
        for i, trace in enumerate(self.traces):
            trace.setPen(self.pens[i])
            trace.setVisible(self.app.model.channel[i].active)
            self.plot.addItem(trace)

        # for i, zm in enumerate(self.zero_markers):
        #     zm.setPen(self.pens[i])
        #     zm.setBrush(self.brushes[i])
        #     zm.setVisible(self.app.model.channel[i].active)
        #     self.plot.addItem(zm)

        self.trigger_level_marker = ArrowItem(
            pos=(9.85, 5 * app.model.trigger.level),
            angle=0, headLen=14, headWidth=10, pxMode=False
        )
        self.trigger_level_marker.setPen(self.trigger_lines_pen)
        self.trigger_level_marker.setBrush(self.trigger_marker_brush)
        # self.plot.addItem(self.trigger_level_marker)

        self.trigger_pos_marker = XArrowItem(
            angle=0, headLen=14, headWidth=10, pxMode=True
        )
        self.trigger_pos_marker.setPen(self.trigger_lines_pen)
        self.trigger_pos_marker.setBrush(self.trigger_marker_brush)
        self.scene().addItem(self.trigger_pos_marker)

        # self.trigger_pos_marker.setPos(QPoint(200, 14))

        def correct_trigger_level_line(pos):
            self.trigger_level_line.setPos(5 * pos)
            self.trigger_level_marker.setY(5 * pos)

        self.app.correct_trigger_level = correct_trigger_level_line

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

        self.update_trigger_lines_color(app.model.trigger.on_channel)
        self.update_trigger_lines_color(app.model.trigger.on_channel)

        self.app.plot_waveforms = self.plot_waveforms
        self.last_plotted_at = time.time()

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
                self.trigger_level_line.setPen(self.trigger_lines_pen)
                self.trigger_pos_line.setPen(self.trigger_lines_pen)
                # self.zero_h_line.setPen(self.black_pen)
                self.app.app_persistence.config.set_value("plot_color_scheme", "light")
            case "dark":
                self.setBackground("black")
                self.trigger_level_line.setPen(self.trigger_lines_pen)
                self.trigger_pos_line.setPen(self.trigger_lines_pen)
                # self.zero_h_line.setPen(self.blue_pen)
                self.app.app_persistence.config.set_value("plot_color_scheme", "dark")

    def set_trigger_level_from_plot_line(self, line):
        self.app.worker.messages.put(WorkerMessage.SetTriggerLevel(line.y() / 5))
        self.app.set_trigger_level_from_plot_line(line.y() / 5)

    def set_trigger_pos_from_plot_line(self, line):
        t_range = 10 * self.app.model.visual_time_scale.value
        t_min = - t_range * self.corrected_trigger_position[0]
        new_trigger_position = (line.x() - t_min) / t_range
        self.app.set_trigger_pos_from_plot_line(new_trigger_position)
        self.app.worker.messages.put(WorkerMessage.SetTriggerPosition(new_trigger_position))
        self.trigger_pos_line.setX(0)

    def mkPen(self, color: str) -> QPen:
        pen = QPen()
        pen.setCosmetic(True)
        pen.setWidth(2)
        pen.setColor(color)
        return pen

    def channel_active_state_changed(self, channel: int, active: bool):
        self.traces[channel].setVisible(active)

    def channel_color_changed(self, channel: int, color: str):
        self.pens[channel].setColor(color)
        self.traces[channel].setPen(self.pens[channel])

    def make_trigger_line_visible(self, visible: bool):
        if self.do_show_trig_level_line:
            self.trigger_level_line.setVisible(visible)

    def set_show_trigger_level_line(self, show_trig_level_line: bool):
        self.app.app_persistence.config.set_by_xpath("/show_trigger_level_line", show_trig_level_line)
        self.trigger_level_line.setVisible(show_trig_level_line)
        self.do_show_trig_level_line = show_trig_level_line

    def set_show_trig_pos_line(self, show_trig_pos_line: bool):
        self.app.app_persistence.config.set_by_xpath("/show_trigger_position_line", show_trig_pos_line)
        self.trigger_pos_line.setVisible(show_trig_pos_line)
        self.do_show_trig_pos_line = show_trig_pos_line

    def set_trigger_lines_width(self, width: int):
        self.trigger_lines_pen.setWidth(width)
        self.trigger_lines_hpen.setWidth(width)

        self.trigger_level_line.setPen(self.trigger_lines_pen)
        self.trigger_level_line.setHoverPen(self.trigger_lines_hpen)
        self.trigger_pos_line.setPen(self.trigger_lines_pen)
        self.trigger_pos_line.setHoverPen(self.trigger_lines_hpen)

    def update_trigger_lines_color(self, on_channel: int):
        match self.trigger_lines_color_map:
            case "Matching Trigger Channel":
                self.trigger_lines_pen.setColor(self.app.model.channel[on_channel].color)
                self.trigger_lines_hpen.setColor(self.app.model.channel[on_channel].color)
            case _:  # Default
                if self.app.plot_color_scheme == "light":
                    self.trigger_lines_pen.setColor("#101010")
                    self.trigger_lines_hpen.setColor(self.app.model.channel[on_channel].color)
                elif self.app.plot_color_scheme == "dark":
                    self.trigger_lines_pen.setColor("#FFFFFF")
                    self.trigger_lines_hpen.setColor(self.app.model.channel[on_channel].color)

        self.trigger_marker_brush.setColor(self.app.model.channel[on_channel].color)
        self.trigger_level_marker.setPen(self.trigger_lines_pen)
        self.trigger_level_marker.setBrush(self.trigger_marker_brush)

        self.trigger_pos_marker.setPen(self.trigger_lines_pen)
        self.trigger_pos_marker.setBrush(self.trigger_marker_brush)

        self.trigger_level_line.setPen(self.trigger_lines_pen)
        self.trigger_level_line.setHoverPen(self.trigger_lines_hpen)
        self.trigger_pos_line.setPen(self.trigger_lines_pen)
        self.trigger_pos_line.setHoverPen(self.trigger_lines_hpen)

    def set_trigger_lines_color_map(self, color_map: str):
        self.trigger_lines_color_map = color_map

    def plot_waveforms(self, ws: tuple[Optional[Waveform], Optional[Waveform]]):
        ts = None
        for i, w in enumerate(ws):
            if w is not None:
                ts = self.get_ts(
                    len_vs=len(w.vs),
                    t_pos=self.corrected_trigger_position[0],
                    board_time_scale=self.app.model.time_scale,
                    visual_time_scale=self.app.model.visual_time_scale
                )
                self.traces[i].setData(ts, w.vs)

        if ts is not None:
            v_scale = self.app.model.visual_time_scale.value
            t_range = 10 * v_scale
            t_max = t_range * (1 - self.corrected_trigger_position[0])
            t_min = - t_range * self.corrected_trigger_position[0]
            current_t_min, current_t_max = self.vbox.viewRange()[0]
            if current_t_max != t_max or current_t_min != t_min:
                self.vbox.setXRange(t_min, t_max, padding=0)
                self.x_axis.setTicks(
                    [[(i * v_scale, f"{int(i * v_scale)}") for i in range(-10, 11)], []]
                )
                self.x_axis.setLabel(f"{self.app.model.visual_time_scale.time_unit.to_str()}")
                self.trigger_pos_marker.setPos(
                    self.plot.getViewBox().x() + self.y_axis.getViewBox().x() +
                    self.corrected_trigger_position[0] * self.x_axis.width(),
                    0
                )

        plotted_at = time.time()
        f = int(1 / (plotted_at - self.last_plotted_at))
        self.app.set_live_info_label(f"fps: {f}")
        self.last_plotted_at = plotted_at

    @cache
    def get_ts(
            self, len_vs: int, t_pos: float, board_time_scale: Duration, visual_time_scale: Duration
    ) -> list[float]:
        trigger_index = int(t_pos * len_vs)
        board_time_scale_value = board_time_scale.to_float(visual_time_scale.time_unit)
        return [10 * board_time_scale_value * (i - trigger_index) / len_vs for i in range(len_vs)]

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if hasattr(self, "trigger_pos_marker"):
            self.trigger_pos_marker.setPos(
                self.plot.getViewBox().x() + self.y_axis.getViewBox().x() +
                self.corrected_trigger_position[0] * self.x_axis.width(),
                0
            )
