import time
from typing import Optional

from PySide6.QtCore import QPointF, Signal, QRectF
from PySide6.QtGui import QPen, Qt, QFontDatabase, QColor, QBrush
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from hspro_api import Waveform
from pyqtgraph import AxisItem, GraphicsLayoutWidget, InfiniteLine, PlotDataItem, TextItem, mkPen, mkBrush
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.graphicsItems.PlotItem import PlotItem
from pyqtgraph.graphicsItems.ViewBox import ViewBox

from hspro.gui.app import App, WorkerMessage
from hspro.gui.gui_ext import fn
from hspro.gui.gui_ext.arrows import XArrowDown, XArrowLeft, XArrowRight
from hspro.gui.waveform_ext import WaveformExt


class TriggerPositionLine(InfiniteLine):
    def __init__(self, pen: QPen):
        super().__init__(pos=0, movable=True, angle=90, pen=pen)
        self.setZValue(10)


class PlotsPanel(GraphicsLayoutWidget):
    update_y_ticks_color = Signal(int)
    update_zero_line_position = Signal(float)
    update_zoom_rect = Signal(QRectF)

    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app
        self.pens = [fn.mkPen(ch.color) for ch in self.app.model.channel]
        self.brushes = [QBrush(ch.color) for ch in self.app.model.channel]
        self.do_show_trig_level_line = self.app.app_persistence.config.get_by_xpath("/show_trigger_level_line", bool)
        self.do_show_trig_pos_line = self.app.app_persistence.config.get_by_xpath("/show_trigger_position_line", bool)
        self.corrected_trigger_position = [0.0]
        self.corrected_trigger_level = [0.0]
        self.first_time_pained = True
        self.show_y_axis_labels_p = [app.app_persistence.config.get_by_xpath("/show_y_axis_labels")]
        self.selected_channel = [0]
        self.grid_opacity = float(self.app.app_persistence.state.get_value("grid_opacity", "0.5"))
        self.grid_visible = self.app.app_persistence.config.get_by_xpath("/show_grid")

        self.trigger_lines_color_map = "Matching Trigger Channel"

        self.plot: PlotItem = self.addPlot(0, 0)
        self.plot.autoBtn.setEnabled(False)
        self.plot.autoBtn.setVisible(False)
        self.plot.autoBtn.show = lambda: None
        self.plot.setMenuEnabled(False)

        self.plot.showGrid(self.grid_visible, self.grid_visible, self.grid_opacity)

        def show_grid(show: bool):
            self.plot.showGrid(show, show, self.grid_opacity)
            self.app.app_persistence.config.set_by_xpath("/show_grid", show)
            self.grid_visible = show

        self.app.set_show_grid_state = show_grid

        def update_grid_opacity(opacity: float):
            self.grid_opacity = opacity / 255
            self.app.app_persistence.state.set_value("grid_opacity", f"{self.grid_opacity}")
            if self.grid_visible:
                self.plot.showGrid(True, True, self.grid_opacity)

        self.app.set_grid_opacity = update_grid_opacity

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

        self.app.remove_all_y_axis_ticks_labels = lambda: self.y_axis.setTicks(
            [
                [(-5, ""), (-4, ""), (-3, ""), (-2, ""), (-1, ""), (0, ""), (1, ""), (2, ""), (3, ""), (4, ""),
                 (5, "")],
                []
            ]
        )

        self.y_axis.setTextPen()

        def update_y_axis_ticks(ch: int | None) -> None:
            if not self.show_y_axis_labels_p[0]:
                self.y_axis.setTicks(
                    [
                        [(-5, ""), (-4, ""), (-3, ""), (-2, ""), (-1, ""), (0, ""), (1, ""), (2, ""), (3, ""), (4, ""),
                         (5, "")],
                        []
                    ]
                )
                if ch is not None:
                    self.selected_channel.clear()
                    self.selected_channel.append(ch)

                ch = self.selected_channel[0]
                dV = self.app.model.channel[ch].dV
                offset_V = self.app.model.channel[ch].offset_V
                self.update_y_ticks_color.emit(ch)
                self.update_zero_line_position.emit(offset_V / dV)
            else:
                if ch is not None:
                    self.selected_channel.clear()
                    self.selected_channel.append(ch)

                ch = self.selected_channel[0]
                dV = self.app.model.channel[ch].dV
                offset_V = self.app.model.channel[ch].offset_V
                ticks = []
                for i in range(-5, 6):
                    vi = dV * i - offset_V
                    ticks.append((i, f"{vi:7.2f} V"))
                self.y_axis.setTicks([ticks, []])
                self.update_y_ticks_color.emit(ch)
                self.update_zero_line_position.emit(offset_V / dV)

        self.app.update_y_axis_ticks = update_y_axis_ticks

        self.update_y_ticks_color.connect(lambda channel: self.y_axis.setTextPen(self.pens[channel]))
        self.update_y_ticks_color.connect(lambda channel: self.zero_line.setPen(self.pens[channel]))
        self.update_y_ticks_color.connect(lambda channel: self.zero_marker.setBrush(self.brushes[channel]))

        def show_y_axis_labels(show: bool):
            self.show_y_axis_labels_p.clear()
            self.show_y_axis_labels_p.append(show)
            self.app.update_y_axis_ticks(None)
            app.app_persistence.config.set_by_xpath("/show_y_axis_labels", show)

        self.app.set_show_y_axis_labels = show_y_axis_labels

        self.vbox: ViewBox = self.x_axis.linkedView()
        self.vbox.setMouseEnabled(False, False)
        self.vbox.setRange(xRange=(0, 10), yRange=(-5, 5), padding=0)

        self.zoom_crds = [[0, 0], [10, 10]]
        self.zoomBox = QtWidgets.QGraphicsRectItem(
            self.zoom_crds[0][0], self.zoom_crds[0][1],
            self.zoom_crds[1][0], self.zoom_crds[1][1]
        )
        self.zoomBox.setPen(mkPen((100, 100, 100), width=1))
        # self.zoomBox.setPen(mkPen((255, 255, 100), width=1))
        self.zoomBox.setBrush(mkBrush(255, 255, 0, 100))
        self.zoomBox.setZValue(1e9)
        self.zoomBox.hide()
        self.app.hide_zoom_box = self.zoomBox.hide
        self.vbox.scene().addItem(self.zoomBox)

        def upd_zoom_box(rect: QRectF):
            rect = self.vbox.mapViewToScene(rect)
            self.zoomBox.setRect(QRectF(rect.toList()[0], rect.toList()[2]))

        self.update_zoom_rect.connect(upd_zoom_box)

        self.app.update_zoom_rect_on_main_plot = self.update_zoom_rect_on_main_plot

        def mouse_press_event(e: QGraphicsSceneMouseEvent):
            if app.current_active_tool == "Zoom":
                pos = e.scenePos()
                self.zoom_crds[0][0] = pos.x()
                self.zoom_crds[0][1] = pos.y()
                self.zoomBox.setRect(self.zoom_crds[0][0], self.zoom_crds[0][1], 1, 1)
                self.zoomBox.show()

        def mouse_release_event(e: QGraphicsSceneMouseEvent):
            if app.current_active_tool == "Zoom":
                rect = self.zoomBox.rect()
                self.app.open_or_update_zoom_dialog(
                    QRectF(
                        self.vbox.mapSceneToView(QPointF(rect.left(), rect.top())),
                        self.vbox.mapSceneToView(QPointF(rect.right(), rect.bottom()))
                    )
                )

        def mouse_move_event(e):
            if app.current_active_tool == "Zoom":
                pos = e.scenePos()
                self.zoom_crds[1][0] = pos.x()
                self.zoom_crds[1][1] = pos.y()
                x0 = self.zoom_crds[0][0] if self.zoom_crds[1][0] >= self.zoom_crds[0][0] else self.zoom_crds[1][0]
                dx = abs(self.zoom_crds[1][0] - self.zoom_crds[0][0])
                y0 = self.zoom_crds[0][1] if self.zoom_crds[1][1] >= self.zoom_crds[0][1] else self.zoom_crds[1][1]
                dy = abs(self.zoom_crds[1][1] - self.zoom_crds[0][1])
                self.zoomBox.setRect(x0, y0, dx, dy)

        self.vbox.mousePressEvent = mouse_press_event
        self.vbox.mouseReleaseEvent = mouse_release_event
        self.vbox.mouseMoveEvent = mouse_move_event

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
        self.app.set_show_zero_line = self.set_show_zero_line

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

        self.traces = [PlotDataItem(), PlotDataItem()]
        self.held_traces = [PlotDataItem(), PlotDataItem()]

        # self.zero_markers = [ArrowItem(pos=(1, 1), angle=0, headLen=15, headWidth=10)]

        for i, trace in enumerate(self.traces):
            trace.setPen(self.pens[i])
            trace.setVisible(self.app.model.channel[i].active)
            self.plot.addItem(trace)

        for held_trace in self.held_traces:
            held_trace.setPen(fn.mkPen("orange"))
            held_trace.setVisible(False)
            self.plot.addItem(held_trace)

        # for i, zm in enumerate(self.zero_markers):
        #     zm.setPen(self.pens[i])
        #     zm.setBrush(self.brushes[i])
        #     zm.setVisible(self.app.model.channel[i].active)
        #     self.plot.addItem(zm)

        self.zero_line_pen = QPen()
        self.zero_line_pen.setCosmetic(True)
        self.zero_line_pen.setColor(QColor(0xFF, 0, 0xff, 100))
        self.zero_line_pen.setWidth(3)

        self.zero_line = InfiniteLine(
            pos=0, movable=False, angle=0  # , pen=self.zero_line_pen
        )
        self.zero_line.setVisible(self.app.app_persistence.config.get_by_xpath("/show_zero_line", bool))
        self.update_zero_line_position.connect(self.zero_line.setY)

        self.plot.addItem(self.zero_line)

        self.zero_marker = XArrowRight(pxMode=True)
        self.zero_marker.setBrush(self.trigger_marker_brush)
        self.zero_marker.setX(30)
        self.scene().addItem(self.zero_marker)

        self.update_zero_line_position.connect(
            lambda y: self.zero_marker.setY(
                self.plot.getViewBox().y() + self.y_axis.getViewBox().y() - (y - 5) / 10 * self.y_axis.height()
            )
        )

        self.trigger_level_marker = XArrowLeft(pxMode=True)
        self.trigger_level_marker.setPen(self.trigger_lines_pen)
        self.trigger_level_marker.setBrush(self.trigger_marker_brush)
        self.scene().addItem(self.trigger_level_marker)

        self.trigger_pos_marker = XArrowDown(pxMode=True)
        self.trigger_pos_marker.setPen(self.trigger_lines_pen)
        self.trigger_pos_marker.setBrush(self.trigger_marker_brush)
        self.scene().addItem(self.trigger_pos_marker)

        def correct_trigger_level_line(pos):
            self.trigger_level_line.setPos(5 * pos)
            self.corrected_trigger_level.clear()
            self.corrected_trigger_level.append(pos)
            self.trigger_level_marker.setY(
                self.plot.getViewBox().y() + self.y_axis.getViewBox().y() + (1 - (pos + 1) / 2) * self.y_axis.height()
            )

        self.app.correct_trigger_level = correct_trigger_level_line

        self.app.set_channel_active_state = self.channel_active_state_changed
        self.app.set_channel_color = self.channel_color_changed

        self.value_label = TextItem("", color=(0, 0, 0), border=(0, 0, 0), fill=(255, 255, 255))
        self.value_label.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.value_label.setPos(15, 5)
        self.value_label.setZValue(5)
        self.value_label.setVisible(False)
        self.scene().addItem(self.value_label)

        self.setMouseTracking(True)
        self.plot.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.plot.setCursor(Qt.CursorShape.CrossCursor)
        self.plot.getAxis('bottom').setZValue(-1)

        self.update_trigger_lines_color(app.model.trigger.on_channel)
        self.update_trigger_lines_color(app.model.trigger.on_channel)

        self.app.plot_waveforms = self.plot_waveforms
        self.last_plotted_at = time.time()
        self.held_waveforms = []

        self.app.select_channel_in_plot = self.select_channel
        self.app.replot_waveforms = self.replot_last_plotted_waveforms
        self.app.plot_held_waveforms = self.plot_held_waveforms
        self.app.show_held_waveforms = self.show_held_waveforms

    def update_zoom_box(self):
        if self.app.current_active_tool == "Zoom":
            rect = self.zoomBox.rect()
            r2 = QRectF(self.vbox.mapSceneToView(QPointF(rect.left(), rect.top())),
                        self.vbox.mapSceneToView(QPointF(rect.right(), rect.bottom())))
            self.app.open_or_update_zoom_dialog(r2)

    def update_zoom_rect_on_main_plot(self, rect: QRectF):
        self.update_zoom_rect.emit(rect)

    def on_mouse_moved(self, evt: QPointF):
        pos = evt
        if self.plot.sceneBoundingRect().contains(pos) and self.app.selected_channel is not None:
            if not self.value_label.isVisible():
                self.value_label.setVisible(True)
            mousePoint = self.plot.vb.mapSceneToView(pos)
            channel = self.app.model.channel[self.app.selected_channel]
            v = channel.dV * mousePoint.y() + channel.offset_V
            label = f"{v:.3f} [V] @ {mousePoint.x():.2f} [{self.app.model.visual_time_scale.time_unit.to_str()}]"
            self.value_label.setText(f"{label:<28}")
        elif self.value_label.isVisible():
            self.value_label.setVisible(False)

    def leaveEvent(self, ev):
        super().leaveEvent(ev)
        self.value_label.setVisible(False)

    def select_channel(self, channel: int):
        self.zero_line.setPen(self.pens[channel])
        self.zero_marker.setBrush(self.brushes[channel])

    def set_plot_color_scheme(self, plot_color_scheme: str):
        match plot_color_scheme:
            case "light":
                self.setBackground("white")
                self.trigger_level_line.setPen(self.trigger_lines_pen)
                self.trigger_pos_line.setPen(self.trigger_lines_pen)
                # self.zero_h_line.setPen(self.black_pen)
                self.app.app_persistence.config.set_by_xpath("/plot_color_scheme", "light")
            case "dark":
                self.setBackground("black")
                self.trigger_level_line.setPen(self.trigger_lines_pen)
                self.trigger_pos_line.setPen(self.trigger_lines_pen)
                # self.zero_h_line.setPen(self.blue_pen)
                self.app.app_persistence.config.set_by_xpath("/plot_color_scheme", "dark")

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

    def channel_active_state_changed(self, channel: int, active: bool):
        self.traces[channel].setVisible(active)

    def channel_color_changed(self, channel: int, color: str, select_channel: bool):
        self.pens[channel].setColor(color)
        self.brushes[channel].setColor(color)
        self.traces[channel].setPen(self.pens[channel])
        if select_channel:
            self.app.worker.messages.put(WorkerMessage.SelectChannel(channel))
        self.y_axis.setTextPen(self.pens[channel])
        self.zero_line.setPen(self.pens[channel])
        self.zero_marker.setBrush(self.brushes[channel])

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

    def set_show_zero_line(self, show_zero_line: bool):
        self.app.app_persistence.config.set_by_xpath("/show_zero_line", show_zero_line)
        self.zero_line.setVisible(show_zero_line)

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

    def replot_last_plotted_waveforms(self):
        if self.app.last_plotted_waveforms != []:
            for i, w in enumerate(self.app.last_plotted_waveforms):
                if w is not None:
                    self.traces[i].setData(w.get_t_vec(self.app.model.visual_time_scale.time_unit), w.vs)
        if self.held_waveforms != []:
            for i, w in enumerate(self.held_waveforms):
                if w is not None:
                    self.held_traces[i].setData(
                        w.waveform.get_t_vec(self.app.model.visual_time_scale.time_unit), w.waveform.vs
                    )

    def plot_waveforms(self, ws: tuple[Optional[Waveform], Optional[Waveform]], save_waveforms: bool = True):
        for i, w in enumerate(ws):
            if w is not None:
                w.apply_trigger_correction(self.corrected_trigger_position[0])
                self.traces[i].setData(w.get_t_vec(self.app.model.visual_time_scale.time_unit), w.vs)

        plotted_at = time.time()
        f = int(1 / (plotted_at - self.last_plotted_at))
        self.app.set_live_info_label(f"fps: {f}")
        self.last_plotted_at = plotted_at

        if save_waveforms:
            self.app.record_last_plotted_waveforms(list(ws))

    def plot_held_waveforms(self, ws: list[Optional[WaveformExt]]):
        self.held_waveforms = ws
        for i, w in enumerate(ws):
            if w is None:
                self.held_traces[i].setData()
                self.held_traces[i].setVisible(False)
            else:
                self.held_traces[i].setData(
                    w.waveform.get_t_vec(self.app.model.visual_time_scale.time_unit), w.waveform.vs
                )
                self.held_traces[i].setPen(fn.mkPen(w.color))
                self.held_traces[i].setVisible(True)

    def show_held_waveforms(self, show: bool):
        for held_trace in self.held_traces:
            if held_trace._dataset is not None:
                held_trace.setVisible(show)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if hasattr(self, "trigger_pos_marker"):
            self.trigger_pos_marker.setPos(
                self.plot.getViewBox().x() + self.y_axis.getViewBox().x() +
                self.corrected_trigger_position[0] * self.x_axis.width(),
                0
            )
        if hasattr(self, "app"):
            self.app.update_y_axis_ticks(None)

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if self.first_time_pained:
            self.trigger_pos_marker.setPos(
                self.plot.getViewBox().x() + self.y_axis.getViewBox().x() +
                self.corrected_trigger_position[0] * self.x_axis.width(),
                0
            )
            self.trigger_level_marker.setPos(
                self.plot.getViewBox().x() + self.y_axis.getViewBox().x() + self.x_axis.width() + 5,
                self.plot.getViewBox().y() + self.y_axis.getViewBox().y() +
                (1 - (self.corrected_trigger_level[0] + 1) / 2) * self.y_axis.height()
            )

            self.zero_marker.setX(self.plot.getViewBox().x() + 8)
