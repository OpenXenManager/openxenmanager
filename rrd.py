#!/usr/bin/env python
# -----------------------------------------------------------------------
# OpenXenManager
#
# Copyright (C) 2009 Alberto Gonzalez Rodriguez alberto@pesadilla.org
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------

import xml.dom.minidom
import  pygtk_chart

class XPORT:
    def __init__(self, filename):
        """
        Read file and parse head/ds
        """
        f = open(filename, "r")
        self.data= f.read()
        f.close()
        self.parse_head()
        self.parse_ds()
    def parse_head(self):
        """
        Get "rows", "step" and "columns" from rrd
        """
        self.dom = xml.dom.minidom.parseString(self.data)
        del self.data
        self.rrdinfo = {}
        for field in ["rows", "step", "columns"]:
            if self.dom.getElementsByTagName(field)[0].childNodes: 
                self.rrdinfo[field] = self.dom.getElementsByTagName(field)[0].childNodes[0].data
            else:
                self.rrdinfo[field] = 0 
    def parse_ds(self):
        """
        Get "ds" (memory, cpu0..) from rrd
        """
        ds_nodes = self.dom.getElementsByTagName("entry")
        self.rrdinfo["ds"] = {}
        self.keys = []
        for ds_node in ds_nodes:
            name = ds_node.childNodes[0].data.split(":")[3]
            if name in self.keys:
                name = "1" + name
            self.keys.append(name)
            self.rrdinfo["ds"][name] = {}
            self.rrdinfo["ds"][name]['values'] = []
            self.rrdinfo["ds"][name]['max_value'] = 0
    def get_data(self):
        """
        Function to get data array (timestamp, value) for all DS
        """
        for row in self.dom.getElementsByTagName("row"):
            i = 0
            lastupdate = row.childNodes[0].childNodes[0].data
            for values in row.childNodes[1:]:
                value = float(values.childNodes[0].data)
                if value == value and value != float('inf'):
                    self.rrdinfo["ds"][self.keys[i]]['values'].append([int(lastupdate), value])
                elif self.keys[i] == "memory_internal_free":
                    self.rrdinfo["ds"][self.keys[i]]['values'].append([int(lastupdate), 0])
                elif self.keys[i] == "memory":
                    self.rrdinfo["ds"][self.keys[i]]['values'].append([int(lastupdate), 0])

                if value != float('inf'):
                    if self.rrdinfo["ds"][self.keys[i]]['max_value'] < value:
                        self.rrdinfo["ds"][self.keys[i]]['max_value'] = value
                i = i + 1
        return self.rrdinfo["ds"]

class RRD:
    def __init__(self, filename):
        """
        Read file and parse head/ds
        """
        f = open(filename, "r")
        self.data= f.read()
        f.close()
        self.parse_head()
        self.parse_ds()

    def parse_head(self):
        """
        Get "version", "step" and "lastupdate" from rrd
        """
        self.dom = xml.dom.minidom.parseString(self.data)
        del self.data
        self.rrdinfo = {}
        for field in ["version", "step", "lastupdate"]:
            self.rrdinfo[field] = self.dom.getElementsByTagName(field)[0].childNodes[0].data

    def parse_ds(self):
        """
        Get "ds" (memory, cpu0..) from rrd
        """
        ds_nodes = self.dom.getElementsByTagName("ds")
        self.rrdinfo["ds"] = {}
        self.keys = []
        for ds_node in ds_nodes:
            if ds_node.getElementsByTagName("name"):
                name = ds_node.getElementsByTagName("name")[0].childNodes[0].data
                if name in self.keys:
                    name = "1" + name
                self.keys.append(name)
                self.rrdinfo["ds"][name] = {}
                for field in ["type", "minimal_heartbeat",  "min", "max",  "last_ds",  "value",  "unknown_sec"]:
                    self.rrdinfo["ds"][name][field] = ds_node.getElementsByTagName(field)[0].childNodes[0].data
                self.rrdinfo["ds"][name]['values'] = []
                self.rrdinfo["ds"][name]['max_value'] = 0

    def get_data(self, pdp=5):
        """
        Function to get data array (timestamp, value) for all DS, filter by pdp (seconds)
        """
        lastupdate = int(self.rrdinfo["lastupdate"])
        for rra in self.dom.getElementsByTagName("rra"):
            step = int(rra.getElementsByTagName("pdp_per_row")[0].childNodes[0].data)*int(self.rrdinfo["step"])
            if step == pdp:
                database = rra.getElementsByTagName("database")[0]
                lastupdate = int(self.rrdinfo["lastupdate"]) - (int(self.rrdinfo["lastupdate"]) % step)
                lastupdate = lastupdate - (len(database.getElementsByTagName("row")) * step)
                for row in database.getElementsByTagName("row"):
                    i = 0
                    lastupdate = lastupdate + step
                    for value in row.childNodes:
                        value = float(value.childNodes[0].data)
                        if value == value and value != float('inf'):
                            self.rrdinfo["ds"][self.keys[i]]['values'].append([int(lastupdate), value])
                        elif self.keys[i] == "memory_internal_free":
                            self.rrdinfo["ds"][self.keys[i]]['values'].append([int(lastupdate), 0])
                        elif self.keys[i] == "memory":
                            self.rrdinfo["ds"][self.keys[i]]['values'].append([int(lastupdate), 0])

                        if value != float('inf'):
                            if self.rrdinfo["ds"][self.keys[i]]['max_value'] < value:
                                self.rrdinfo["ds"][self.keys[i]]['max_value'] = value
                        i = i + 1
        return self.rrdinfo["ds"]
"""
window = gtk.Window()
window.connect("destroy", gtk.main_quit)
window.resize(500, 300)
window.set_size_request(500, 200)

chart = line_chart.LineChart()
from time import strftime, localtime
count = 0
def prueba(value):
    if strftime("%S", localtime(value)) == "00":
        return strftime("%H:%M", localtime(value))
    else:
        return ""

def hovered(chart, graph, (x, y)):
    print  strftime("%H:%M:%S", localtime(x)), y

chart.xaxis.set_show_tics(True)
chart.xaxis.set_show_label(True)
chart.xaxis.set_tic_format_function(prueba)
chart.yaxis.set_position(7)
chart.connect("datapoint-hovered", hovered)
chart.legend.set_visible(False)
chart.legend.set_position(line_chart.POSITION_BOTTOM_RIGHT)

rrd = RRD("prueba2.rrd")
rrdinfo = rrd.get_data(5)
def dump(obj):
    Internal use only
    for attr in dir(obj):
       print "obj.%s = %s" % (attr, getattr(obj, attr))

#Memory
chart.set_yrange((0, 256))
data = rrdinfo["memory"]["values"]
data2 = rrdinfo["memory_internal_free"]["values"]
for i in range(len(data)):
    data[i][1] = (data[i][1] - data2[i][1]*1024)/1024/1024
#cpu0
chart.set_yrange((0, 1.0))
#vif_0_tx
max_value = 0
for key in rrdinfo.keys():
    if key[:3] == "vif":
        data = rrdinfo[key]["values"]
        for i in range(len(data)):
            data[i][1] = data[i][1]/1024

        if rrdinfo[key]['max_value']/1024 > max_value:
            max_value = rrdinfo[key]['max_value']/1024

        graph_a = line_chart.Graph(key[4:], key[4:], data)
        dump(graph_a)
        chart.add_graph(graph_a)

chart.set_yrange((0, max_value))


scrolled = gtk.ScrolledWindow()
viewport = gtk.Viewport()
chart.set_size_request(len(data)*10, 200)
scrolled.add(viewport)
chart2 = chart
scrolled.add_with_viewport(chart)
window.add(scrolled)
window.show_all()
gtk.main()
"""
