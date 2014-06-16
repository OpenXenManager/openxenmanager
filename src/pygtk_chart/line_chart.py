#!/usr/bin/env python
#
#       lineplot.py
#
#       Copyright 2008 Sven Festersen <sven@sven-festersen.de>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
"""
Contains the LineChart widget.

Author: Sven Festersen (sven@sven-festersen.de)
"""
__docformat__ = "epytext"
import gobject
import cairo
import gtk
import math
import os

import pygtk_chart
from pygtk_chart.basics import *
from pygtk_chart.chart_object import ChartObject
from pygtk_chart import chart
from pygtk_chart import label
from pygtk_chart import COLORS, COLOR_AUTO

RANGE_AUTO = 0
GRAPH_PADDING = 1 / 15.0 #a relative padding
GRAPH_POINTS = 1
GRAPH_LINES = 2
GRAPH_BOTH = 3
COLOR_AUTO = 4
POSITION_AUTO = 5
POSITION_LEFT = 6
POSITION_RIGHT = 7
POSITION_BOTTOM = 6
POSITION_TOP = 7
POSITION_TOP_RIGHT = 8
POSITION_BOTTOM_RIGHT = 9
POSITION_BOTTOM_LEFT = 10
POSITION_TOP_LEFT = 11

        
def draw_point(context, x, y, radius, style):
    a = radius / 1.414 #1.414=sqrt(2)
    if style == pygtk_chart.POINT_STYLE_CIRCLE:
        context.arc(x, y, radius, 0, 2 * math.pi)
        context.fill()
    elif style == pygtk_chart.POINT_STYLE_SQUARE:
        context.rectangle(x - a, y- a, 2 * a, 2 * a)
        context.fill()
    elif style == pygtk_chart.POINT_STYLE_CROSS:
        context.move_to(x, y - a)
        context.rel_line_to(0, 2 * a)
        context.stroke()
        context.move_to(x - a, y)
        context.rel_line_to(2 * a, 0)
        context.stroke()
    elif style == pygtk_chart.POINT_STYLE_TRIANGLE_UP:
        a = 1.732 * radius #1.732=sqrt(3)
        b = a / (2 * 1.732)
        context.move_to(x - a / 2, y + b)
        context.rel_line_to(a, 0)
        context.rel_line_to(-a / 2, -(radius + b))
        context.rel_line_to(-a / 2, radius + b)
        context.close_path()
        context.fill()
    elif style == pygtk_chart.POINT_STYLE_TRIANGLE_DOWN:
        a = 1.732 * radius #1.732=sqrt(3)
        b = a / (2 * 1.732)
        context.move_to(x - a / 2, y - b)
        context.rel_line_to(a, 0)
        context.rel_line_to(-a / 2, radius + b)
        context.rel_line_to(-a / 2, -(radius + b))
        context.close_path()
        context.fill()
    elif style == pygtk_chart.POINT_STYLE_DIAMOND:
        context.move_to(x, y - a)
        context.rel_line_to(a, a)
        context.rel_line_to(-a, a)
        context.rel_line_to(-a, -a)
        context.rel_line_to(a, -a)
        context.fill()
        
def draw_point_pixbuf(context, x, y, pixbuf):
    w = pixbuf.get_width()
    h = pixbuf.get_height()
    ax = x - w / 2
    ay = y - h / 2
    context.set_source_pixbuf(pixbuf, ax, ay)
    context.rectangle(ax, ay, w, h)
    context.fill()
    
def draw_errors(context, rect, range_calc, x, y, errors, draw_x, draw_y, xaxis, yaxis, size):
    if (x, y) in errors:
        xerror, yerror = errors[(x, y)]
        if draw_x and xerror > 0:
            #rect, x, y, xaxis, yaxis
            left = range_calc.get_absolute_point(rect, x - xerror, y, xaxis, yaxis)
            right = range_calc.get_absolute_point(rect, x + xerror, y, xaxis, yaxis)
            context.move_to(left[0], left[1])
            context.line_to(right[0], right[1])
            context.stroke()
            context.move_to(left[0], left[1] - size)
            context.rel_line_to(0, 2 * size)
            context.stroke()
            context.move_to(right[0], right[1] - size)
            context.rel_line_to(0, 2 * size)
            context.stroke()
        if draw_y and yerror > 0:
            top = range_calc.get_absolute_point(rect, x, y - yerror, xaxis, yaxis)
            bottom = range_calc.get_absolute_point(rect, x, y + yerror, xaxis, yaxis)
            context.move_to(top[0], top[1])
            context.line_to(bottom[0], bottom[1])
            context.stroke()
            context.move_to(top[0] - size, top[1])
            context.rel_line_to(2 * size, 0)
            context.stroke()
            context.move_to(bottom[0] - size, bottom[1])
            context.rel_line_to(2 * size, 0)
            context.stroke()
    
def separate_data_and_errors(old_data):
    data = []
    errors = {}
    for d in old_data:
        if len(d) == 2:
            data.append(d)
        elif len(d) == 4:
            data.append((d[0], d[1]))
            errors[(d[0], d[1])] = (d[2], d[3])
    return data, errors


class RangeCalculator:
    """
    This helper class calculates ranges. It is used by the LineChart
    widget internally, there is no need to create an instance yourself.
    """
    def __init__(self):
        self._data_xrange = None
        self._data_yrange = None
        self._xrange = RANGE_AUTO
        self._yrange = RANGE_AUTO
        self._cached_xtics = []
        self._cached_ytics = []

    def add_graph(self, graph):
        if self._data_xrange == None:
            self._data_yrange = graph.get_y_range()
            self._data_xrange = graph.get_x_range()
        else:
            yrange = graph.get_y_range()
            xrange = graph.get_x_range()

            if xrange and yrange:
                xmin = min(xrange[0], self._data_xrange[0])
                xmax = max(xrange[1], self._data_xrange[1])
                ymin = min(yrange[0], self._data_yrange[0])
                ymax = max(yrange[1], self._data_yrange[1])

                self._data_xrange = (xmin, xmax)
                self._data_yrange = (ymin, ymax)

    def get_ranges(self, xaxis, yaxis):
        xrange = self._xrange
        if xrange == RANGE_AUTO:
            xrange = self._data_xrange
            if xrange[0] == xrange[1]:
                xrange = (xrange[0], xrange[0] + 0.1)

        yrange = self._yrange
        if yrange == RANGE_AUTO:
            yrange = self._data_yrange
            if yrange[0] == yrange[1]:
                yrange = (yrange[0], yrange[0] + 0.1)
                
                
        if xaxis.get_logarithmic():
            xrange = math.log10(xrange[0]), math.log10(xrange[1])
        if yaxis.get_logarithmic():
            yrange = math.log10(yrange[0]), math.log10(yrange[1])

        return (xrange, yrange)

    def set_xrange(self, xrange):
        self._xrange = xrange

    def set_yrange(self, yrange):
        self._yrange = yrange

    def get_absolute_zero(self, rect, xaxis, yaxis):
        xrange, yrange = self.get_ranges(xaxis, yaxis)

        xfactor = float(rect.width * (1 - 2 * GRAPH_PADDING)) / (xrange[1] - xrange[0])
        yfactor = float(rect.height * (1 - 2 * GRAPH_PADDING)) / (yrange[1] - yrange[0])
        zx = (rect.width * GRAPH_PADDING) - xrange[0] * xfactor
        zy = rect.height - ((rect.height * GRAPH_PADDING) - yrange[0] * yfactor)

        return (zx,zy)

    def get_absolute_point(self, rect, x, y, xaxis, yaxis):
        (zx, zy) = self.get_absolute_zero(rect, xaxis, yaxis)
        xrange, yrange = self.get_ranges(xaxis, yaxis)

        xfactor = float(rect.width * (1 - 2 * GRAPH_PADDING)) / (xrange[1] - xrange[0])
        yfactor = float(rect.height * (1 - 2 * GRAPH_PADDING)) / (yrange[1] - yrange[0])

        ax = zx + x * xfactor
        ay = zy - y * yfactor
        return (ax, ay)

    def prepare_tics(self, rect, xaxis, yaxis):
        self._cached_xtics = self._get_xtics(rect, xaxis, yaxis)
        self._cached_ytics = self._get_ytics(rect, xaxis, yaxis)

    def get_xtics(self, rect):
        return self._cached_xtics

    def get_ytics(self, rect):
        return self._cached_ytics

    def _get_xtics(self, rect, xaxis, yaxis):
        tics = []
        (zx, zy) = self.get_absolute_zero(rect, xaxis, yaxis)
        (xrange, yrange) = self.get_ranges(xaxis, yaxis)
        delta = xrange[1] - xrange[0]
        exp = int(math.log10(delta)) - 1

        first_n = int(xrange[0] / (10 ** exp))
        last_n = int(xrange[1] / (10 ** exp))
        n = last_n - first_n
        N = rect.width / 50.0
        divide_by = int(n / N)
        if divide_by == 0: divide_by = 1

        left = rect.width * GRAPH_PADDING
        right = rect.width * (1 - GRAPH_PADDING)

        for i in range(first_n, last_n + 1):
            num = i * 10 ** exp
            (x, y) = self.get_absolute_point(rect, num, 0, xaxis, yaxis)
            if i % divide_by == 0 and is_in_range(x, (left, right)):
                tics.append(((x, y), num))

        return tics

    def _get_ytics(self, rect, xaxis, yaxis):
        tics = []
        (zx, zy) = self.get_absolute_zero(rect, xaxis, yaxis)
        (xrange, yrange) = self.get_ranges(xaxis, yaxis)
        delta = yrange[1] - yrange[0]
        exp = int(math.log10(delta)) - 1

        first_n = int(yrange[0] / (10 ** exp))
        last_n = int(yrange[1] / (10 ** exp))
        n = last_n - first_n
        N = rect.height / 50.0
        divide_by = int(n / N)
        if divide_by == 0: divide_by = 1

        top = rect.height * GRAPH_PADDING
        bottom = rect.height * (1 - GRAPH_PADDING)

        for i in range(first_n, last_n + 1):
            num = i * 10 ** exp
            (x, y) = self.get_absolute_point(rect, 0, num, xaxis, yaxis)
            if i % divide_by == 0 and is_in_range(y, (top, bottom)):
                tics.append(((x, y), num))

        return tics


class LineChart(chart.Chart):
    """
    A widget that shows a line chart. The following attributes can be
    accessed:
     - LineChart.background (inherited from chart.Chart)
     - LineChart.title (inherited from chart.Chart)
     - LineChart.graphs (a dict that holds the graphs identified by
       their name)
     - LineChart.grid
     - LineChart.xaxis
     - LineChart.yaxis
     
    Properties
    ==========
    LineChart inherits properties from chart.Chart.
    
    Signals
    =======
    The LineChart class inherits signals from chart.Chart.
    Additional chart:
     - datapoint-clicked (emitted if a datapoint is clicked)
     - datapoint-hovered (emitted if a datapoint is hovered with the
       mouse pointer)
    Callback signature for both signals:
    def callback(linechart, graph, (x, y))
    """
    
    __gsignals__ = {"datapoint-clicked": (gobject.SIGNAL_RUN_LAST,
                                            gobject.TYPE_NONE,
                                            (gobject.TYPE_PYOBJECT,
                                            gobject.TYPE_PYOBJECT)),
                    "datapoint-hovered": (gobject.SIGNAL_RUN_LAST,
                                            gobject.TYPE_NONE,
                                            (gobject.TYPE_PYOBJECT,
                                            gobject.TYPE_PYOBJECT))}
    
    def __init__(self):
        chart.Chart.__init__(self)
        self.graphs = {}
        self._range_calc = RangeCalculator()
        self.xaxis = XAxis(self._range_calc)
        self.yaxis = YAxis(self._range_calc)
        self.grid = Grid(self._range_calc)
        self.legend = Legend()
        
        self._highlighted_points = []

        self.xaxis.connect("appearance_changed", self._cb_appearance_changed)
        self.yaxis.connect("appearance_changed", self._cb_appearance_changed)
        self.grid.connect("appearance_changed", self._cb_appearance_changed)
        self.legend.connect("appearance_changed", self._cb_appearance_changed)
        
    def __iter__(self):
        for name, graph in self.graphs.iteritems():
            yield graph
            
    def _cb_button_pressed(self, widget, event):
        points = chart.get_sensitive_areas(event.x, event.y)
        for x, y, graph in points:
            self.emit("datapoint-clicked", graph, (x, y))
    
    def _cb_motion_notify(self, widget, event):
        self._highlighted_points = chart.get_sensitive_areas(event.x, event.y)
        for x, y, graph in self._highlighted_points:
            self.emit("datapoint-hovered", graph, (x, y))
        self.queue_draw()

    def _do_draw_graphs(self, context, rect):
        """
        Draw all the graphs.

        @type context: cairo.Context
        @param context: The context to draw on.
        @type rect: gtk.gdk.Rectangle
        @param rect: A rectangle representing the charts area.
        """
        for (name, graph) in self.graphs.iteritems():
            graph.draw(context, rect, self.xaxis, self.yaxis, self._highlighted_points)
        self._highlighted_points = []

    def _do_draw_axes(self, context, rect):
        """
        Draw x and y axis.

        @type context: cairo.Context
        @param context: The context to draw on.
        @type rect: gtk.gdk.Rectangle
        @param rect: A rectangle representing the charts area.
        """
        self.xaxis.draw(context, rect, self.yaxis)
        self.yaxis.draw(context, rect, self.xaxis)

    def draw(self, context):
        """
        Draw the widget. This method is called automatically. Don't call it
        yourself. If you want to force a redrawing of the widget, call
        the queue_draw() method.

        @type context: cairo.Context
        @param context: The context to draw on.
        """
        label.begin_drawing()
        chart.init_sensitive_areas()
        rect = self.get_allocation()
        self._range_calc.prepare_tics(rect, self.xaxis, self.yaxis)
        #initial context settings: line width & font
        context.set_line_width(1)
        font = gtk.Label().style.font_desc.get_family()
        context.select_font_face(font,cairo.FONT_SLANT_NORMAL, \
                                    cairo.FONT_WEIGHT_NORMAL)

        self.draw_basics(context, rect)
        data_available = False
        for (name, graph) in self.graphs.iteritems():
            if graph.has_something_to_draw():
                data_available = True
                break

        if self.graphs and data_available:
            self.grid.draw(context, rect, self.xaxis, self.yaxis)
            self._do_draw_axes(context, rect)
            self._do_draw_graphs(context, rect)
        label.finish_drawing()
        
        self.legend.draw(context, rect, self.graphs)

    def add_graph(self, graph):
        """
        Add a graph object to the plot.

        @type graph: line_chart.Graph
        @param graph: The graph to add.
        """
        if graph.get_color() == COLOR_AUTO:
            graph.set_color(COLORS[len(self.graphs) % len(COLORS)])
        graph.set_range_calc(self._range_calc)
        self.graphs[graph.get_name()] = graph
        self._range_calc.add_graph(graph)

        graph.connect("appearance-changed", self._cb_appearance_changed)

    def remove_graph(self, name):
        """
        Remove a graph from the plot.

        @type name: string
        @param name: The name of the graph to remove.
        """
        del self.graphs[name]
        self.queue_draw()

    def set_xrange(self, xrange):
        """
        Set the visible xrange. xrange has to be a pair: (xmin, xmax) or
        RANGE_AUTO. If you set it to RANGE_AUTO, the visible range will
        be calculated.

        @type xrange: pair of numbers
        @param xrange: The new xrange.
        """
        self._range_calc.set_xrange(xrange)
        self.queue_draw()
        
    def get_xrange(self):
        return self._range_calc.get_ranges(self.xaxis, self.yaxis)[0]

    def set_yrange(self, yrange):
        """
        Set the visible yrange. yrange has to be a pair: (ymin, ymax) or
        RANGE_AUTO. If you set it to RANGE_AUTO, the visible range will
        be calculated.

        @type yrange: pair of numbers
        @param yrange: The new yrange.
        """
        self._range_calc.set_yrange(yrange)
        self.queue_draw()
        
    def get_yrange(self):
        return self._range_calc.get_ranges(self.xaxis, self.yaxis)[1]


class Axis(ChartObject):
    """
    This class represents an axis on the line chart.
    
    Properties
    ==========
    The Axis class inherits properties from chart_object.ChartObject.
    Additional properties:
     - label (a label for the axis, type: string)
     - show-label (sets whether the axis' label should be shown, 
       type: boolean)
     - position (position of the axis, type: an axis position constant)
     - show-tics (sets whether tics should be shown at the axis,
       type: boolean)
     - show-tic-lables (sets whether labels should be shown at the tics,
       type: boolean)
     - tic-format-function (a function that is used to format the tic
       labels, default: str)
     - logarithmic (sets whether the axis should use a logarithmic
       scale, type: boolean).
       
    Signals
    =======
    The Axis class inherits signals from chart_object.ChartObject.
    """

    __gproperties__ = {"label": (gobject.TYPE_STRING, "axis label",
                                    "The label of the axis.", "",
                                    gobject.PARAM_READWRITE),
                        "show-label": (gobject.TYPE_BOOLEAN, "show label",
                                    "Set whether to show the axis label.",
                                    True, gobject.PARAM_READWRITE),
                        "position": (gobject.TYPE_INT, "axis position",
                                    "Position of the axis.", 5, 7, 5,
                                    gobject.PARAM_READWRITE),
                        "show-tics": (gobject.TYPE_BOOLEAN, "show tics",
                                    "Set whether to draw tics.", True,
                                    gobject.PARAM_READWRITE),
                        "show-tic-labels": (gobject.TYPE_BOOLEAN,
                                            "show tic labels",
                                            "Set whether to draw tic labels",
                                            True,
                                            gobject.PARAM_READWRITE),
                        "tic-format-function": (gobject.TYPE_PYOBJECT,
                                            "tic format function",
                                            "This function is used to label the tics.",
                                            gobject.PARAM_READWRITE),
                        "logarithmic": (gobject.TYPE_BOOLEAN,
                                        "logarithmic scale",
                                        "Set whether to use logarithmic scale.",
                                        False, gobject.PARAM_READWRITE)}

    def __init__(self, range_calc, label):
        ChartObject.__init__(self)
        self.set_property("antialias", False)

        self._label = label
        self._show_label = True
        self._position = POSITION_AUTO
        self._show_tics = True
        self._show_tic_labels = True
        self._tic_format_function = str
        self._logarithmic = False

        self._range_calc = range_calc

    def do_get_property(self, property):
        if property.name == "visible":
            return self._show
        elif property.name == "antialias":
            return self._antialias
        elif property.name == "label":
            return self._label
        elif property.name == "show-label":
            return self._show_label
        elif property.name == "position":
            return self._position
        elif property.name == "show-tics":
            return self._show_tics
        elif property.name == "show-tic-labels":
            return self._show_tic_labels
        elif property.name == "tic-format-function":
            return self._tic_format_function
        elif property.name == "logarithmic":
            return self._logarithmic
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def do_set_property(self, property, value):
        if property.name == "visible":
            self._show = value
        elif property.name == "antialias":
            self._antialias = value
        elif property.name == "label":
            self._label = value
        elif property.name == "show-label":
            self._show_label = value
        elif property.name == "position":
            self._position = value
        elif property.name == "show-tics":
            self._show_tics = value
        elif property.name == "show-tic-labels":
            self._show_tic_labels = value
        elif property.name == "tic-format-function":
            self._tic_format_function = value
        elif property.name == "logarithmic":
            self._logarithmic = value
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def set_label(self, label):
        """
        Set the label of the axis.

        @param label: new label
        @type label: string.
        """
        self.set_property("label", label)
        self.emit("appearance_changed")

    def get_label(self):
        """
        Returns the current label of the axis.

        @return: string.
        """
        return self.get_property("label")

    def set_show_label(self, show):
        """
        Set whether to show the axis' label.

        @type show: boolean.
        """
        self.set_property("show-label", show)
        self.emit("appearance_changed")

    def get_show_label(self):
        """
        Returns True if the axis' label is shown.

        @return: boolean.
        """
        return self.get_property("show-label")

    def set_position(self, pos):
        """
        Set the position of the axis. pos hast to be one these
        constants: POSITION_AUTO, POSITION_BOTTOM, POSITION_LEFT,
        POSITION_RIGHT, POSITION_TOP.
        """
        self.set_property("position", pos)
        self.emit("appearance_changed")

    def get_position(self):
        """
        Returns the position of the axis. (see set_position for
        details).
        """
        return self.get_property("position")

    def set_show_tics(self, show):
        """
        Set whether to draw tics at the axis.

        @type show: boolean.
        """
        self.set_property("show-tics", show)
        self.emit("appearance_changed")

    def get_show_tics(self):
        """
        Returns True if tics are drawn.

        @return: boolean.
        """
        return self.get_property("show-tics")

    def set_show_tic_labels(self, show):
        """
        Set whether to draw tic labels. Labels are only drawn if
        tics are drawn.

        @type show: boolean.
        """
        self.set_property("show-tic-labels", show)
        self.emit("appearance_changed")

    def get_show_tic_labels(self):
        """
        Returns True if tic labels are shown.

        @return: boolean.
        """
        return self.get_property("show-tic-labels")

    def set_tic_format_function(self, func):
        """
        Use this to set the function that should be used to label
        the tics. The function should take a number as the only
        argument and return a string. Default: str

        @type func: function.
        """
        self.set_property("tic-format-function", func)
        self.emit("appearance_changed")

    def get_tic_format_function(self):
        """
        Returns the function currently used for labeling the tics.
        """
        return self.get_property("tic-format-function")
        
    def set_logarithmic(self, log):
        """
        Set whether the axis should use logarithmic (base 10) scale.
        
        @type log: boolean.
        """
        self.set_property("logarithmic", log)
        self.emit("appearance_changed")
        
    def get_logarithmic(self):
        """
        Returns True if the axis uses logarithmic scale.
        
        @return: boolean.
        """
        return self.get_property("logarithmic")


class XAxis(Axis):
    """
    This class represents the xaxis. It is used by the LineChart
    widget internally, there is no need to create an instance yourself.
    
    Properties
    ==========
    The XAxis class inherits properties from Axis.
    
    Signals
    =======
    The XAxis class inherits signals from Axis.
    """
    def __init__(self, range_calc):
        Axis.__init__(self, range_calc, "x")

    def draw(self, context, rect, yaxis):
        """
        This method is called by the parent Plot instance. It
        calls _do_draw.
        """
        if self._show:
            if not self._antialias:
                context.set_antialias(cairo.ANTIALIAS_NONE)
            self._do_draw(context, rect, yaxis)
            context.set_antialias(cairo.ANTIALIAS_DEFAULT)

    def _do_draw_tics(self, context, rect, yaxis):
        if self._show_tics:
            tics = self._range_calc.get_xtics(rect)
            
            #calculate yaxis position
            (zx, zy) = self._range_calc.get_absolute_zero(rect, self, yaxis)
            if yaxis.get_position() == POSITION_LEFT:
                zx = rect.width * GRAPH_PADDING
            elif yaxis.get_position() == POSITION_RIGHT:
                zx = rect.width * (1 - GRAPH_PADDING)

            for ((x,y), val) in tics:
                if self._position == POSITION_TOP:
                    y = rect.height * GRAPH_PADDING
                elif self._position == POSITION_BOTTOM:
                    y = rect.height * (1 - GRAPH_PADDING)
                tic_height = rect.height / 80.0
                context.move_to(x, y + tic_height / 2)
                context.rel_line_to(0, - tic_height)
                context.stroke()
                
                if self._show_tic_labels:
                    if abs(x - zx) < 10:
                        #the distance to the yaxis is to small => do not draw label
                        continue
                    pos = x, y + tic_height
                    text = self._tic_format_function(val)
                    tic_label = label.Label(pos, text, anchor=label.ANCHOR_TOP_CENTER, fixed=True)
                    tic_label.draw(context, rect)

    def _do_draw_label(self, context, rect, pos):
        axis_label = label.Label(pos, self._label, anchor=label.ANCHOR_LEFT_CENTER, fixed=True)
        axis_label.draw(context, rect)

    def _do_draw(self, context, rect, yaxis):
        """
        Draw the axis.
        """
        (zx, zy) = self._range_calc.get_absolute_zero(rect, self, yaxis)
        if self._position == POSITION_BOTTOM:
            zy = rect.height * (1 - GRAPH_PADDING)
        elif self._position == POSITION_TOP:
            zy = rect.height * GRAPH_PADDING
        if rect.height * GRAPH_PADDING <= zy and rect.height * (1 - GRAPH_PADDING) >= zy:
            context.set_source_rgb(0, 0, 0)
            #draw the line:
            context.move_to(rect.width * GRAPH_PADDING, zy)
            context.line_to(rect.width * (1 - GRAPH_PADDING), zy)
            context.stroke()
            #draw arrow:
            context.move_to(rect.width * (1 - GRAPH_PADDING) + 3, zy)
            context.rel_line_to(-3, -3)
            context.rel_line_to(0, 6)
            context.close_path()
            context.fill()

            if self._show_label:
                self._do_draw_label(context, rect, (rect.width * (1 - GRAPH_PADDING) + 3, zy))
            self._do_draw_tics(context, rect, yaxis)


class YAxis(Axis):
    """
    This class represents the yaxis. It is used by the LineChart
    widget internally, there is no need to create an instance yourself.
    
    Properties
    ==========
    The YAxis class inherits properties from Axis.
    
    Signals
    =======
    The YAxis class inherits signals from Axis.
    """
    def __init__(self, range_calc):
        Axis.__init__(self, range_calc, "y")

    def draw(self, context, rect, xaxis):
        """
        This method is called by the parent Plot instance. It
        calls _do_draw.
        """
        if self._show:
            if not self._antialias:
                context.set_antialias(cairo.ANTIALIAS_NONE)
            self._do_draw(context, rect, xaxis)
            context.set_antialias(cairo.ANTIALIAS_DEFAULT)

    def _do_draw_tics(self, context, rect, xaxis):
        if self._show_tics:
            tics = self._range_calc.get_ytics(rect)

            #calculate xaxis position
            (zx, zy) = self._range_calc.get_absolute_zero(rect, xaxis, self)
            if xaxis.get_position() == POSITION_BOTTOM:
                zy = rect.height * (1 - GRAPH_PADDING)
            elif xaxis.get_position() == POSITION_TOP:
                zy = rect.height * GRAPH_PADDING

            for ((x,y), val) in tics:
                if self._position == POSITION_LEFT:
                    x = rect.width * GRAPH_PADDING
                elif self._position == POSITION_RIGHT:
                    x = rect.width * (1 - GRAPH_PADDING)
                tic_width = rect.height / 80.0
                context.move_to(x + tic_width / 2, y)
                context.rel_line_to(- tic_width, 0)
                context.stroke()

                if self._show_tic_labels:
                    if abs(y - zy) < 10:
                        #distance to xaxis is to small => do not draw label
                        continue
                        
                    pos = x - tic_width, y
                    text = self._tic_format_function(val)
                    tic_label = label.Label(pos, text, anchor=label.ANCHOR_RIGHT_CENTER, fixed=True)
                    tic_label.draw(context, rect)


    def _do_draw_label(self, context, rect, pos):
        axis_label = label.Label(pos, self._label, anchor=label.ANCHOR_BOTTOM_CENTER, fixed=True)
        axis_label.draw(context, rect)

    def _do_draw(self, context, rect, xaxis):
        (zx, zy) = self._range_calc.get_absolute_zero(rect, xaxis, self)
        if self._position == POSITION_LEFT:
            zx = rect.width * GRAPH_PADDING
        elif self._position == POSITION_RIGHT:
            zx = rect.width * (1 - GRAPH_PADDING)
        if rect.width * GRAPH_PADDING <= zx and rect.width * (1 - GRAPH_PADDING) >= zx:
            context.set_source_rgb(0, 0, 0)
            #draw line:
            context.move_to(zx, rect.height * (1 - GRAPH_PADDING))
            context.line_to(zx, rect.height * GRAPH_PADDING)
            context.stroke()
            #draw arrow:
            context.move_to(zx, rect.height * GRAPH_PADDING - 3)
            context.rel_line_to(-3, 3)
            context.rel_line_to(6, 0)
            context.close_path()
            context.fill()

            if self._show_label:
                self._do_draw_label(context, rect, (zx, rect.height * GRAPH_PADDING - 3))
            self._do_draw_tics(context, rect, xaxis)


class Grid(ChartObject):
    """
    A class representing the grid of the chart. It is used by the LineChart
    widget internally, there is no need to create an instance yourself.
    
    Properties
    ==========
    The Grid class inherits properties from chart_object.ChartObject.
    Additional properties:
     - show-horizontal (sets whther to show horizontal grid lines,
       type: boolean)
     - show-vertical (sets whther to show vertical grid lines,
       type: boolean)
     - color (the color of the grid lines, type: gtk.gdk.Color)
     - line-style-horizontal (the line style of the horizontal grid
       lines, type: a line style constant)
     - line-style-vertical (the line style of the vertical grid lines,
       type: a line style constant).
       
    Signals
    =======
    The Grid class inherits signals from chart_object.ChartObject.
    """

    __gproperties__ = {"show-horizontal": (gobject.TYPE_BOOLEAN,
                                    "show horizontal lines",
                                    "Set whether to draw horizontal lines.",
                                    True, gobject.PARAM_READWRITE),
                        "show-vertical": (gobject.TYPE_BOOLEAN,
                                    "show vertical lines",
                                    "Set whether to draw vertical lines.",
                                    True, gobject.PARAM_READWRITE),
                        "color": (gobject.TYPE_PYOBJECT,
                                    "grid color",
                                    "The color of the grid in (r,g,b) format. r,g,b in [0,1]",
                                    gobject.PARAM_READWRITE),
                        "line-style-horizontal": (gobject.TYPE_INT,
                                                "horizontal line style",
                                                "Line Style for the horizontal grid lines",
                                                0, 3, 0, gobject.PARAM_READWRITE),
                        "line-style-vertical": (gobject.TYPE_INT,
                                                "vertical line style",
                                                "Line Style for the vertical grid lines",
                                                0, 3, 0, gobject.PARAM_READWRITE)}

    def __init__(self, range_calc):
        ChartObject.__init__(self)
        self.set_property("antialias", False)
        self._range_calc = range_calc
        self._color = gtk.gdk.color_parse("#DEDEDE")
        self._show_h = True
        self._show_v = True
        self._line_style_h = pygtk_chart.LINE_STYLE_SOLID
        self._line_style_v = pygtk_chart.LINE_STYLE_SOLID

    def do_get_property(self, property):
        if property.name == "visible":
            return self._show
        elif property.name == "antialias":
            return self._antialias
        elif property.name == "show-horizontal":
            return self._show_h
        elif property.name == "show-vertical":
            return self._show_v
        elif property.name == "color":
            return self._color
        elif property.name == "line-style-horizontal":
            return self._line_style_h
        elif property.name == "line-style-vertical":
            return self._line_style_v
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def do_set_property(self, property, value):
        if property.name == "visible":
            self._show = value
        elif property.name == "antialias":
            self._antialias = value
        elif property.name == "show-horizontal":
            self._show_h = value
        elif property.name == "show-vertical":
            self._show_v = value
        elif property.name == "color":
            self._color = value
        elif property.name == "line-style-horizontal":
            self._line_style_h = value
        elif property.name == "line-style-vertical":
            self._line_style_v = value
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def _do_draw(self, context, rect, xaxis, yaxis):
        context.set_source_rgb(*color_gdk_to_cairo(self._color))
        #draw horizontal lines
        if self._show_h:
            set_context_line_style(context, self._line_style_h)
            ytics = self._range_calc.get_ytics(rect)
            xa = rect.width * GRAPH_PADDING
            xb = rect.width * (1 - GRAPH_PADDING)
            for ((x, y), label) in ytics:
                context.move_to(xa, y)
                context.line_to(xb, y)
                context.stroke()
            context.set_dash([])

        #draw vertical lines
        if self._show_v:
            set_context_line_style(context, self._line_style_v)
            xtics = self._range_calc.get_xtics(rect)
            ya = rect.height * GRAPH_PADDING
            yb = rect.height * (1 - GRAPH_PADDING)
            for ((x, y), label) in xtics:
                context.move_to(x, ya)
                context.line_to(x, yb)
                context.stroke()
            context.set_dash([])

    def set_draw_horizontal_lines(self, draw):
        """
        Set whether to draw horizontal grid lines.

        @type draw: boolean.
        """
        self.set_property("show-horizontal", draw)
        self.emit("appearance_changed")

    def get_draw_horizontal_lines(self):
        """
        Returns True if horizontal grid lines are drawn.

        @return: boolean.
        """
        return self.get_property("show-horizontal")

    def set_draw_vertical_lines(self, draw):
        """
        Set whether to draw vertical grid lines.

        @type draw: boolean.
        """
        self.set_property("show-vertical", draw)
        self.emit("appearance_changed")

    def get_draw_vertical_lines(self):
        """
        Returns True if vertical grid lines are drawn.

        @return: boolean.
        """
        return self.get_property("show-vertical")

    def set_color(self, color):
        """
        Set the color of the grid.

        @type color: gtk.gdk.Color
        @param color: The new color of the grid.
        """
        self.set_property("color", color)
        self.emit("appearance_changed")

    def get_color(self):
        """
        Returns the color of the grid.

        @return: gtk.gdk.Color.
        """
        return self.get_property("color")
        
    def set_line_style_horizontal(self, style):
        """
        Set the line style of the horizontal grid lines.
        style has to be one of these constants:
         - pygtk_chart.LINE_STYLE_SOLID (default)
         - pygtk_chart.LINE_STYLE_DOTTED
         - pygtk_chart.LINE_STYLE_DASHED
         - pygtk_chart.LINE_STYLE_DASHED_ASYMMETRIC.
        
        @param style: the new line style
        @type style: one of the constants above.
        """
        self.set_property("line-style-horizontal", style)
        self.emit("appearance_changed")
        
    def get_line_style_horizontal(self):
        """
        Returns ths current horizontal line style.
        
        @return: a line style constant.
        """
        return self.get_property("line-style-horizontal")
        
    def set_line_style_vertical(self, style):
        """
        Set the line style of the vertical grid lines.
        style has to be one of these constants:
         - pygtk_chart.LINE_STYLE_SOLID (default)
         - pygtk_chart.LINE_STYLE_DOTTED
         - pygtk_chart.LINE_STYLE_DASHED
         - pygtk_chart.LINE_STYLE_DASHED_ASYMMETRIC.
        
        @param style: the new line style
        @type style: one of the constants above.
        """
        self.set_property("line-style-vertical", style)
        self.emit("appearance_changed")
        
    def get_line_style_vertical(self):
        """
        Returns ths current vertical line style.
        
        @return: a line style constant.
        """
        return self.get_property("line-style-vertical")


class Graph(ChartObject):
    """
    This class represents a graph or the data you want to plot on your
    LineChart widget.
    
    Properties
    ==========
    The Graph class inherits properties from chart_object.ChartObject.
    Additional properties:
     - name (a unique id for the graph, type: string, read only)
     - title (the graph's title, type: string)
     - color (the graph's color, type: gtk.gdk.Color)
     - type (graph type, type: a graph type constant)
     - point-size (radius of the datapoints in px,
       type: int in [1, 100])
     - fill-to (set how to fill space under the graph, type: None,
       Graph or float)
     - fill-color (the color of the filling, type: gtk.gdk.Color)
     - fill-opacity (the opacity of the filling, type: float in [0, 1])
     - show-values (sets whether y values should be shown at the
       datapoints, type: boolean)
     - show-title (sets whether ot show the graph's title,
       type: boolean)
     - line-style (the graph's line style, type: a line style constant)
     - point-style (the graph's datapoints' point style,
       type: a point style constant)
     - clickable (sets whether datapoints are sensitive for clicks,
       type: boolean)
     - show-xerrors (sets whether x errors should be shown if error data
       is available, type: boolean)
     - show-yerrors (sets whether y errors should be shown if error data
       is available, type: boolean).
       
    Signals
    =======
    The Graph class inherits signals from chart_object.ChartObject.
    """

    __gproperties__ = {"name": (gobject.TYPE_STRING, "graph id",
                                "The graph's unique name.",
                                "", gobject.PARAM_READABLE),
                        "title": (gobject.TYPE_STRING, "graph title",
                                    "The title of the graph.", "",
                                    gobject.PARAM_READWRITE),
                        "color": (gobject.TYPE_PYOBJECT,
                                    "graph color",
                                    "The color of the graph in (r,g,b) format. r,g,b in [0,1].",
                                    gobject.PARAM_READWRITE),
                        "type": (gobject.TYPE_INT, "graph type",
                                    "The type of the graph.", 1, 3, 3,
                                    gobject.PARAM_READWRITE),
                        "point-size": (gobject.TYPE_INT, "point size",
                                        "Radius of the data points.", 1,
                                        100, 2, gobject.PARAM_READWRITE),
                        "fill-to": (gobject.TYPE_PYOBJECT, "fill to",
                                    "Set how to fill space under the graph.",
                                    gobject.PARAM_READWRITE),
                        "fill-color": (gobject.TYPE_PYOBJECT, "fill color",
                                    "Set which color to use when filling space under the graph.",
                                    gobject.PARAM_READWRITE),
                        "fill-opacity": (gobject.TYPE_FLOAT, "fill opacity",
                                    "Set which opacity to use when filling space under the graph.",
                                    0.0, 1.0, 0.3, gobject.PARAM_READWRITE),
                        "show-values": (gobject.TYPE_BOOLEAN, "show values",
                                    "Sets whether to show the y values.",
                                    False, gobject.PARAM_READWRITE),
                        "show-title": (gobject.TYPE_BOOLEAN, "show title",
                                    "Sets whether to show the graph's title.",
                                    True, gobject.PARAM_READWRITE),
                        "line-style": (gobject.TYPE_INT, "line style",
                                     "The line style to use.", 0, 3, 0,
                                     gobject.PARAM_READWRITE),
                        "point-style": (gobject.TYPE_PYOBJECT, "point style",
                                        "The graph's point style.",
                                        gobject.PARAM_READWRITE),
                        "clickable": (gobject.TYPE_BOOLEAN, "clickable",
                                    "Sets whether datapoints should be clickable.",
                                    True, gobject.PARAM_READWRITE),
                        "show-xerrors": (gobject.TYPE_BOOLEAN,
                                            "show xerrors",
                                            "Set whether to show x-errorbars.",
                                            True, gobject.PARAM_READWRITE),
                        "show-yerrors": (gobject.TYPE_BOOLEAN,
                                            "show yerrors",
                                            "Set whether to show y-errorbars.",
                                            True, gobject.PARAM_READWRITE)}

    def __init__(self, name, title, data):
        """
        Create a new graph instance.
        data should be a list of x,y pairs. If you want to provide
        error data for a datapoint, the tuple for that point has to be
        (x, y, xerror, yerror). If you want only one error, set the
        other to zero. You can mix datapoints with and without error
        data in data.

        @type name: string
        @param name: A unique name for the graph. This could be everything.
        It's just a name used internally for identification. You need to know
        this if you want to access or delete a graph from a chart.
        @type title: string
        @param title: The graphs title. This can be drawn on the chart.
        @type data: list (see above)
        @param data: This is the data you want to be visualized. For
        detail see description above.
        """
        ChartObject.__init__(self)
        self._name = name
        self._title = title
        self._data, self._errors = separate_data_and_errors(data)
        self._color = COLOR_AUTO
        self._type = GRAPH_BOTH
        self._point_size = 2
        self._show_value = False
        self._show_title = True
        self._fill_to = None
        self._fill_color = COLOR_AUTO
        self._fill_opacity = 0.3
        self._line_style = pygtk_chart.LINE_STYLE_SOLID
        self._point_style = pygtk_chart.POINT_STYLE_CIRCLE
        self._clickable = True
        self._draw_xerrors = True
        self._draw_yerrors = True

        self._range_calc = None
        self._label = label.Label((0, 0), self._title, anchor=label.ANCHOR_LEFT_CENTER)

    def do_get_property(self, property):
        if property.name == "visible":
            return self._show
        elif property.name == "antialias":
            return self._antialias
        elif property.name == "name":
            return self._name
        elif property.name == "title":
            return self._title
        elif property.name == "color":
            return self._color
        elif property.name == "type":
            return self._type
        elif property.name == "point-size":
            return self._point_size
        elif property.name == "fill-to":
            return self._fill_to
        elif property.name == "fill-color":
            return self._fill_color
        elif property.name == "fill-opacity":
            return self._fill_opacity
        elif property.name == "show-values":
            return self._show_value
        elif property.name == "show-title":
            return self._show_title
        elif property.name == "line-style":
            return self._line_style
        elif property.name == "point-style":
            return self._point_style
        elif property.name == "clickable":
            return self._clickable
        elif property.name == "show-xerrors":
            return self._draw_xerrors
        elif property.name == "show-yerrors":
            return self._draw_yerrors
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def do_set_property(self, property, value):
        if property.name == "visible":
            self._show = value
        elif property.name == "antialias":
            self._antialias = value
        elif property.name == "title":
            self._label.set_text(value)
            self._title = value
        elif property.name == "color":
            self._color = value
        elif property.name == "type":
            self._type = value
        elif property.name == "point-size":
            self._point_size = value
        elif property.name == "fill-to":
            self._fill_to = value
        elif property.name == "fill-color":
            self._fill_color = value
        elif property.name == "fill-opacity":
            self._fill_opacity = value
        elif property.name == "show-values":
            self._show_value = value
        elif property.name == "show-title":
            self._show_title = value
        elif property.name == "line-style":
            self._line_style = value
        elif property.name == "point-style":
            self._point_style = value
        elif property.name == "clickable":
            self._clickable = value
        elif property.name == "show-xerrors":
            self._draw_xerrors = value
        elif property.name == "show-yerrors":
            self._draw_yerrors = value
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def has_something_to_draw(self):
        return self._data != []
        
    def _do_draw_lines(self, context, rect, xrange, yrange, xaxis, yaxis):
        context.set_source_rgb(*color_gdk_to_cairo(self._color))
        
        set_context_line_style(context, self._line_style)
        
        first_point = None
        last_point = None
        
        for (x, y) in self._data:
            
            if xaxis.get_logarithmic():
                x = math.log10(x)
            if yaxis.get_logarithmic():
                y = math.log10(y)
                
            if is_in_range(x, xrange) and is_in_range(y, yrange):
                (ax, ay) = self._range_calc.get_absolute_point(rect, x, y, xaxis, yaxis)
                if first_point == None:
                    context.move_to(ax, ay)
                    first_point = x, y
                else:
                    context.line_to(ax, ay)
                last_point = ax, ay
                    
        context.stroke()
        context.set_dash([])
        return first_point, last_point
        
    def _do_draw_points(self, context, rect, xrange, yrange, xaxis, yaxis, highlighted_points):
        context.set_source_rgb(*color_gdk_to_cairo(self._color))
        
        first_point = None
        last_point = None
        
        for (x, y) in self._data:
            if xaxis.get_logarithmic():
                x = math.log10(x)
            if yaxis.get_logarithmic():
                y = math.log10(y)
            
            if is_in_range(x, xrange) and is_in_range(y, yrange):
                (ax, ay) = self._range_calc.get_absolute_point(rect, x, y, xaxis, yaxis)
                if self._clickable:
                    chart.add_sensitive_area(chart.AREA_CIRCLE, (ax, ay, self._point_size), (x, y, self))
                if first_point == None:
                    context.move_to(ax, ay)
                    
                #draw errors
                draw_errors(context, rect, self._range_calc, x, y, self._errors, self._draw_xerrors, self._draw_yerrors, xaxis, yaxis, self._point_size)
                    
                #draw the point
                if type(self._point_style) != gtk.gdk.Pixbuf:
                    draw_point(context, ax, ay, self._point_size, self._point_style)
                    highlighted = (x, y, self) in highlighted_points
                    if highlighted and self._clickable:
                        context.set_source_rgba(1, 1, 1, 0.3)
                        draw_point(context, ax, ay, self._point_size, self._point_style)
                        context.set_source_rgb(*color_gdk_to_cairo(self._color))
                else:
                    draw_point_pixbuf(context, ax, ay, self._point_style)
                    
                last_point = ax, ay
        return first_point, last_point
        
    def _do_draw_values(self, context, rect, xrange, yrange, xaxis, yaxis):
        anchors = {}
        first_point = True
        for i, (x, y) in enumerate(self._data):
            
            if xaxis.get_logarithmic():
                x = math.log10(x)
            if yaxis.get_logarithmic():
                y = math.log10(y)
            
            if is_in_range(x, xrange) and is_in_range(y, yrange):
                next_point = None
                if i + 1 < len(self._data) and (is_in_range(self._data[i + 1][0], xrange) and is_in_range(self._data[i + 1][1], yrange)):
                    next_point = self._data[i + 1]
                if first_point:
                    if next_point != None:
                        if next_point[1] >= y:
                            anchors[(x, y)] = label.ANCHOR_TOP_LEFT
                        else:
                            anchors[(x, y)] = label.ANCHOR_BOTTOM_LEFT
                    first_point = False
                else:
                    previous_point = self._data[i - 1]
                    if next_point != None:
                        if previous_point[1] <= y <= next_point[1]:
                            anchors[(x, y)] = label.ANCHOR_BOTTOM_RIGHT
                        elif previous_point[1] > y > next_point[1]:
                            anchors[(x, y)] = label.ANCHOR_BOTTOM_LEFT
                        elif previous_point[1] < y and next_point[1] < y:
                            anchors[(x, y)] = label.ANCHOR_BOTTOM_CENTER
                        elif previous_point[1] > y and next_point[1] > y:
                            anchors[(x, y)] = label.ANCHOR_TOP_CENTER
                    else:
                        if previous_point[1] >= y:
                            anchors[(x, y)] = label.ANCHOR_TOP_RIGHT
                        else:
                            anchors[(x, y)] = label.ANCHOR_BOTTOM_RIGHT
                            
        for x, y in self._data:
            
            if xaxis.get_logarithmic():
                x = math.log10(x)
            if yaxis.get_logarithmic():
                y = math.log10(y)
            
            if (x, y) in anchors and is_in_range(x, xrange) and is_in_range(y, yrange):
                (ax, ay) = self._range_calc.get_absolute_point(rect, x, y, xaxis, yaxis)
                value_label = label.Label((ax, ay), str(y), anchor=anchors[(x, y)])
                value_label.set_color(self._color)
                value_label.draw(context, rect)

    def _do_draw_title(self, context, rect, last_point, xaxis, yaxis):
        """
        Draws the title.

        @type context: cairo.Context
        @param context: The context to draw on.
        @type rect: gtk.gdk.Rectangle
        @param rect: A rectangle representing the charts area.
        @type last_point: pairs of numbers
        @param last_point: The absolute position of the last drawn data point.
        """
        if last_point:
            x = last_point[0] + 5
            y = last_point[1]
            self._label.set_position((x, y))
            self._label.set_color(self._color)
            self._label.draw(context, rect)
            
    def _do_draw_fill(self, context, rect, xrange, xaxis, yaxis):
        if type(self._fill_to) in (int, float):
            data = []
            for i, (x, y) in enumerate(self._data):
                
                if xaxis.get_logarithmic():
                    x = math.log10(x)
                if yaxis.get_logarithmic():
                    y = math.log10(y)
                
                if is_in_range(x, xrange) and not data:
                    data.append((x, self._fill_to))
                elif not is_in_range(x, xrange) and len(data) == 1:
                    data.append((prev, self._fill_to))
                    break
                elif i == len(self._data) - 1:
                    data.append((x, self._fill_to))
                prev = x
            graph = Graph("none", "", data)
        elif type(self._fill_to) == Graph:
            graph = self._fill_to
            d = graph.get_data()
            range_b = d[0][0], d[-1][0]
            xrange = intersect_ranges(xrange, range_b)
            
        if not graph.get_visible(): return
        
        c = self._fill_color
        if c == COLOR_AUTO: c = self._color
        c = color_gdk_to_cairo(c)
        context.set_source_rgba(c[0], c[1], c[2], self._fill_opacity)
        
        data_a = self._data
        data_b = graph.get_data()
        
        first = True
        start_point = (0, 0)
        for x, y in data_a:
            
            if xaxis.get_logarithmic():
                x = math.log10(x)
            if yaxis.get_logarithmic():
                y = math.log10(y)
            
            if is_in_range(x, xrange):
                xa, ya = self._range_calc.get_absolute_point(rect, x, y, xaxis, yaxis)
                if first:
                    context.move_to(xa, ya)
                    start_point = xa, ya
                    first = False
                else:
                    context.line_to(xa, ya)
                
        first = True
        for i in range(0, len(data_b)):
            j = len(data_b) - i - 1
            x, y = data_b[j]
            xa, ya = self._range_calc.get_absolute_point(rect, x, y, xaxis, yaxis)
            if is_in_range(x, xrange):
                context.line_to(xa, ya)
        context.line_to(*start_point)
        context.fill()

    def _do_draw(self, context, rect, xaxis, yaxis, highlighted_points):
        """
        Draw the graph.

        @type context: cairo.Context
        @param context: The context to draw on.
        @type rect: gtk.gdk.Rectangle
        @param rect: A rectangle representing the charts area.
        """
        (xrange, yrange) = self._range_calc.get_ranges(xaxis, yaxis)
                
        if self._type in [GRAPH_LINES, GRAPH_BOTH]:
            first_point, last_point = self._do_draw_lines(context, rect, xrange, yrange, xaxis, yaxis)
            
        if self._type in [GRAPH_POINTS, GRAPH_BOTH]:
            first_point, last_point = self._do_draw_points(context, rect, xrange, yrange, xaxis, yaxis, highlighted_points)

        if self._fill_to != None:
            self._do_draw_fill(context, rect, xrange, xaxis, yaxis)
        
        if self._show_value and self._type in [GRAPH_POINTS, GRAPH_BOTH]:
            self._do_draw_values(context, rect, xrange, yrange, xaxis, yaxis)

        if self._show_title:
            self._do_draw_title(context, rect, last_point, xaxis, yaxis)

    def get_x_range(self):
        """
        Get the the endpoints of the x interval.

        @return: pair of numbers
        """
        try:
            self._data.sort(lambda x, y: cmp(x[0], y[0]))
            return (self._data[0][0], self._data[-1][0])
        except:
            return None

    def get_y_range(self):
        """
        Get the the endpoints of the y interval.

        @return: pair of numbers
        """
        try:
            self._data.sort(lambda x, y: cmp(x[1], y[1]))
            return (self._data[0][1], self._data[-1][1])
        except:
            return None

    def get_name(self):
        """
        Get the name of the graph.

        @return: string
        """
        return self.get_property("name")

    def get_title(self):
        """
        Returns the title of the graph.

        @return: string
        """
        return self.get_property("title")

    def set_title(self, title):
        """
        Set the title of the graph.

        @type title: string
        @param title: The graph's new title.
        """
        self.set_property("title", title)
        self.emit("appearance_changed")

    def set_range_calc(self, range_calc):
        self._range_calc = range_calc

    def get_color(self):
        """
        Returns the current color of the graph or COLOR_AUTO.

        @return: gtk.gdk.Color or COLOR_AUTO.
        """
        return self.get_property("color")

    def set_color(self, color):
        """
        Set the color of the graph.
        If set to COLOR_AUTO, the color will be choosen dynamicly.

        @type color: gtk.gdk.Color
        @param color: The new color of the graph.
        """
        self.set_property("color", color)
        self.emit("appearance_changed")

    def get_type(self):
        """
        Returns the type of the graph.

        @return: a type constant (see set_type() for details)
        """
        return self.get_property("type")

    def set_type(self, type):
        """
        Set the type of the graph to one of these:
         - GRAPH_POINTS: only show points
         - GRAPH_LINES: only draw lines
         - GRAPH_BOTH: draw points and lines, i.e. connect points with lines

        @param type: One of the constants above.
        """
        self.set_property("type", type)
        self.emit("appearance_changed")

    def get_point_size(self):
        """
        Returns the radius of the data points.

        @return: a poisitive integer
        """
        return self.get_property("point_size")

    def set_point_size(self, size):
        """
        Set the radius of the drawn points.

        @type size: a positive integer in [1, 100]
        @param size: The new radius of the points.
        """
        self.set_property("point_size", size)
        self.emit("appearance_changed")

    def get_fill_to(self):
        """
        The return value of this method depends on the filling under
        the graph. See set_fill_to() for details.
        """
        return self.get_property("fill-to")

    def set_fill_to(self, fill_to):
        """
        Use this method to specify how the space under the graph should
        be filled. fill_to has to be one of these:
        
         - None: dont't fill the space under the graph.
         - int or float: fill the space to the value specified (setting
           fill_to=0 means filling the space between graph and xaxis).
         - a Graph object: fill the space between this graph and the
           graph given as the argument.
           
        The color of the filling is the graph's color with 30% opacity.
           
        @type fill_to: one of the possibilities listed above.
        """
        self.set_property("fill-to", fill_to)
        self.emit("appearance_changed")
        
    def get_fill_color(self):
        """
        Returns the color that is used to fill space under the graph
        or COLOR_AUTO.
        
        @return: gtk.gdk.Color or COLOR_AUTO.
        """
        return self.get_property("fill-color")
        
    def set_fill_color(self, color):
        """
        Set which color should be used when filling the space under a
        graph.
        If color is COLOR_AUTO, the graph's color will be used.
        
        @type color: gtk.gdk.Color or COLOR_AUTO.
        """
        self.set_property("fill-color", color)
        self.emit("appearance_changed")
        
    def get_fill_opacity(self):
        """
        Returns the opacity that is used to fill space under the graph.
        """
        return self.get_property("fill-opacity")
        
    def set_fill_opacity(self, opacity):
        """
        Set which opacity should be used when filling the space under a
        graph. The default is 0.3.
        
        @type opacity: float in [0, 1].
        """
        self.set_property("fill-opacity", opacity)
        self.emit("appearance_changed")

    def get_show_values(self):
        """
        Returns True if y values are shown.

        @return: boolean
        """
        return self.get_property("show-values")

    def set_show_values(self, show):
        """
        Set whether the y values should be shown (only if graph type
        is GRAPH_POINTS or GRAPH_BOTH).

        @type show: boolean
        """
        self.set_property("show-values", show)
        self.emit("appearance_changed")

    def get_show_title(self):
        """
        Returns True if the title of the graph is shown.

        @return: boolean.
        """
        return self.get_property("show-title")

    def set_show_title(self, show):
        """
        Set whether to show the graph's title or not.

        @type show: boolean.
        """
        self.set_property("show-title", show)
        self.emit("appearance_changed")

    def add_data(self, data_list):
        """
        Add data to the graph.
        data_list should be a list of x,y pairs. If you want to provide
        error data for a datapoint, the tuple for that point has to be
        (x, y, xerror, yerror). If you want only one error, set the
        other to zero. You can mix datapoints with and without error
        data in data_list.

        @type data_list: a list (see above).
        """
        new_data, new_errors = separate_data_and_errors(data_list)
        self._data += new_data
        self._errors = dict(self._errors, **new_errors)
        self._range_calc.add_graph(self)
        
    def get_data(self):
        """
        Returns the data of the graph.
        
        @return: a list of x, y pairs.
        """
        return self._data
        
    def set_line_style(self, style):
        """
        Set the line style that should be used for drawing the graph
        (if type is line_chart.GRAPH_LINES or line_chart.GRAPH_BOTH).
        style has to be one of these constants:
         - pygtk_chart.LINE_STYLE_SOLID (default)
         - pygtk_chart.LINE_STYLE_DOTTED
         - pygtk_chart.LINE_STYLE_DASHED
         - pygtk_chart.LINE_STYLE_DASHED_ASYMMETRIC.
        
        @param style: the new line style
        @type style: one of the line style constants above.
        """
        self.set_property("line-style", style)
        self.emit("appearance_changed")
        
    def get_line_style(self):
        """
        Returns the current line style for the graph (see
        L{set_line_style} for details).
        
        @return: a line style constant.
        """
        return self.get_property("line-style")
        
    def set_point_style(self, style):
        """
        Set the point style that should be used when drawing the graph
        (if type is line_chart.GRAPH_POINTS or line_chart.GRAPH_BOTH).
        For style you can use one of these constants:
         - pygtk_chart.POINT_STYLE_CIRCLE (default)
         - pygtk_chart.POINT_STYLE_SQUARE
         - pygtk_chart.POINT_STYLE_CROSS
         - pygtk_chart.POINT_STYLE_TRIANGLE_UP
         - pygtk_chart.POINT_STYLE_TRIANGLE_DOWN
         - pygtk_chart.POINT_STYLE_DIAMOND
        style can also be a gtk.gdk.Pixbuf that should be used as point.
        
        @param style: the new point style
        @type style: one of the cosnatnts above or gtk.gdk.Pixbuf.
        """
        self.set_property("point-style", style)
        self.emit("appearance_changed")
        
    def get_point_style(self):
        """
        Returns the current point style. See L{set_point_style} for 
        details.
        
        @return: a point style constant or gtk.gdk.Pixbuf.
        """
        return self.get_property("point-style")
        
    def set_clickable(self, clickable):
        """
        Set whether the datapoints of the graph should be clickable
        (only if the datapoints are shown).
        If this is set to True, the LineChart will emit the signal
        'datapoint-clicked' when a datapoint was clicked.
        
        @type clickable: boolean.
        """
        self.set_property("clickable", clickable)
        self.emit("appearance_changed")
        
    def get_clickable(self):
        """
        Returns True if the datapoints of the graph are clickable.
        
        @return: boolean.
        """
        return self.get_property("clickable")
        
    def set_show_xerrors(self, show):
        """
        Use this method to set whether x-errorbars should be shown
        if error data is available.
        
        @type show: boolean.
        """
        self.set_property("show-xerrors", show)
        self.emit("appearance_changed")
        
    def get_show_xerrors(self):
        """
        Returns True if x-errorbars should be drawn if error data is
        available.
        
        @return: boolean.
        """
        return self.get_property("show-xerrors")
        
    def set_show_yerrors(self, show):
        """
        Use this method to set whether y-errorbars should be shown
        if error data is available.
        
        @type show: boolean.
        """
        self.set_property("show-yerrors", show)
        self.emit("appearance_changed")
        
    def get_show_yerrors(self):
        """
        Returns True if y-errorbars should be drawn if error data is
        available.
        
        @return: boolean.
        """
        return self.get_property("show-yerrors")
        
        
def graph_new_from_function(func, xmin, xmax, graph_name, samples=100, do_optimize_sampling=True):
    """
    Returns a line_chart.Graph with data created from the function
    y = func(x) with x in [xmin, xmax]. The id of the new graph is
    graph_name.
    The parameter samples gives the number of points that should be
    evaluated in [xmin, xmax] (default: 100).
    If do_optimize_sampling is True (default) additional points will be
    evaluated to smoothen the curve.
    
    @type func: a function
    @param func: the function to evaluate
    @type xmin: float
    @param xmin: the minimum x value to evaluate
    @type xmax: float
    @param xmax: the maximum x value to evaluate
    @type graph_name: string
    @param graph_name: a unique name for the new graph
    @type samples: int
    @param samples: number of samples
    @type do_optimize_sampling: boolean
    @param do_optimize_sampling: set whether to add additional points
    
    @return: line_chart.Graph    
    """
    delta = (xmax - xmin) / float(samples - 1)
    data = []
    x = xmin
    while x <= xmax:
        data.append((x, func(x)))
        x += delta
        
    if do_optimize_sampling:
        data = optimize_sampling(func, data)
        
    return Graph(graph_name, "", data)
    
def optimize_sampling(func, data):
    new_data = []
    prev_point = None
    prev_slope = None
    for x, y in data:
        if prev_point != None:
            if (x - prev_point[0]) == 0: return data
            slope = (y - prev_point[1]) / (x - prev_point[0])
            if prev_slope != None:
                if abs(slope - prev_slope) >= 0.1:
                    nx = prev_point[0] + (x - prev_point[0]) / 2.0
                    ny = func(nx)
                    new_data.append((nx, ny))
                    #print abs(slope - prev_slope), prev_point[0], nx, x
            prev_slope = slope
        
        prev_point = x, y
    
    if new_data:
        data += new_data
        data.sort(lambda x, y: cmp(x[0], y[0]))
        return optimize_sampling(func, data)
    else:
        return data
        
def graph_new_from_file(filename, graph_name, x_col=0, y_col=1, xerror_col=-1, yerror_col=-1):
    """
    Returns a line_chart.Graph with point taken from data file
    filename.
    The id of the new graph is graph_name.    
    
    Data file format:
    The columns in the file have to be separated by tabs or one
    or more spaces. Everything after '#' is ignored (comment).
    
    Use the parameters x_col and y_col to control which columns to use
    for plotting. By default, the first column (x_col=0) is used for
    x values, the second (y_col=1) is used for y values.
    
    The parameters xerror_col and yerror_col should point to the column
    in which the x/y error values are. If you do not want to provide
    x or y error data, omit the paramter or set it to -1 (default).
    
    @type filename: string
    @param filename: path to the data file
    @type graph_name: string
    @param graph_name: a unique name for the graph
    @type x_col: int
    @param x_col: the number of the column to use for x values
    @type y_col: int
    @param y_col: the number of the column to use for y values
    @type xerror_col: int
    @param xerror_col: index of the column for x error values
    @type yerror_col: int
    @param yerror_col: index of the column for y error values
    
    @return: line_chart.Graph
    """
    points = []
    f = open(filename, "r")
    data = f.read()
    f.close()
    lines = data.split("\n")
    
    for line in lines:
        line = line.strip() #remove special characters at beginning and end
        
        #remove comments:
        a = line.split("#", 1)
        if a and a[0]:
            line = a[0]
            #get data from line:
            if line.find("\t") != -1:
                #col separator is tab
                d = line.split("\t")
            else:
                #col separator is one or more space
                #normalize to one space:
                while line.find("  ") != -1:
                    line = line.replace("  ", " ")
                d = line.split(" ")
            d = filter(lambda x: x, d)
            d = map(lambda x: float(x), d)
            
            new_data = (d[x_col], d[y_col])
            
            if xerror_col != -1 or yerror_col != -1:
                xerror = 0
                yerror = 0
                
                if xerror_col != -1:
                    xerror = d[xerror_col]
                if yerror_col != -1:
                    yerror = d[yerror_col]
                
                new_data = (d[x_col], d[y_col], xerror, yerror)
                
            points.append(new_data)
    return Graph(graph_name, "", points)


class Legend(ChartObject):
    """
    This class represents a legend on a line chart.
    
    Properties
    ==========
    The Legend class inherits properties from chart_object.ChartObject.
    Additional properties:
     - position (the legend's position on the chart, type: a corner
       position constant).
       
    Signals
    =======
    The Legend class inherits signals from chart_object.ChartObject.    
    """
    
    __gproperties__ = {"position": (gobject.TYPE_INT, "legend position",
                                    "Position of the legend.", 8, 11, 8,
                                    gobject.PARAM_READWRITE)}
    
    def __init__(self):
        ChartObject.__init__(self)
        self._show = False
        self._position = POSITION_TOP_RIGHT
        
    def do_get_property(self, property):
        if property.name == "visible":
            return self._show
        elif property.name == "antialias":
            return self._antialias
        elif property.name == "position":
            return self._position
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def do_set_property(self, property, value):
        if property.name == "visible":
            self._show = value
        elif property.name == "antialias":
            self._antialias = value
        elif property.name == "position":
            self._position = value
        else:
            raise AttributeError, "Property %s does not exist." % property.name
        
    def _do_draw(self, context, rect, graphs):
        context.set_line_width(1)
        width = 0.2 * rect.width
        label_width = width - 12 - 20

        x = rect.width - width
        y = 16
        
        total_height = 0
        total_width = 0
        for id, graph in graphs.iteritems():
            if not graph.get_visible(): continue
            graph_label = label.Label((x + (width - label_width), y), graph.get_title(), anchor=label.ANCHOR_TOP_LEFT)
            graph_label.set_max_width(label_width)
            
            rwidth, rheight = graph_label.get_calculated_dimensions(context, rect)
            
            total_height += rheight + 6
            total_width = max(total_width, rwidth)
            
        total_width += 18 + 20
        if self._position == POSITION_TOP_RIGHT:
            x = rect.width - total_width - 16
            y = 16
        elif self._position == POSITION_BOTTOM_RIGHT:
            x = rect.width - total_width - 16
            y = rect.height - 16 - total_height
        elif self._position == POSITION_BOTTOM_LEFT:
            x = 16
            y = rect.height - 16 - total_height
        elif self._position == POSITION_TOP_LEFT:
            x = 16
            y = 16
        
        context.set_antialias(cairo.ANTIALIAS_NONE)
        context.set_source_rgb(1, 1, 1)
        context.rectangle(x, y - 3, total_width, total_height)
        context.fill_preserve()
        context.set_source_rgb(0, 0, 0)
        context.stroke()
        context.set_antialias(cairo.ANTIALIAS_DEFAULT)
        
        for id, graph in graphs.iteritems():
            if not graph.get_visible(): continue
            #draw the label
            graph_label = label.Label((x + (width - label_width), y), graph.get_title(), anchor=label.ANCHOR_TOP_LEFT)
            graph_label.set_max_width(label_width)
            graph_label.draw(context, rect)
            
            #draw line
            if graph.get_type() in [GRAPH_LINES, GRAPH_BOTH]:
                lines = graph_label.get_line_count()
                line_height = graph_label.get_real_dimensions()[1] / lines
                set_context_line_style(context, graph.get_line_style())
                context.set_source_rgb(*color_gdk_to_cairo(graph.get_color()))
                context.move_to(x + 6, y + line_height / 2)
                context.rel_line_to(20, 0)
                context.stroke()
            #draw point
            if graph.get_type() in [GRAPH_POINTS, GRAPH_BOTH]:
                lines = graph_label.get_line_count()
                line_height = graph_label.get_real_dimensions()[1] / lines
                context.set_source_rgb(*color_gdk_to_cairo(graph.get_color()))
                if type(graph.get_point_style()) != gtk.gdk.Pixbuf:
                    draw_point(context, x + 6 + 20, y + line_height / 2, graph.get_point_size(), graph.get_point_style())
                else:
                    draw_point_pixbuf(context, x + 6 + 20, y + line_height / 2, graph.get_point_style())
                    
            
            y += graph_label.get_real_dimensions()[1] + 6
            
    def set_position(self, position):
        """
        Set the position of the legend. position has to be one of these
        position constants:
         - line_chart.POSITION_TOP_RIGHT (default)
         - line_chart.POSITION_BOTTOM_RIGHT
         - line_chart.POSITION_BOTTOM_LEFT
         - line_chart.POSITION_TOP_LEFT
        
        @param position: the legend's position
        @type position: one of the constants above.
        """
        self.set_property("position", position)
        self.emit("appearance_changed")
        
    def get_position(self):
        """
        Returns the position of the legend. See L{set_position} for
        details.
        
        @return: a position constant.
        """
        return self.get_property("position")
