#!/usr/bin/env python
#
#       plot.py
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
Module Contents
===============
This is the main module. It contains the base classes for chart widgets.
 - class Chart: base class for all chart widgets.
 - class Background: background of a chart widget.
 - class Title: title of a chart.

Colors
------
All colors that pygtkChart uses are gtk.gdk.Colors as used by PyGTK.

Author: Sven Festersen (sven@sven-festersen.de)
"""
__docformat__ = "epytext"
import cairo
import gobject
import gtk
import os
import pango
import pangocairo
import pygtk

from pygtk_chart.chart_object import ChartObject
from pygtk_chart.basics import *
from pygtk_chart import label

COLOR_AUTO = 0
AREA_CIRCLE = 0
AREA_RECTANGLE = 1
CLICK_SENSITIVE_AREAS = []


def init_sensitive_areas():
    global CLICK_SENSITIVE_AREAS
    CLICK_SENSITIVE_AREAS = []
    
def add_sensitive_area(type, coords, data):
    global CLICK_SENSITIVE_AREAS
    CLICK_SENSITIVE_AREAS.append((type, coords, data))
    
def get_sensitive_areas(x, y):
    res = []
    global CLICK_SENSITIVE_AREAS
    for type, coords, data in CLICK_SENSITIVE_AREAS:
        if type == AREA_CIRCLE:
            ax, ay, radius = coords
            if (ax - x) ** 2 + (ay - y) ** 2 <= radius ** 2:
                res.append(data)
        elif type == AREA_RECTANGLE:
            ax, ay, width, height = coords
            if ax <= x <= ax + width and ay <= y <= ay + height:
                res.append(data)
    return res


class Chart(gtk.DrawingArea):
    """
    This is the base class for all chart widgets.
    
    Properties
    ==========
    The Chart class inherits properties from gtk.DrawingArea.
    Additional properties:
     - padding (the amount of free white space between the chart's
       content and its border in px, type: int in [0, 100].
       
    Signals
    =======
    The Chart class inherits signals from gtk.DrawingArea.
    """
    
    __gproperties__ = {"padding": (gobject.TYPE_INT, "padding",
                                    "The chart's padding.", 0, 100, 16,
                                    gobject.PARAM_READWRITE)}
    
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        #private properties:
        self._padding = 16
        #objects needed for every chart:
        self.background = Background()
        self.background.connect("appearance-changed", self._cb_appearance_changed)
        self.title = Title()
        self.title.connect("appearance-changed", self._cb_appearance_changed)
        
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.SCROLL_MASK|gtk.gdk.POINTER_MOTION_MASK)
        self.connect("expose_event", self._cb_expose_event)
        self.connect("button_press_event", self._cb_button_pressed)
        self.connect("motion-notify-event", self._cb_motion_notify)
        
    def do_get_property(self, property):
        if property.name == "padding":
            return self._padding
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def do_set_property(self, property, value):
        if property.name == "padding":
            self._padding = value
        else:
            raise AttributeError, "Property %s does not exist." % property.name
        
    def _cb_appearance_changed(self, object):
        """
        This method is called after the appearance of an object changed
        and forces a redraw.
        """
        self.queue_draw()
        
    def _cb_button_pressed(self, widget, event):
        pass
    
    def _cb_motion_notify(self, widget, event):
        pass
        
    def _cb_expose_event(self, widget, event):
        """
        This method is called when an instance of Chart receives
        the gtk expose_event.
        
        @type widget: gtk.Widget
        @param widget: The widget that received the event.
        @type event: gtk.Event
        @param event: The event.
        """
        self.context = widget.window.cairo_create()
        self.context.rectangle(event.area.x, event.area.y, \
                                event.area.width, event.area.height)
        self.context.clip()
        self.draw(self.context)
        return False
        
    def draw_basics(self, context, rect):
        """
        Draw basic things that every plot has (background, title, ...).
        
        @type context: cairo.Context
        @param context: The context to draw on.
        @type rect: gtk.gdk.Rectangle
        @param rect: A rectangle representing the charts area.
        """
        self.background.draw(context, rect)
        self.title.draw(context, rect)
        
        #calculate the rectangle that's available for drawing the chart
        title_height = self.title.get_real_dimensions()[1]
        rect_height = int(rect.height - 3 * self._padding - title_height)
        rect_width = int(rect.width - 2 * self._padding)
        rect_x = int(rect.x + self._padding)
        rect_y = int(rect.y + title_height + 2 * self._padding)
        return gtk.gdk.Rectangle(rect_x, rect_y, rect_width, rect_height)
        
    def draw(self, context):
        """
        Draw the widget. This method is called automatically. Don't call it
        yourself. If you want to force a redrawing of the widget, call
        the queue_draw() method.
        
        @type context: cairo.Context
        @param context: The context to draw on.
        """
        rect = self.get_allocation()
        rect = gtk.gdk.Rectangle(0, 0, rect.width, rect.height) #transform rect to context coordinates
        context.set_line_width(1)
        rect = self.draw_basics(context, rect)
        
    def export_svg(self, filename, size=None):
        """
        Saves the contents of the widget to svg file. The size of the image
        will be the size of the widget.
        
        @type filename: string
        @param filename: The path to the file where you want the chart to be saved.
        @type size: tuple
        @param size: Optional parameter to give the desired height and width of the image.
        """
        if size is None:
            rect = self.get_allocation()
            width = rect.width
            height = rect.height
        else:
            width, height = size
            old_alloc = self.get_allocation
            self.get_allocation = lambda: gtk.gdk.Rectangle(0, 0, width, height)
        surface = cairo.SVGSurface(filename, width, height)
        ctx = cairo.Context(surface)
        context = pangocairo.CairoContext(ctx)
        self.draw(context)
        surface.finish()
        if size is not None:
            self.get_allocation = old_alloc
        
    def export_png(self, filename, size=None):
        """
        Saves the contents of the widget to png file. The size of the image
        will be the size of the widget.
        
        @type filename: string
        @param filename: The path to the file where you want the chart to be saved.
        @type size: tuple
        @param size: Optional parameter to give the desired height and width of the image.
        """
        if size is None:
            rect = self.get_allocation()
            width = rect.width
            height = rect.height
        else:
            width, height = size
            old_alloc = self.get_allocation
            self.get_allocation = lambda: gtk.gdk.Rectangle(0, 0, width, height)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)
        context = pangocairo.CairoContext(ctx)
        self.set_size_request(width, height)
        self.draw(context)
        surface.write_to_png(filename)
        if size is not None:
            self.get_allocation = old_alloc
        
        
    def set_padding(self, padding):
        """
        Set the chart's padding.
        
        @param padding: the padding in px
        @type padding: int in [0, 100] (default: 16).
        """
        self.set_property("padding", padding)
        self.queue_draw()
        
    def get_padding(self):
        """
        Returns the chart's padding.
        
        @return: int in [0, 100].
        """
        return self.get_property("padding")
    
        
class Background(ChartObject):
    """
    The background of a chart.
    
    Properties
    ==========
    This class inherits properties from chart_object.ChartObject.
    Additional properties:
     - color (the background color, type: gtk.gdk.Color)
     - gradient (the background gradient, type: a pair of gtk.gdk.Color)
     - image (path to the background image file, type: string)
     
    Signals
    =======
    The Background class inherits signals from chart_object.ChartObject.
    """    
    
    __gproperties__ = {"color": (gobject.TYPE_PYOBJECT,
                                    "background color",
                                    "The color of the backround.",
                                    gobject.PARAM_READWRITE),
                        "gradient": (gobject.TYPE_PYOBJECT,
                                    "background gradient",
                                    "A background gardient. (first_color, second_color)",
                                    gobject.PARAM_READWRITE),
                        "image": (gobject.TYPE_STRING,
                                    "background image file",
                                    "Path to the image file to use as background.",
                                    "", gobject.PARAM_READWRITE)}
    
    def __init__(self):
        ChartObject.__init__(self)
        self._color = gtk.gdk.color_parse("#ffffff") #the backgound is filled white by default
        self._gradient = None
        self._image = ""
        self._pixbuf = None
        
    def do_get_property(self, property):
        if property.name == "visible":
            return self._show
        elif property.name == "antialias":
            return self._antialias
        elif property.name == "gradient":
            return self._gradient
        elif property.name == "color":
            return self._color
        elif property.name == "image":
            return self._image
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def do_set_property(self, property, value):
        if property.name == "visible":
            self._show = value
        elif property.name == "antialias":
            self._antialias = value
        elif property.name == "gradient":
            self._gradient = value
        elif property.name == "color":
            self._color = value
        elif property.name == "image":
            self._image = value
        else:
            raise AttributeError, "Property %s does not exist." % property.name
        
    def _do_draw(self, context, rect):
        """
        Do all the drawing stuff.
        
        @type context: cairo.Context
        @param context: The context to draw on.
        @type rect: gtk.gdk.Rectangle
        @param rect: A rectangle representing the charts area.
        """
        if self._color != None:
            #set source color
            context.set_source_rgb(*color_gdk_to_cairo(self._color))
        elif self._gradient != None:
            #set source gradient
            cs = color_gdk_to_cairo(self._gradient[0])
            ce = color_gdk_to_cairo(self._gradient[1])
            gradient = cairo.LinearGradient(0, 0, 0, rect.height)
            gradient.add_color_stop_rgb(0, cs[0], cs[1], cs[2])
            gradient.add_color_stop_rgb(1, ce[0], ce[1], ce[2])
            context.set_source(gradient)
        elif self._pixbuf:
            context.set_source_pixbuf(self._pixbuf, 0, 0)
        else:
            context.set_source_rgb(1, 1, 1) #fallback to white bg
        #create the background rectangle and fill it:
        context.rectangle(0, 0, rect.width, rect.height)
        context.fill()
        
    def set_color(self, color):
        """
        The set_color() method can be used to change the color of the
        background.
        
        @type color: gtk.gdk.Color
        @param color: Set the background to be filles with this color.
        """
        self.set_property("color", color)
        self.set_property("gradient", None)
        self.set_property("image", "")
        self.emit("appearance_changed")
        
    def get_color(self):
        """
        Returns the background's color.
        
        @return: gtk.gdk.Color.
        """
        return self.get_property("color")
        
    def set_gradient(self, color_start, color_end):
        """
        Use set_gradient() to define a vertical gradient as the background.
        
        @type color_start: gtk.gdk.Color
        @param color_start: The starting (top) color of the gradient.
        @type color_end: gtk.gdk.Color
        @param color_end: The ending (bottom) color of the gradient.
        """
        self.set_property("color", None)
        self.set_property("gradient", (color_start, color_end))
        self.set_property("image", "")
        self.emit("appearance_changed")
        
    def get_gradient(self):
        """
        Returns the gradient of the background or None.
        
        @return: A (gtk.gdk.Color, gtk.gdk.Color) tuple or None.
        """
        return self.get_property("gradient")
        
    def set_image(self, filename):
        """
        The set_image() method sets the background to be filled with an
        image.
        
        @type filename: string
        @param filename: Path to the file you want to use as background
        image. If the file does not exists, the background is set to white.
        """
        try:
            self._pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        except:
            self._pixbuf = None
        
        self.set_property("color", None)
        self.set_property("gradient", None)
        self.set_property("image", filename)
        self.emit("appearance_changed")
        
    def get_image(self):
        return self.get_property("image")
        
        
class Title(label.Label):
    """
    The title of a chart. The title will be drawn centered at the top of the
    chart.
    
    Properties
    ==========
    The Title class inherits properties from label.Label.
       
    Signals
    =======
    The Title class inherits signals from label.Label.
    """    
    
    def __init__(self, text=""):
        label.Label.__init__(self, (0, 0), text, weight=pango.WEIGHT_BOLD, anchor=label.ANCHOR_TOP_CENTER, fixed=True)
        
    def _do_draw(self, context, rect, top=-1):
        if top == -1: top = rect.height / 80
        self._size = max(8, int(rect.height / 50.0))
        self._position = rect.width / 2, top
        self._do_draw_label(context, rect)
        
        
class Area(ChartObject):
    """
    This is a base class for classes that represent areas, e.g. the
    pie_chart.PieArea class and the bar_chart.Bar class.
    
    Properties
    ==========
    The Area class inherits properties from chart_object.ChartObject.
    Additional properties:
     - name (a unique name for the area, type: string, read only)
     - value (the value of the area, type: float)
     - color (the area's color, type: gtk.gdk.Color)
     - label (a label for the area, type: string)
     - highlighted (set whether the area should be highlighted,
       type: boolean).
       
    Signals
    =======
    The Area class inherits signals from chart_object.ChartObject.
    """
    
    __gproperties__ = {"name": (gobject.TYPE_STRING, "area name",
                                "A unique name for the area.",
                                "", gobject.PARAM_READABLE),
                        "value": (gobject.TYPE_FLOAT,
                                    "value",
                                    "The value.",
                                    0.0, 9999999999.0, 0.0, gobject.PARAM_READWRITE),
                        "color": (gobject.TYPE_PYOBJECT, "area color",
                                    "The color of the area.",
                                    gobject.PARAM_READWRITE),
                        "label": (gobject.TYPE_STRING, "area label",
                                    "The label for the area.", "",
                                    gobject.PARAM_READWRITE),
                        "highlighted": (gobject.TYPE_BOOLEAN, "area is higlighted",
                                        "Set whether the area should be higlighted.",
                                        False, gobject.PARAM_READWRITE)}
    
    def __init__(self, name, value, title=""):
        ChartObject.__init__(self)
        self._name = name
        self._value = value
        self._label = title
        self._color = COLOR_AUTO
        self._highlighted = False
        
    def do_get_property(self, property):
        if property.name == "visible":
            return self._show
        elif property.name == "antialias":
            return self._antialias
        elif property.name == "name":
            return self._name
        elif property.name == "value":
            return self._value
        elif property.name == "color":
            return self._color
        elif property.name == "label":
            return self._label
        elif property.name == "highlighted":
            return self._highlighted
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def do_set_property(self, property, value):
        if property.name == "visible":
            self._show = value
        elif property.name == "antialias":
            self._antialias = value
        elif property.name == "value":
            self._value = value
        elif property.name == "color":
            self._color = value
        elif property.name == "label":
            self._label = value
        elif property.name == "highlighted":
            self._highlighted = value
        else:
            raise AttributeError, "Property %s does not exist." % property.name
            
    def set_value(self, value):
        """
        Set the value of the area.
        
        @type value: float.
        """
        self.set_property("value", value)
        self.emit("appearance_changed")
        
    def get_value(self):
        """
        Returns the current value of the area.
        
        @return: float.
        """
        return self.get_property("value")
        
    def set_color(self, color):
        """
        Set the color of the area.
        
        @type color: gtk.gdk.Color.
        """
        self.set_property("color", color)
        self.emit("appearance_changed")
        
    def get_color(self):
        """
        Returns the current color of the area or COLOR_AUTO.
        
        @return: gtk.gdk.Color or COLOR_AUTO.
        """
        return self.get_property("color")
        
    def set_label(self, label):
        """
        Set the label for the area.
        
        @param label: the new label
        @type label: string.
        """
        self.set_property("label", label)
        self.emit("appearance_changed")
        
    def get_label(self):
        """
        Returns the current label of the area.
        
        @return: string.
        """
        return self.get_property("label")
        
    def set_highlighted(self, highlighted):
        """
        Set whether the area should be highlighted.
        
        @type highlighted: boolean.
        """
        self.set_property("highlighted", highlighted)
        self.emit("appearance_changed")
        
    def get_highlighted(self):
        """
        Returns True if the area is currently highlighted.
        
        @return: boolean.
        """
        return self.get_property("highlighted")
