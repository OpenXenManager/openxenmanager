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
#!/usr/bin/env python
import os
import gtk
from threading import Thread
import time
class oxcWindowVMPerformance:
    """
    Class to manage "performance" of a VM/host
    """
    vport = None
    prevmousex = 0
    prevmousey = 0
    toggling = False
    graphtime = 0
    def on_btgraph_clicked(self, widget, data=None):
        """
        Update period time
        """
        times = {
                "btgraphtenmin" : 5,
                "btgraphtwohours" : 60,
                "btgraphoneweek" : 3600, 
                "btgraphoneyear" : 86400 
        }
        host = self.selected_host
        ref = self.selected_ref
        if self.selected_type == "vm":
            self.builder.get_object("scrolledwindow50").show()
            self.builder.get_object("labeldiskusage").show()
            Thread(target=self.xc_servers[host].update_performance, args=(self.selected_uuid, ref, \
                                     self.selected_ip, False, times[gtk.Buildable.get_name(widget)])).start()
        else:
            self.builder.get_object("scrolledwindow50").hide()
            self.builder.get_object("labeldiskusage").hide()
            Thread(target=self.xc_servers[host].update_performance, args=(self.selected_uuid, ref, \
                                     self.selected_ip, True, times[gtk.Buildable.get_name(widget)])).start()


    def on_viewportperf_button_press_event(self, widget, event):	
        """
        Function called when you press on image
        """
        self.vport = widget
        if event.button == 1:
            # Set cursor and set actual X/Y
            widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.FLEUR))
            self.prevmousex = event.x_root
            self.prevmousey = event.y_root

    def on_viewportperf_button_release_event(self, widget, event):
        """
        Function called on release mouse 
        """
        self.vport = None
        if event.button == 1:
            # Disable cursor
            widget.window.set_cursor(None)

    def on_viewportperf_motion_notify_event(self, widget, event):
        """
        Function called on mouse move
        """
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            state = event.state
        x, y = event.x_root, event.y_root
        if state & gtk.gdk.BUTTON1_MASK:
            offset_x = self.prevmousex - x
            offset_y = self.prevmousey - y
            self.move_image(offset_x, offset_y)
        self.prevmousex = x
        self.prevmousey = y

    def move_image(self, offset_x, offset_y):
        """
        Move image
        """
        vport = self.vport
        xadjust = vport.props.hadjustment
        newx = xadjust.value + offset_x
        yadjust = vport.props.vadjustment
        newy = yadjust.value + offset_y
        if (newx >= xadjust.lower) and \
               (newx <= (xadjust.upper - xadjust.page_size)):
            xadjust.value = newx
            vport.set_hadjustment(xadjust)
        if (newy >= yadjust.lower) and \
               (newy <= (yadjust.upper - yadjust.page_size)):
            yadjust.value = newy
            vport.set_vadjustment(yadjust)

