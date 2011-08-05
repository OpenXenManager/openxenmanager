#!/usr/bin/env python
#
#       __init__.py
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
This package contains four pygtk widgets for drawing simple charts:
 - line_chart.LineChart for line charts,
 - pie_chart.PieChart for pie charts,
 - bar_chart.BarChart for bar charts,
 - bar_chart.MultiBarChart for charts with groups of bars.
"""
__docformat__ = "epytext"

__version__ = "beta"
__author__ = "Sven Festersen, John Dickinson"
__license__ = "GPL"
__url__ = "http://notmyname.github.com/pygtkChart/"

import os
from pygtk_chart.basics import gdk_color_list_from_file
COLOR_AUTO = 0
COLORS = gdk_color_list_from_file(os.sep.join([os.path.dirname(__file__), "data", "tango.color"]))

#line style
LINE_STYLE_SOLID = 0
LINE_STYLE_DOTTED = 1
LINE_STYLE_DASHED = 2
LINE_STYLE_DASHED_ASYMMETRIC = 3

#point styles
POINT_STYLE_CIRCLE = 0
POINT_STYLE_SQUARE = 1
POINT_STYLE_CROSS = 2
POINT_STYLE_TRIANGLE_UP = 3
POINT_STYLE_TRIANGLE_DOWN = 4
POINT_STYLE_DIAMOND = 5

