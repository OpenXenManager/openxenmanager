#!/usr/bin/env python
#
#       text.py
#       
#       Copyright 2009 Sven Festersen <sven@sven-festersen.de>
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
Contains the Label class.

Author: Sven Festersen (sven@sven-festersen.de)
"""
import cairo
import gobject
import gtk
import math
import pango
import pygtk

from pygtk_chart import basics
from pygtk_chart.chart_object import ChartObject


ANCHOR_BOTTOM_LEFT = 0
ANCHOR_TOP_LEFT = 1
ANCHOR_TOP_RIGHT = 2
ANCHOR_BOTTOM_RIGHT = 4
ANCHOR_CENTER = 5
ANCHOR_TOP_CENTER = 6
ANCHOR_BOTTOM_CENTER = 7
ANCHOR_LEFT_CENTER = 8
ANCHOR_RIGHT_CENTER = 9

UNDERLINE_NONE = pango.UNDERLINE_NONE
UNDERLINE_SINGLE = pango.UNDERLINE_SINGLE
UNDERLINE_DOUBLE = pango.UNDERLINE_DOUBLE
UNDERLINE_LOW = pango.UNDERLINE_LOW

STYLE_NORMAL = pango.STYLE_NORMAL
STYLE_OBLIQUE = pango.STYLE_OBLIQUE
STYLE_ITALIC = pango.STYLE_ITALIC

WEIGHT_ULTRALIGHT = pango.WEIGHT_ULTRALIGHT
WEIGHT_LIGHT = pango.WEIGHT_LIGHT
WEIGHT_NORMAL = pango.WEIGHT_NORMAL
WEIGHT_BOLD = pango.WEIGHT_BOLD
WEIGHT_ULTRABOLD = pango.WEIGHT_ULTRABOLD
WEIGHT_HEAVY = pango.WEIGHT_HEAVY


DRAWING_INITIALIZED = False
REGISTERED_LABELS = []


def begin_drawing():
    global DRAWING_INITIALIZED
    DRAWING_INITIALIZED = True
    
def finish_drawing():
    global REGISTERED_LABELS
    global DRAWING_INITIALIZED
    REGISTERED_LABELS = []
    DRAWING_INITIALIZED = False
    
def register_label(label):
    if DRAWING_INITIALIZED:
        REGISTERED_LABELS.append(label)
    
def get_registered_labels():
    if DRAWING_INITIALIZED:
        return REGISTERED_LABELS
    return []


class Label(ChartObject):
    """
    This class is used for drawing all the text on the chart widgets.
    It uses the pango layout engine.
    
    Properties
    ==========
    The Label class inherits properties from chart_object.ChartObject.
    Additional properties:
     - color (the label's color, type: gtk.gdk.Color)
     - text (text to display, type: string)
     - position (the label's position, type: pair of float)
     - anchor (the anchor that should be used to position the label,
       type: an anchor constant)
     - underline (sets the type of underline, type; an underline
       constant)
     - max-width (the maximum width of the label in px, type: int)
     - rotation (angle of rotation in degrees, type: int)
     - size (the size of the label's text in px, type: int)
     - slant (the font slant, type: a slant style constant)
     - weight (the font weight, type: a font weight constant)
     - fixed (sets whether the position of the label may be changed
       dynamicly or not, type: boolean)
     - wrap (sets whether the label's text should be wrapped if it's
       longer than max-width, type: boolean).
       
    Signals
    =======
    The Label class inherits signals from chart_object.ChartObject.
    """
    
    __gproperties__ = {"color": (gobject.TYPE_PYOBJECT,
                                "label color",
                                "The color of the label (a gtk.gdkColor)",
                                gobject.PARAM_READWRITE),
                        "text": (gobject.TYPE_STRING,
                                "label text",
                                "The text to show on the label.",
                                "", gobject.PARAM_READWRITE),
                        "position": (gobject.TYPE_PYOBJECT,
                                    "label position",
                                    "A pair of x,y coordinates.",
                                    gobject.PARAM_READWRITE),
                        "anchor": (gobject.TYPE_INT, "label anchor",
                                    "The anchor of the label.", 0, 9, 0,
                                    gobject.PARAM_READWRITE),
                        "underline": (gobject.TYPE_PYOBJECT,
                                    "underline text",
                                    "Set whether to underline the text.",
                                    gobject.PARAM_READWRITE),
                        "max-width": (gobject.TYPE_INT, "maximum width",
                                        "The maximum width of the label.",
                                        1, 99999, 99999,
                                        gobject.PARAM_READWRITE),
                        "rotation": (gobject.TYPE_INT, "rotation of the label",
                                    "The angle that the label should be rotated by in degrees.",
                                    0, 360, 0, gobject.PARAM_READWRITE),
                        "size": (gobject.TYPE_INT, "text size",
                                "The size of the text.", 0, 1000, 8,
                                gobject.PARAM_READWRITE),
                        "slant": (gobject.TYPE_PYOBJECT, "font slant",
                                "The font slant style.", 
                                gobject.PARAM_READWRITE),
                        "weight": (gobject.TYPE_PYOBJECT, "font weight",
                                "The font weight.", gobject.PARAM_READWRITE),
                        "fixed": (gobject.TYPE_BOOLEAN, "fixed",
                                    "Set whether the position of the label should be forced.",
                                    False, gobject.PARAM_READWRITE),
                        "wrap": (gobject.TYPE_BOOLEAN, "wrap text",
                                    "Set whether text should be wrapped.",
                                    False, gobject.PARAM_READWRITE)}
    
    def __init__(self, position, text, size=None,
                    slant=pango.STYLE_NORMAL,
                    weight=pango.WEIGHT_NORMAL,
                    underline=pango.UNDERLINE_NONE,
                    anchor=ANCHOR_BOTTOM_LEFT, max_width=99999,
                    fixed=False):
        ChartObject.__init__(self)
        self._position = position
        self._text = text
        self._size = size
        self._slant = slant
        self._weight = weight
        self._underline = underline
        self._anchor = anchor
        self._rotation = 0
        self._color = gtk.gdk.Color()
        self._max_width = max_width
        self._fixed = fixed
        self._wrap = True
        
        self._real_dimensions = (0, 0)
        self._real_position = (0, 0)
        self._line_count = 1
        
        self._context = None
        self._layout = None
        
    def do_get_property(self, property):
        if property.name == "visible":
            return self._show
        elif property.name == "antialias":
            return self._antialias
        elif property.name == "text":
            return self._text
        elif property.name == "color":
            return self._color
        elif property.name == "position":
            return self._position
        elif property.name == "anchor":
            return self._anchor
        elif property.name == "underline":
            return self._underline
        elif property.name == "max-width":
            return self._max_width
        elif property.name == "rotation":
            return self._rotation
        elif property.name == "size":
            return self._size
        elif property.name == "slant":
            return self._slant
        elif property.name == "weight":
            return self._weight
        elif property.name == "fixed":
            return self._fixed
        elif property.name == "wrap":
            return self._wrap
        else:
            raise AttributeError, "Property %s does not exist." % property.name

    def do_set_property(self, property, value):
        if property.name == "visible":
            self._show = value
        elif property.name == "antialias":
            self._antialias = value
        elif property.name == "text":
            self._text = value
        elif property.name == "color":
            self._color = value
        elif property.name == "position":
            self._position = value
        elif property.name == "anchor":
            self._anchor = value
        elif property.name == "underline":
            self._underline = value
        elif property.name == "max-width":
            self._max_width = value
        elif property.name == "rotation":
            self._rotation = value
        elif property.name == "size":
            self._size = value
        elif property.name == "slant":
            self._slant = value
        elif property.name == "weight":
            self._weight = value
        elif property.name == "fixed":
            self._fixed = value
        elif property.name == "wrap":
            self._wrap = value
        else:
            raise AttributeError, "Property %s does not exist." % property.name
        
    def _do_draw(self, context, rect):
        self._do_draw_label(context, rect)
        
    def _do_draw_label(self, context, rect):
        angle = 2 * math.pi * self._rotation / 360.0
        
        if self._context == None:
            label = gtk.Label()
            self._context = label.create_pango_context()          
        pango_context = self._context
        
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(self._weight, 0, len(self._text)))
        attrs.insert(pango.AttrStyle(self._slant, 0, len(self._text)))
        attrs.insert(pango.AttrUnderline(self._underline, 0,
                        len(self._text)))
        if self._size != None:
            attrs.insert(pango.AttrSize(1000 * self._size, 0,
                            len(self._text)))
        
        if self._layout == None:
            self._layout = pango.Layout(pango_context)
        layout = self._layout
        layout.set_text(self._text)
        layout.set_attributes(attrs)
        
        #find out where to draw the layout and calculate the maximum width
        width = rect.width
        if self._anchor in [ANCHOR_BOTTOM_LEFT, ANCHOR_TOP_LEFT,
                            ANCHOR_LEFT_CENTER]:
            width = rect.width - self._position[0]
        elif self._anchor in [ANCHOR_BOTTOM_RIGHT, ANCHOR_TOP_RIGHT,
                                ANCHOR_RIGHT_CENTER]:
            width = self._position[0]
        
        text_width, text_height = layout.get_pixel_size()
        width = width * math.cos(angle)
        width = min(width, self._max_width)
        
        if self._wrap:
            layout.set_wrap(pango.WRAP_WORD_CHAR)
        layout.set_width(int(1000 * width))
        
        x, y = get_text_pos(layout, self._position, self._anchor, angle)
        
        if not self._fixed:
            #Find already drawn labels that would intersect with the current one
            #and adjust position to avoid intersection.
            text_width, text_height = layout.get_pixel_size()
            real_width = abs(text_width * math.cos(angle)) + abs(text_height * math.sin(angle))
            real_height = abs(text_height * math.cos(angle)) + abs(text_width * math.sin(angle))
            
            other_labels = get_registered_labels()
            this_rect = gtk.gdk.Rectangle(int(x), int(y), int(real_width), int(real_height))
            for label in other_labels:
                label_rect = label.get_allocation()
                intersection = this_rect.intersect(label_rect)
                if intersection.width == 0 and intersection.height == 0:
                    continue
                
                y_diff = 0
                if label_rect.y <= y and label_rect.y + label_rect.height >= y:
                    y_diff = y - label_rect.y + label_rect.height
                elif label_rect.y > y and label_rect.y < y + real_height:
                    y_diff = label_rect.y - real_height - y
                y += y_diff
        
        #draw layout
        context.move_to(x, y)
        context.rotate(angle)
        context.set_source_rgb(*basics.color_gdk_to_cairo(self._color))
        context.show_layout(layout)
        context.rotate(-angle)
        context.stroke()
        
        #calculate the real dimensions
        text_width, text_height = layout.get_pixel_size()
        real_width = abs(text_width * math.cos(angle)) + abs(text_height * math.sin(angle))
        real_height = abs(text_height * math.cos(angle)) + abs(text_width * math.sin(angle))
        self._real_dimensions = real_width, real_height
        self._real_position = x, y
        self._line_count = layout.get_line_count()
        
        register_label(self)
        
    def get_calculated_dimensions(self, context, rect):
        angle = 2 * math.pi * self._rotation / 360.0
        
        if self._context == None:
            label = gtk.Label()
            self._context = label.create_pango_context()          
        pango_context = self._context
        
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(self._weight, 0, len(self._text)))
        attrs.insert(pango.AttrStyle(self._slant, 0, len(self._text)))
        attrs.insert(pango.AttrUnderline(self._underline, 0,
                        len(self._text)))
        if self._size != None:
            attrs.insert(pango.AttrSize(1000 * self._size, 0,
                            len(self._text)))
        
        if self._layout == None:
            self._layout = pango.Layout(pango_context)
        layout = self._layout
            
        layout.set_text(self._text)
        layout.set_attributes(attrs)
        
        #find out where to draw the layout and calculate the maximum width
        width = rect.width
        if self._anchor in [ANCHOR_BOTTOM_LEFT, ANCHOR_TOP_LEFT,
                            ANCHOR_LEFT_CENTER]:
            width = rect.width - self._position[0]
        elif self._anchor in [ANCHOR_BOTTOM_RIGHT, ANCHOR_TOP_RIGHT,
                                ANCHOR_RIGHT_CENTER]:
            width = self._position[0]
        
        text_width, text_height = layout.get_pixel_size()
        width = width * math.cos(angle)
        width = min(width, self._max_width)
        
        if self._wrap:
            layout.set_wrap(pango.WRAP_WORD_CHAR)
        layout.set_width(int(1000 * width))
        
        x, y = get_text_pos(layout, self._position, self._anchor, angle)
        
        if not self._fixed:
            #Find already drawn labels that would intersect with the current one
            #and adjust position to avoid intersection.
            text_width, text_height = layout.get_pixel_size()
            real_width = abs(text_width * math.cos(angle)) + abs(text_height * math.sin(angle))
            real_height = abs(text_height * math.cos(angle)) + abs(text_width * math.sin(angle))
            
            other_labels = get_registered_labels()
            this_rect = gtk.gdk.Rectangle(int(x), int(y), int(real_width), int(real_height))
            for label in other_labels:
                label_rect = label.get_allocation()
                intersection = this_rect.intersect(label_rect)
                if intersection.width == 0 and intersection.height == 0:
                    continue
                
                y_diff = 0
                if label_rect.y <= y and label_rect.y + label_rect.height >= y:
                    y_diff = y - label_rect.y + label_rect.height
                elif label_rect.y > y and label_rect.y < y + real_height:
                    y_diff = label_rect.y - real_height - y
                y += y_diff
        
        #calculate the dimensions
        text_width, text_height = layout.get_pixel_size()
        real_width = abs(text_width * math.cos(angle)) + abs(text_height * math.sin(angle))
        real_height = abs(text_height * math.cos(angle)) + abs(text_width * math.sin(angle))
        return real_width, real_height
        
    def set_text(self, text):
        """
        Use this method to set the text that should be displayed by
        the label.
        
        @param text: the text to display.
        @type text: string
        """
        self.set_property("text", text)
        self.emit("appearance_changed")
        
    def get_text(self):
        """
        Returns the text currently displayed.
        
        @return: string.
        """
        return self.get_property("text")
        
    def set_color(self, color):
        """
        Set the color of the label. color has to be a gtk.gdk.Color.
        
        @param color: the color of the label
        @type color: gtk.gdk.Color.
        """
        self.set_property("color", color)
        self.emit("appearance_changed")
        
    def get_color(self):
        """
        Returns the current color of the label.
        
        @return: gtk.gdk.Color.
        """
        return self.get_property("color")
        
    def set_position(self, pos):
        """
        Set the position of the label. pos has to be a x,y pair of
        absolute pixel coordinates on the widget.
        The position is not the actual position but the position of the
        Label's anchor point (see L{set_anchor} for details).
        
        @param pos: new position of the label
        @type pos: pair of (x, y).
        """
        self.set_property("position", pos)
        self.emit("appearance_changed")
        
    def get_position(self):
        """
        Returns the current position of the label.
        
        @return: pair of (x, y).
        """
        return self.get_property("position")
        
    def set_anchor(self, anchor):
        """
        Set the anchor point of the label. The anchor point is the a
        point on the label's edge that has the position you set with
        set_position().
        anchor has to be one of the following constants:
        
         - label.ANCHOR_BOTTOM_LEFT
         - label.ANCHOR_TOP_LEFT
         - label.ANCHOR_TOP_RIGHT
         - label.ANCHOR_BOTTOM_RIGHT
         - label.ANCHOR_CENTER
         - label.ANCHOR_TOP_CENTER
         - label.ANCHOR_BOTTOM_CENTER
         - label.ANCHOR_LEFT_CENTER
         - label.ANCHOR_RIGHT_CENTER
         
        The meaning of the constants is illustrated below:::
        
        
             ANCHOR_TOP_LEFT     ANCHOR_TOP_CENTER   ANCHOR_TOP_RIGHT
                            *           *           *
                              #####################
         ANCHOR_LEFT_CENTER * #         *         # * ANCHOR_RIGHT_CENTER
                              #####################
                            *           *           *
          ANCHOR_BOTTOM_LEFT   ANCHOR_BOTTOM_CENTER  ANCHOR_BOTTOM_RIGHT
          
        The point in the center is of course referred to by constant
        label.ANCHOR_CENTER.
        
        @param anchor: the anchor point of the label
        @type anchor: one of the constants described above.
        """
        
        self.set_property("anchor", anchor)
        self.emit("appearance_changed")
        
    def get_anchor(self):
        """
        Returns the current anchor point that's used to position the
        label. See L{set_anchor} for details.
        
        @return: one of the anchor constants described in L{set_anchor}.
        """
        return self.get_property("anchor")
        
    def set_underline(self, underline):
        """
        Set the underline style of the label. underline has to be one
        of the following constants:
        
         - label.UNDERLINE_NONE: do not underline the text
         - label.UNDERLINE_SINGLE: draw a single underline (the normal
           underline method)
         - label.UNDERLINE_DOUBLE: draw a double underline
         - label.UNDERLINE_LOW; draw a single low underline.
         
        @param underline: the underline style
        @type underline: one of the constants above.
        """    
        self.set_property("underline", underline)
        self.emit("appearance_changed")
        
    def get_underline(self):
        """
        Returns the current underline style. See L{set_underline} for
        details.
        
        @return: an underline constant (see L{set_underline}).
        """
        return self.get_property("underline")
        
    def set_max_width(self, width):
        """
        Set the maximum width of the label in pixels.
        
        @param width: the maximum width
        @type width: integer.
        """
        self.set_property("max-width", width)
        self.emit("appearance_changed")
        
    def get_max_width(self):
        """
        Returns the maximum width of the label.
        
        @return: integer.
        """
        return self.get_property("max-width")
        
    def set_rotation(self, angle):
        """
        Use this method to set the rotation of the label in degrees.
        
        @param angle: the rotation angle
        @type angle: integer in [0, 360].
        """
        self.set_property("rotation", angle)
        self.emit("appearance_changed")
        
    def get_rotation(self):
        """
        Returns the current rotation angle.
        
        @return: integer in [0, 360].
        """
        return self.get_property("rotation")
        
    def set_size(self, size):
        """
        Set the size of the text in pixels.
        
        @param size: size of the text
        @type size: integer.
        """
        self.set_property("size", size)
        self.emit("appearance_changed")
        
    def get_size(self):
        """
        Returns the current size of the text in pixels.
        
        @return: integer.
        """
        return self.get_property("size")
        
    def set_slant(self, slant):
        """
        Set the font slant. slat has to be one of the following:
        
         - label.STYLE_NORMAL
         - label.STYLE_OBLIQUE
         - label.STYLE_ITALIC
         
        @param slant: the font slant style
        @type slant: one of the constants above.
        """
        self.set_property("slant", slant)
        self.emit("appearance_changed")
        
    def get_slant(self):
        """
        Returns the current font slant style. See L{set_slant} for
        details.
        
        @return: a slant style constant.
        """
        return self.get_property("slant")
        
    def set_weight(self, weight):
        """
        Set the font weight. weight has to be one of the following:
        
         - label.WEIGHT_ULTRALIGHT
         - label.WEIGHT_LIGHT
         - label.WEIGHT_NORMAL
         - label.WEIGHT_BOLD
         - label.WEIGHT_ULTRABOLD
         - label.WEIGHT_HEAVY
         
        @param weight: the font weight
        @type weight: one of the constants above.
        """
        self.set_property("weight", weight)
        self.emit("appearance_changed")
        
    def get_weight(self):
        """
        Returns the current font weight. See L{set_weight} for details.
        
        @return: a font weight constant.
        """
        return self.get_property("weight")
        
    def set_fixed(self, fixed):
        """
        Set whether the position of the label should be forced
        (fixed=True) or if it should be positioned avoiding intersection
        with other labels.
        
        @type fixed: boolean.
        """
        self.set_property("fixed", fixed)
        self.emit("appearance_changed")
        
    def get_fixed(self):
        """
        Returns True if the label's position is forced.
        
        @return: boolean
        """
        return self.get_property("fixed")
        
    def set_wrap(self, wrap):
        """
        Set whether too long text should be wrapped.
        
        @type wrap: boolean.
        """
        self.set_property("wrap", wrap)
        self.emit("appearance_changed")
        
    def get_wrap(self):
        """
        Returns True if too long text should be wrapped.
        
        @return: boolean.
        """
        return self.get_property("wrap")
        
    def get_real_dimensions(self):
        """
        This method returns a pair (width, height) with the dimensions
        the label was drawn with. Call this method I{after} drawing
        the label.
        
        @return: a (width, height) pair.
        """
        return self._real_dimensions
        
    def get_real_position(self):
        """
        Returns the position of the label where it was really drawn.
        
        @return: a (x, y) pair.
        """
        return self._real_position
        
    def get_allocation(self):
        """
        Returns an allocation rectangle.
        
        @return: gtk.gdk.Rectangle.
        """
        x, y = self._real_position
        w, h = self._real_dimensions
        return gtk.gdk.Rectangle(int(x), int(y), int(w), int(h))
        
    def get_line_count(self):
        """
        Returns the number of lines.
        
        @return: int.
        """
        return self._line_count
    
        
def get_text_pos(layout, pos, anchor, angle):
    """
    This function calculates the position of bottom left point of the
    layout respecting the given anchor point.
    
    @return: (x, y) pair
    """
    text_width_n, text_height_n = layout.get_pixel_size()
    text_width = text_width_n * abs(math.cos(angle)) + text_height_n * abs(math.sin(angle))
    text_height = text_height_n * abs(math.cos(angle)) + text_width_n * abs(math.sin(angle))
    height_delta = text_height - text_height_n
    x, y = pos
    ref = (0, -text_height)
    if anchor == ANCHOR_TOP_LEFT:
        ref = (0, 0)
    elif anchor == ANCHOR_TOP_RIGHT:
        ref = (-text_width, height_delta)
    elif anchor == ANCHOR_BOTTOM_RIGHT:
        ref = (-text_width, -text_height)
    elif anchor == ANCHOR_CENTER:
        ref = (-text_width / 2, -text_height / 2)
    elif anchor == ANCHOR_TOP_CENTER:
        ref = (-text_width / 2, 0)
    elif anchor == ANCHOR_BOTTOM_CENTER:
        ref = (-text_width / 2, -text_height)
    elif anchor == ANCHOR_LEFT_CENTER:
        ref = (0, -text_height / 2)
    elif anchor == ANCHOR_RIGHT_CENTER:
        ref = (-text_width, -text_height / 2)
    x += ref[0]
    y += ref[1]
    return x, y
