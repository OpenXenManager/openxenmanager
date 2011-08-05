# http://www.daa.com.au/pipermail/pygtk/2004-September/008685.html

#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gobject

PAD = 3

class PixbufTextCellRenderer(gtk.GenericCellRenderer):

    __gproperties__ = {
        "pixbuf": (gobject.TYPE_PYOBJECT, "Pixbuf", 
                    "Pixbuf image", gobject.PARAM_READWRITE),
        "text": (gobject.TYPE_STRING, "Text", "Text string", None,
                 gobject.PARAM_READWRITE),
        'background': (gtk.gdk.Color, 'Background', 'The background color', gobject.PARAM_READWRITE)
    }
                     
    def __init__(self):
        self.__gobject_init__()
        self.prend = gtk.CellRendererPixbuf()
        self.trend = gtk.CellRendererText()
        self.percent = 0

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def update_properties(self):
        self.trend.set_property('text', self.get_property('text'))
        self.prend.set_property('pixbuf', self.get_property('pixbuf'))
        self.prend.set_property('cell-background-gdk', self.get_property('background'))
        return

    def on_render(self, window, widget, background_area,
                  cell_area, expose_area, flags):
        self.update_properties()
        ypad = self.get_property('ypad')
        px, py, pw, ph = self.prend.get_size(widget, cell_area)
        px += cell_area.x
        prect = (px, cell_area.y, pw, ph)
        tx, ty, tw, th = self.trend.get_size(widget, cell_area)
        tx = cell_area.x + (cell_area.width - tw) / 2
        ty = cell_area.y + ph + PAD
        trect = (tx, ty, tw, th)
        self.prend.render(window, widget, background_area, prect,
                          expose_area, flags)
        self.trend.render(window, widget, background_area, trect,
                          expose_area, flags)
        return

    def on_get_size(self, widget, cell_area):
        self.update_properties()
        xpad = self.get_property("xpad")
        ypad = self.get_property("ypad")
        xoff, yoff, width, height = self.trend.get_size(widget, cell_area)
        pxoff, pyoff, pwidth, pheight = self.prend.get_size(widget, cell_area)
        height += pheight + PAD + ypad
        width = max(width, pwidth) + xpad * 2
        return xoff, yoff, width, height

gobject.type_register(PixbufTextCellRenderer)

if __name__ == "__main__":
    w = gtk.Window()
    ls = gtk.ListStore(str, object)
    tv = gtk.TreeView(ls)
    pbtcell = PixbufTextCellRenderer()
    pbtcell.set_property('xpad', 5)
    pbtcell.set_property('ypad', 3)
    tvc = gtk.TreeViewColumn('Icons', pbtcell, text=0, pixbuf=1, background=2)
    tv.append_column(tvc)
    w.add(tv)
    ls.append(['Error',
               gtk.gdk.pixbuf_new_from_file('usagebar_1.png')])
    ls.append(['Warning',
               gtk.gdk.pixbuf_new_from_file('usagebar_2.png')])
    ls.append(['Info',
               gtk.gdk.pixbuf_new_from_file('usagebar_3.png')])
    ls.append(['Question',
               gtk.gdk.pixbuf_new_from_file('usagebar_4.png')])
    w.show_all()
    gtk.main()

