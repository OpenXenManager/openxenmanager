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
import sys
# Add paths for compatibility (centos, debian lenny..)
sys.path.append("/usr/local/lib/python2.5/site-packages/")
sys.path.append("gtk-2.0/")
sys.path.append("/usr/local/lib/python2.5/site-packages/gtk-2.0/")
import os
if os.path.dirname(sys.argv[0]): 
    os.chdir(os.path.dirname(sys.argv[0]))
import pygtk
# On next releases we will use gettext for translations
APP = 'oxc'
DIR = 'locale'
if sys.platform != "win32" and sys.platform != "darwin":
    # If sys.platform is linux or unix
    """
    if not os.path.exists("oxcgtkvnc.so"):
        if platform.architecture()[0] == "32bit":
            shutil.copy("32/oxcgtkvnc.so", "oxcgtkvnc.so")
            shutil.copy("32/liboxcgtk-vnc-1.0.so.0", "liboxcgtk-vnc-1.0.so.0")
        if platform.architecture()[0] == "64bit":
            shutil.copy("64/oxcgtkvnc.so", "oxcgtkvnc.so")
            shutil.copy("64/liboxcgtk-vnc-1.0.so.0", "liboxcgtk-vnc-1.0.so.0")
    """
    import gtkvnc
    # Only needed for translations
    import gtk.glade
    gtk.glade.bindtextdomain(APP, DIR)
elif sys.platform == "darwin":
    # On MacOSX with macports sys.platform is "darwin", we need Popen for run tightvnc
    from subprocess import Popen
else:
    # On Windows we need right tightvnc and we need win32 libraries for move the window
    from subprocess import Popen
    import win32gui
    import win32con
import gtk
import gobject
# For md5 and xtea
import hashlib, xtea
from oxcSERVER import *
from pprint import pprint
import signal
import atexit
import re
# For a TreeView Cell with image+text
from PixbufTextCellRenderer import PixbufTextCellRenderer
#import locale
import gettext
gettext.install('oxc', localedir="./locale")
if sys.platform != "win32":
    # On unix is recommended run threads from gtk.gdk
    gtk.gdk.threads_init()
else:
    # On windows is needed run gobject threads
    gobject.threads_init()

# Splitted classes for oxcWindow
from window_vm import * 
from window_host import * 
from window_properties import * 
from window_storage import * 
from window_alerts import * 
from window_addserver import * 
from window_newvm import * 
from window_menuitem import * 
from window_tools import * 
import xdot

class MyDotWindow(xdot.DotWindow):

    def __init__(self, window, liststore, treestore):
        self.liststore = liststore
        self.treestore = treestore
        xdot.DotWindow.__init__(self, window)
        self.widget.connect('button_press_event', self.on_double_clicked)

    def on_double_clicked(self, widget, event):
        # On doublie click go to element
        if event.type == gtk.gdk._2BUTTON_PRESS: 
            x, y = int(event.x), int(event.y)
            if widget.get_url(x, y):
                url =  widget.get_url(x, y).url
                # Search ref and go to 
                self.liststore.foreach(self.search_ref, url)
        return True
    def search_ref(self, model, path, iter_ref, user_data):
        if self.liststore.get_value(iter_ref, 6) == user_data:
            self.treestore.get_selection().select_path(path)
            event = gtk.gdk.Event(gtk.gdk.BUTTON_RELEASE)
            event.x = float(-10)
            event.y = float(-10)
            self.treestore.emit("button_press_event", event)
        

class oxcWindow(oxcWindowVM,oxcWindowHost,oxcWindowProperties,oxcWindowStorage,oxcWindowAlerts,oxcWindowAddServer,oxcWindowNewVm,oxcWindowMenuItem,oxcWindowTools):
    """Main class to oxc window"""
    xc_servers = {}
    # When you select a element of left tree these variables are filled
    selected_actions = None
    selected_ref = None
    selected_iter= None 
    selected_tab = None
    selected_host = None
    selected_type = None
    selected_widget = None
    selected_state = None

    noclosevnc = False
    # If "Use master password" is enabled, password typed is set on it
    password = None
    reattach_storage = False
    # For New VM
    newvmdata = {}

    # On Host -> On general tab: "VMs" label hasn't a fixed width
    # If host is included on "moved" variable then "VMs" label was moved
    moved = []

    # Flag variable to avoid select signals
    set_active = False
    
    # Flag variable to export snapshot
    export_snap = False
    export_snap_vm = False

    # For windows only
    hWnd = 0

    # Used only for plugins.. 
    delete_pages = []

    # Used for pool join force
    last_host_pool = None

    # For XTEA only (needs a string with 8 characters)
    iv = "OXCENTER"

    # Tunnel VNC
    tunnel = None

    # For know if performance images was set
    performance_updated = False
    def __init__(self):
        atexit.register(self.signal_handler)
        signal.signal(15, self.signal_handler)
        # Read the configuration from oxc.conf file
        if sys.platform != "win32":
            if not os.path.exists(os.path.join(os.path.expanduser("~"), ".config")):
                os.mkdir(os.path.join(os.path.expanduser("~"), ".config"))
            if not os.path.exists(os.path.join(os.path.expanduser("~"), ".config", "openxenmanager")):
                os.mkdir(os.path.join(os.path.expanduser("~"), ".config", "openxenmanager"))
            dirconfig =  os.path.join(os.path.expanduser("~"), ".config", "openxenmanager")
            pathconfig =  os.path.join(os.path.expanduser("~"), ".config", "openxenmanager", "oxc.conf")
        else: 
            if not os.path.exists(os.path.join(os.path.expanduser("~"), "openxenmanager")):
                os.mkdir(os.path.join(os.path.expanduser("~"), "openxenmanager"))
            dirconfig =  os.path.join(os.path.expanduser("~"), "openxenmanager")
            pathconfig =  os.path.join(os.path.expanduser("~"), "openxenmanager", "oxc.conf")

        if not os.path.exists(pathconfig):
            shutil.copy("oxc.conf", pathconfig)
            
        self.config = ConfigObj(pathconfig) 
        self.pathconfig = dirconfig 
        # Read from configuration saved servers
        if self.config['servers']['hosts']:
            self.config_hosts = self.config['servers']['hosts']
        else:
            self.config_hosts = {}
        # Define the glade file
        self.gladefile = "oxc.glade"
        self.builder = gtk.Builder() 
        self.builder.set_translation_domain("oxc")
        # Add the file to gtk.Builder object
        self.builder.add_from_file(self.gladefile)


        # Connect Windows and Dialog to delete-event (we want not destroy dialog/window)
        # delete-event is called when you close the window with "x" button
        for widget in self.builder.get_objects():
            if type(widget) == type(gtk.Dialog()):
                widget.connect("delete-event", self.on_delete_event)
            if type(widget) == type(gtk.Window()):
                if gtk.Buildable.get_name(widget) != "window1":
                    widget.connect("delete-event", self.on_delete_event)
        # Frequent objects
        self.txttreefilter = self.builder.get_object("txttreefilter")

        self.listphydvd = self.builder.get_object("listphydvd")
        self.listisoimage = self.builder.get_object("listisoimage")
        self.listnetworks = self.builder.get_object("listnewvmnetworks")
        self.listnetworkcolumn = self.builder.get_object("listnewvmnetworkcolumn")
        self.window = self.builder.get_object("window1")
        self.listalerts = self.builder.get_object("listalerts")
        self.treealerts = self.builder.get_object("treealerts")
        self.filesave = self.builder.get_object("filesave")
        self.fileopen = self.builder.get_object("fileopen")
        self.newvm = self.builder.get_object("window_newvm")

        self.treeview = self.builder.get_object("treevm")
        self.treeprop = self.builder.get_object("treeprop")
        self.listprop = self.builder.get_object("listprop")
        self.statusbar = self.builder.get_object("statusbar1")
        self.treesearch = self.builder.get_object("treesearch")
        """
        for i in range(0,7):
            if self.newvm.get_nth_page(i):
                self.newvm.set_page_complete(self.newvm.get_nth_page(i), True)
        """

        # Combo's style
        style = gtk.rc_parse_string('''
                style "my-style" { GtkComboBox::appears-as-list = 1 }
                widget "*" style "my-style"
        ''')
        # Set a default font 
        self.window.get_settings().set_string_property('gtk-font-name', 'sans normal 8','');

        self.builder.connect_signals(self)

        # Create a new TreeStore
        self.treestore = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, str, str, str, str, str, str)
                                           # Image,Name, uuid, type, state, host, ref, actions, ip
        # Append default logo on created TreeStore
        self.treeroot = self.treestore.append(None, ([gtk.gdk.pixbuf_new_from_file("images/xen.gif"), "OpenXenManager", None, "home", "home", None, None, ["addserver","connectall","disconnectall"], None]))
        
        # Model Filter is used but show/hide templates/custom templates/local storage..
        self.modelfilter = self.treestore.filter_new()
        # Define the function to check if a element should be showed or not
        self.modelfilter.set_visible_func(self.visible_func)
        self.treeview.set_model(self.modelfilter) 
        
        self.modelfiltertpl = self.builder.get_object("listtemplates").filter_new()
        self.builder.get_object("treetemplates").set_model(self.modelfiltertpl)
        self.modelfiltertpl.set_visible_func(self.visible_func_templates)


        self.builder.get_object("networkcolumn1").set_property("model", self.builder.get_object("listimportnetworkcolumn"))
        self.builder.get_object("cellrenderercombo1").set_property("model", self.builder.get_object("listnewvmnetworkcolumn"))
        # Same for properties treestore
        self.propmodelfilter = self.listprop.filter_new()
        self.propmodelfilter.set_visible_func(self.prop_visible_func)
        self.treeprop.set_model(self.propmodelfilter) 

        # Fill defaults selection variables
        self.selected_name  = "OpenXenManager"
        self.selected_type  = "home"
        self.selected_uuid = ""
        self.headimage = self.builder.get_object("headimage")
        self.headlabel = self.builder.get_object("headlabel")
        self.headlabel.set_label(self.selected_name)
        self.headimage.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file("images/xen.gif"))

        if "show_hidden_vms" not in self.config["gui"]:
            self.config["gui"]["show_hidden_vms"] = "False"
            self.config.write()
        # Set menuitem checks to value from configuration
        self.builder.get_object("checkshowxstpls").set_active(self.config["gui"]["show_xs_templates"] == "True")
        self.builder.get_object("checkshowcustomtpls").set_active(self.config["gui"]["show_custom_templates"] == "True")
        self.builder.get_object("checkshowlocalstorage").set_active(self.config["gui"]["show_local_storage"] == "True")
        self.builder.get_object("checkshowtoolbar").set_active(self.config["gui"]["show_toolbar"] == "True")
        self.builder.get_object("checksetsyle").set_active(self.config["gui"]["set_style"] == "True")
        self.builder.get_object("checkshowhiddenvms").set_active(self.config["gui"]["show_hidden_vms"] == "True")

        if "maps" in self.config:
            for check in self.config["maps"]:
                self.builder.get_object(check).set_active(self.config["maps"][check] == "True")

        # If "Show toolbar" is checked then show, else hide
        if self.config["gui"]["show_toolbar"] != "False":
            self.builder.get_object("toolbar").show()
        else:
            self.builder.get_object("toolbar").hide()

        # Add to left tree the saved servers from configuration
        for host in self.config_hosts.keys():
            self.builder.get_object("listaddserverhosts").append([host])
            self.treestore.append(self.treeroot, ([gtk.gdk.pixbuf_new_from_file("images/tree_disconnected_16.png"), host, None, "server", "Disconnected", None, None, ["connect", "forgetpw", "remove"], None]))

        # Expand left tree and update menubar, tabs and toolbar
        self.treeview.expand_all()
        self.update_menubar() 
        self.update_tabs() 
        self.update_toolbar()

        # Create a TreeStore for SERVER->Search tab 
        self.listsearch = gtk.TreeStore(gtk.gdk.Pixbuf, str, object, str, object, str, str, str, str, str, gtk.gdk.Color)
        self.treesearch.set_model(self.listsearch)
        #self.treesearch.get_column(0).set_cell_data_func(self.func_cell_data_treesearch, self.treesearch.get_cell(0))

        # Add two columns with image/text from PixBufTextCellRenderer class
        pbtcell = PixbufTextCellRenderer()
        pbtcell.set_property('xpad', 15)
        pbtcell.set_property('ypad', 13)
        tvc = gtk.TreeViewColumn('CPU Usage', pbtcell, text=3, pixbuf=2, background=10)
        tvc.set_widget(self.builder.get_object("lbltreesearch6"))
        self.builder.get_object("lbltreesearch6").show()
        tvc.set_reorderable(True)
        tvc.set_sort_column_id(3)
        self.treesearch.insert_column(tvc, 1)
        pbtcell = PixbufTextCellRenderer()
        pbtcell.set_property('xpad', 15)
        pbtcell.set_property('ypad', 13)
        tvc = gtk.TreeViewColumn('Used memory', pbtcell, text=5, pixbuf=4, background=10)
        tvc.set_widget(self.builder.get_object("lbltreesearch7"))
        tvc.set_reorderable(True)
        tvc.set_sort_column_id(5)
        self.treesearch.insert_column(tvc, 2)

        # ComboBox created from GLADE needs a cellrenderertext 
        # and an attribute defining the column to show
        combobox = self.builder.get_object("radiobutton2_data")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)  
        combobox.set_model(self.listphydvd)

        combobox = self.builder.get_object("radiobutton3_data")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)  
        combobox.add_attribute(cell, 'rise', 2)  
        combobox.add_attribute(cell, 'sensitive', 3)  
        combobox.set_model(self.listisoimage)

        combobox = self.builder.get_object("treeeditnetwork")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)  
        combobox.set_model(self.builder.get_object("listeditnetwork"))

        combobox = self.builder.get_object("treeaddnetwork")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)  
        combobox.set_model(self.builder.get_object("listaddnetwork"))
        combobox.set_active(0)

        combobox = self.builder.get_object("combostgmode")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)  
        combobox.set_model(self.builder.get_object("liststgmode"))
        combobox.set_active(0)

        combobox = self.builder.get_object("combostgposition")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)  
        combobox.set_model(self.builder.get_object("liststgposition"))
        combobox.set_active(0) 
        combobox.set_style(style)

        combobox = self.builder.get_object("combomgmtnetworks")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)  
        combobox.set_model(self.builder.get_object("listmgmtnetworks"))
        combobox.set_active(0) 
        combobox.set_style(style)

        combobox = self.builder.get_object("combopoolmaster")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)  
        combobox.set_model(self.builder.get_object("listpoolmaster"))
        combobox.set_active(0) 
        combobox.set_style(style)

        combobox = self.builder.get_object("combotargetiqn")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)  
        combobox.set_model(self.builder.get_object("listtargetiqn"))
        combobox.set_active(0) 
        combobox.set_style(style)

        combobox = self.builder.get_object("combotargetlun")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)  
        combobox.set_model(self.builder.get_object("listtargetlun"))
        combobox.set_active(0) 
        combobox.set_style(style)

        combobox = self.builder.get_object("combonetworknic")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)  
        combobox.set_model(self.builder.get_object("listnetworknic"))
        combobox.set_active(0) 
        combobox.set_style(style)

        combobox = self.builder.get_object("combocustomfields")
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)  
        combobox.set_model(self.builder.get_object("listcombocustomfields"))
        combobox.set_active(0) 
        combobox.set_style(style)

        #print combobox.get_internal_child()
        # If gtk version is 2.18.0 or higher then add "marks" to scale
        if hasattr(self.builder.get_object("scalepropvmprio"), "add_mark"):
            self.builder.get_object("scalepropvmprio").add_mark(0, gtk.POS_BOTTOM, "\nLowest")
            self.builder.get_object("scalepropvmprio").add_mark(1, gtk.POS_BOTTOM, "")
            self.builder.get_object("scalepropvmprio").add_mark(2, gtk.POS_BOTTOM, "")
            self.builder.get_object("scalepropvmprio").add_mark(3, gtk.POS_BOTTOM, "")
            self.builder.get_object("scalepropvmprio").add_mark(4, gtk.POS_BOTTOM, "\nNormal")
            self.builder.get_object("scalepropvmprio").add_mark(5, gtk.POS_BOTTOM, "")
            self.builder.get_object("scalepropvmprio").add_mark(6, gtk.POS_BOTTOM, "")
            self.builder.get_object("scalepropvmprio").add_mark(7, gtk.POS_BOTTOM, "")
            self.builder.get_object("scalepropvmprio").add_mark(8, gtk.POS_BOTTOM, "\nHighest")

        # Set default colors
        self.set_style_colors()
        # Manual function to set the default buttons on dialogs/window 
        # Default buttons could be pressed with enter without need do click
        self.set_window_defaults()
        
        # If we need a master password for connect to servers without password:
        # Show the dialog asking master password
        if str(self.config["gui"]["save_password"]) == "True":
            self.builder.get_object("masterpassword").show()


        self.windowmap = MyDotWindow(self.builder.get_object("viewportmap"), self.treestore, self.treeview)

    def adjust_scrollbar_performance(self):
        for widget in ["scrolledwindow47", "scrolledwindow48", "scrolledwindow49", "scrolledwindow50"]:
            self.builder.get_object(widget).grab_focus()
            adj = self.builder.get_object(widget).get_hadjustment()
            adj.set_value(adj.upper - adj.page_size)
            

    def func_cell_data_treesearch(self, column, cell, model, iter_ref, user_data):
        # Test function don't used
        print column, cell, model, iter_ref, user_data

    def set_window_defaults(self):
        """
        Function to define what button is the default for each window/dialog
        Default button could be pressed with enter key
        """
        widgets = ["addserverpassword","addserverusername","snaptplname", "snapshotname", "vmaddnewdisk_name",
                   "txtcopyvmname", "txtpropvmname", "txtnetworkname",  "txtmasterpassword", "txtaskmasterpassword"
                   ]

        dialogs = {
            "addserver" : "connectAddServer",
            "newvmdisk" : "acceptnewvmdisk",
            "vmaddnewdisk" : "acceptvmaddnewdisk",
            "dialogsnapshotname" : "btacceptsnapshotname",
            "dialogsnaptplname" : "btacceptsnaptplname",
            "dialogsnapshotdelete" : "btacceptsnapshotdelete",
            "vmattachdisk": "btacceptattachdisk",
            "dialogdeletevm" : "dialogdelete_accept",
            "dialogdeletevdi" : "dialogdeletevdi_accept",
            "windowcopyvm" : "windowcopyvm_copy",
            "dialogvmprop" : "btvmpropaccept",
            "dialogdeletehostnetwork" : "acceptdialogdeletehostnetwork",
            "dialogdeletehostnic" : "acceptdialogdeletehostnic",
            "addbond" : "btacceptaddbond",
            "newnetwork" : "acceptnewnetwork",
            "dialogoptions" : "acceptdialogoptions",
            "masterpassword" : "acceptmasterpassword",
            "dialogeditnetwork" : "accepteditnetwork",
            "dialognetworkrestart" : "acceptdialognetworkrestart",
            "vmimport" : "nextvmimport",
            "mgmtinterface" : "acceptmgmtinterface",
            "newpool" : "acceptnewpool"
        }
        # For each dialog
        for wid in dialogs:
            # Set the flag indicating the widget could be a default button
            self.builder.get_object(dialogs[wid]).set_flags(gtk.CAN_DEFAULT)
            # If widget is a dialog
            if type(self.builder.get_object(wid)) == type(gtk.Dialog()):
                # Set the button with "id response = 1" as default
                self.builder.get_object(wid).set_default_response(1)
            else:
                # If is a Gtk.Window set the indicated button as default
                self.builder.get_object(wid).set_default(self.builder.get_object(dialogs[wid]))

        for wid in widgets:
            # For each button indicate that it may be the default button
            self.builder.get_object(wid).set_activates_default(True)
    def set_style_colors(self):
        """
        Function to set the colors for all widgets on application
        If OXC style is checked use defined colors
        Else we will use GTK colors
        """
        # If we use the OXC style... define the colors
        if str(self.config["gui"]["set_style"]) == "True":
            blue = gtk.gdk.color_parse("#d5e5f7")
            white = gtk.gdk.color_parse("white")
            header = gtk.gdk.color_parse("#e1edfb")
            green = gtk.gdk.color_parse("#577B53")
        else:
            # If you prefer GTK colors... se colors to None
            header = None
            blue = None
            white = None 
            green = None
        for i in range(1,3):
            self.builder.get_object("newvmframe" + str(i)).modify_bg(gtk.STATE_NORMAL, white)
        self.builder.get_object("window_newvm").modify_bg(gtk.STATE_NORMAL, blue)

        for i in range(1,26):
            if self.builder.get_object("eventbox" + str(i)):
                self.builder.get_object("eventbox" + str(i)).modify_bg(gtk.STATE_NORMAL, white)
        self.builder.get_object("treebootorder").set_border_width(50)

        self.builder.get_object("framehome").modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        self.builder.get_object("treebootorder").modify_bg(gtk.STATE_INSENSITIVE, blue)
        self.builder.get_object("treebootorder").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("treebootorder").modify_bg(gtk.STATE_ACTIVE, blue)
        self.builder.get_object("treebootorder").modify_bg(gtk.STATE_PRELIGHT, blue)
        self.builder.get_object("treebootorder").modify_bg(gtk.STATE_SELECTED, blue)
        self.builder.get_object("treebootorder").modify_bg(gtk.STATE_INSENSITIVE, blue)
        for widget in ["eventbox26", "eventbox26", "eventbox27", "eventbox28",
                       "eventbox29", "dialogaddnetwork", "eventbox30",
                       "dialogeditnetwork", "eventbox31", "dialognetworkrestart",
                       "dialogdeletehostnic", "dialogdeletehostnetwork", "eventbox32",
                       "dialogdeletedisk", "dialogdeletevdi", "dialogremovenetwork",
                       "dialogsnapshotname", "vmaddnewdisk", "windowcopyvm",
                       "forcejoinpool", "windowalerts", "migratetool", "fileoutputxva",
                       "statusreport", "dialogrevert"
                       ]:
            self.builder.get_object(widget).modify_bg(gtk.STATE_NORMAL, blue)
        for i in range(33,40):
            if self.builder.get_object("eventbox" + str(i)):
                self.builder.get_object("eventbox" + str(i)).modify_bg(gtk.STATE_NORMAL, white)
        self.builder.get_object("vmimport").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("filechooserimportvm").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("eventbox37").modify_bg(gtk.STATE_NORMAL, blue)
        for i in range(0,5):
            self.builder.get_object("eventimport" + str(i)).modify_bg(gtk.STATE_NORMAL, white)
        for i in range(0,2):
            self.builder.get_object("eventnewstg" + str(i)).modify_bg(gtk.STATE_NORMAL, white)
        for i in range(40,50):
            self.builder.get_object("eventbox" + str(i)).modify_bg(gtk.STATE_NORMAL, white)
        self.builder.get_object("eventbox48").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("eventbox49").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("eventbox50").modify_bg(gtk.STATE_NORMAL, green)
        self.builder.get_object("eventbox51").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("eventbox52").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("eventbox53").modify_bg(gtk.STATE_NORMAL, blue)
        for i in range(54,68):
            self.builder.get_object("eventbox" + str(i)).modify_bg(gtk.STATE_NORMAL, white)
        self.builder.get_object("eventbox67").modify_bg(gtk.STATE_NORMAL, blue)
        for i in range(68,109):
            self.builder.get_object("eventbox" + str(i)).modify_bg(gtk.STATE_NORMAL, white)
        self.builder.get_object("eventbox76").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("eventbox109").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("eventbox109").modify_bg(gtk.STATE_NORMAL, white)

        for widget in ["dialogdismissall", "maintenancemode", "changepassword",
                     "dialogreconfigure", "detachstorage", "filebackupserver",
                     "filerestoreserver", "filepoolbackupdb", "filepoolrestoredb",
                     "detachhbalun", "formatdisklun", "reattachhbalun",
                     "reattachformathbalun", "filesave", "fileopen",
                     "filelicensekey", "newvmdisk", "dialogdeletevm",
                     "warninglicense", "aboutdialog", "menu_snapshot",
                     "dialogsnaptplname", "dialogsnaptplname", "dialogsnapshotdelete",
                     "removeserverfrompool", "repairstorage", "menu_add_server",
                     "menu_add_to_pool", "menu_m_add_server", "menu_server_add_to_pool", 
                     "menu_pool_migrate", "migratetoolhelp","filesavereport", "updatemanager",
                     "filenewupdate", "wcustomfields", "fileexportmap", "dialoglicensehost"
                     ]:
            self.builder.get_object(widget).modify_bg(gtk.STATE_NORMAL, blue)

        for button in ["checksavepassword"]:
            self.builder.get_object(button).modify_bg(gtk.STATE_NORMAL, blue)
            self.builder.get_object(button).modify_bg(gtk.STATE_ACTIVE, blue)
            self.builder.get_object(button).modify_bg(gtk.STATE_PRELIGHT, blue)
            self.builder.get_object(button).modify_bg(gtk.STATE_SELECTED, blue)
            self.builder.get_object(button).modify_bg(gtk.STATE_INSENSITIVE, blue)
        for button in ["button1", "linkbutton1", "linkbutton2"]:
            self.builder.get_object(button).modify_bg(gtk.STATE_NORMAL, white)
            self.builder.get_object(button).modify_bg(gtk.STATE_ACTIVE, white)
            self.builder.get_object(button).modify_bg(gtk.STATE_PRELIGHT, white)
            self.builder.get_object(button).modify_bg(gtk.STATE_SELECTED, white)
            self.builder.get_object(button).modify_bg(gtk.STATE_INSENSITIVE, white)
        for button in ["btstgnewdisk","btstgproperties","btstgremove","btvmproperties",
                "bthostproperties","btvmaddstorage","btstorageattach","btstorageproperties",
                "btstoragedeactivate","btstoragedetach","btstoragedelete","bthostnicremove",
                "bthostnicreadd","bthostnetworkproperties","bthostnetworkadd","bthostnetworkremove",
                "btaddinterface","btpropertiesinterface","btremoveinterface","bttakesnapshot","button1",
                "btsavefile","btcancelsavefile","btopenfile","btcancelopenfile","addnewvmstorage",
                "editnewvmstorage","deletenewvmstorage","addnewvmnetwork","deletenewvmnetwork",
                "acceptnewvmdisk","cancelnewvmdisk","acceptvmaddnewdisk","cancelvmaddnewdisk",
                "btacceptsnapshotname","btcancelsnapshotname","btacceptsnaptplname","btcancelsnaptplname",
                "btacceptsnapshotdelete","btcancelsnapshotdelete","btacceptattachdisk","btcancelattachdisk",
                "acceptdeletedisk","canceldeletedisk","acceptaddnetwork","canceladdnetwork",
                "acceptremovenetwork","cancelremovenetwork","dialogdelete_accept","dialogdelete_cancel",
                "dialogdeletevdi_accept","dialogdeletevdi_cancel","windowcopyvm_copy","windowcopyvm_cancel",
                "btalertdismiss","btalertdismissall","btclosewindowalerts","btdismissallyes","btdismissallno",
                "btmoveup","btmovedown","btvmpropaccept","btvmpropcancel","connectAddServer","cancelAddServer",
                "acceptdialogsyslogempty","acceptdialogdeletehostnetwork","canceldialogdeletehostnetwork",
                "acceptdialogdeletehostnic","canceldialogdeletehostnic","btaddbondednic","btrembondednic",
                "btacceptaddbond","btcanceladdbond","acceptnewnetwork","cancelnewnetwork",
                "acceptdialogoptions","canceldialogoptions","acceptmasterpassword","cancelmasterpassword",
                "accepteditnetwork","canceleditnetwork","acceptdialognetworkrestart","btimportaddnetwork",
                "btimportdeletenetwork", "previousvmimport", "nextvmimport", "finishvmimport", "cancelvmimport",
                "acceptmgmtinterface", "cancelmgmtinterface", "btmgmtnewinterface", "canceldialogreconfigure",
                "acceptdialogreconfigure", "acceptnewpool", "cancelnewpool","acceptchangepassword","cancelchangepassword",
                "acceptdetachstorage", "canceldetachstorage","savefilebackupserver", "cancelfilebackupserver",
                "openfilerestoreserver", "cancelrestoreserver","btpoolproperties", "bttplproperties", "btstgproperties",
                "accepformatdisklun", "cancelformatdisklun", "acceptdetachhbalun","acceptreattachhbalun", 
                "cancelreattachhbalun", "cancelreattachformathbalun", "acceptareattachformathbalun", 
                "acceptbreattachformathbalun", "acceptconfirmreboot", "cancelconfirmreboot", "accepthostdmesg",
                "acceptmaintenancemode","cancelmaintenancemode","acceptfilepoolbackupdb", "cancelfilepoolbackupdb",
                "acceptfilepoolrestoredb", "cancelfilepoolrestoredb","rebootconfirmpoolrestoredb","dryrunconfirmpoolrestoredb",
                "cancelconfirmpoolrestoredb", "acceptsavescreenshot", "cancelsavescreenshot", "acceptremoveserverfrompool",
                "cancelremoveserverfrompool", "acceptrepairstorage", "cancelrepairstorage", "acceptforcejoinpool",
                "cancelforcejoinpool", "savefiledownloadlogs", "cancelfiledownloadlogs", "helpmigratetool",
                "acceptmigratetool", "cancelmigratetool", "cancelfileoutputxva", "acceptfileoutputxva", "closemigratetoolhelp",
                "acceptstatusreport", "cancelstatusreport", "clearallstatusreport", "selectallstatusreport",
                "acceptfilereport", "cancelfilereport", "previouswindownewvm", "nextwindownewvm", "cancelwindownewvm",
                "finishwindownewvm", "closeupdatemanager", "btuploadnewupdate", "btapplypatch", "btremoveupdate",
                "acceptfilenewupdate", "cancelfilenewupdate", "btgraphtenmin",  "btgraphtwohours",
                "btgraphoneweek", "btgraphoneyear", "btsendctraltdel", "btenterfullscreen", "btundockconsole", "btsendctrlaltdel1", "btsendctrlaltdel2", "btredockconsole",
                "btexitfullscreen", "bteditcustomfields", "addcustomfield", "deletecustomfield", "cancelwcustomfields",
                "acceptwcustomfields", "btexportmap", "rescanisos", "btnewstgsaoescan", "btsnapnewvm",
                "btsnapcreatetpl", "btsnapexport", "btsnapexportvm", "btsnapdelete", "btsnaprevert", "acceptdialogrevert", "canceldialogrevert",
                "acceptconfirmshutdown", "cancelconfirmshutdown", "acceptlicensehost", "cancellicensehost", "btcopytext", "btleavedomain",
                "btjoindomain", "btadduser", "btremoveuser", "btlogoutuser", "btchangerole"
                ]:
            self.builder.get_object(button).modify_bg(gtk.STATE_NORMAL, blue)
            self.builder.get_object(button).modify_bg(gtk.STATE_ACTIVE, blue)
            self.builder.get_object(button).modify_bg(gtk.STATE_PRELIGHT, blue)
            self.builder.get_object(button).modify_bg(gtk.STATE_SELECTED, blue)
            self.builder.get_object(button).modify_bg(gtk.STATE_INSENSITIVE, blue)
        for combo in ["combovmstoragedvd"]:
            self.builder.get_object(combo).modify_bg(gtk.STATE_NORMAL, blue)
            self.builder.get_object(combo).modify_bg(gtk.STATE_ACTIVE, blue)
            self.builder.get_object(combo).modify_bg(gtk.STATE_PRELIGHT, blue)
            self.builder.get_object(combo).modify_bg(gtk.STATE_SELECTED, blue)
            self.builder.get_object(combo).modify_bg(gtk.STATE_INSENSITIVE, blue)
        for i in range(1,8): 
            self.builder.get_object("lbltreesearch" + str(i)).get_parent().get_parent().get_parent().modify_bg(gtk.STATE_NORMAL, header)
            self.builder.get_object("lbltreesearch" + str(i)).get_parent().get_parent().get_parent().modify_bg(gtk.STATE_PRELIGHT, header)
        for i in range(1,5): 
            self.builder.get_object("lbltreestg" + str(i)).get_parent().get_parent().get_parent().modify_bg(gtk.STATE_NORMAL, header)
        for i in range(1,11): 
            self.builder.get_object("lbltreevmstorage" + str(i)).get_parent().get_parent().get_parent().modify_bg(gtk.STATE_NORMAL, header)
        for i in range(1,8): 
            self.builder.get_object("lbltreehoststorage" + str(i)).get_parent().get_parent().get_parent().modify_bg(gtk.STATE_NORMAL, header)
        for i in range(1,9): 
            self.builder.get_object("lbltreehostnics" + str(i)).get_parent().get_parent().get_parent().modify_bg(gtk.STATE_NORMAL, header)
        for i in range(1,8): 
            self.builder.get_object("lbltreehostnetwork" + str(i)).get_parent().get_parent().get_parent().modify_bg(gtk.STATE_NORMAL, header)
        for i in range(1,7): 
            self.builder.get_object("lbltreevmnetwork" + str(i)).get_parent().get_parent().get_parent().modify_bg(gtk.STATE_NORMAL, header)
        for i in range(1,5): 
            self.builder.get_object("lbltreealerts" + str(i)).get_parent().get_parent().get_parent().modify_bg(gtk.STATE_NORMAL, header)

        self.builder.get_object("eventbox11").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("eventboxprop").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("addserver").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("dialog-addserver").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("dialog-vbox23").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("newstorage").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("dialogvmprop").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("menubar1").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("window1").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("scrolledwindow1").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("savescreenshot").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("filedownloadlogs").modify_bg(gtk.STATE_NORMAL, blue)
        for i in range(1,60):
            if self.builder.get_object("scrolledwindow" + str(i)):
                if type(self.builder.get_object("scrolledwindow" + str(i)).get_hscrollbar()) != "NoneType":
                    self.builder.get_object("scrolledwindow" + str(i)).get_hscrollbar().modify_bg(
                            gtk.STATE_INSENSITIVE, blue)
                    self.builder.get_object("scrolledwindow" + str(i)).get_hscrollbar().modify_bg(
                            gtk.STATE_NORMAL, blue)
                if type(self.builder.get_object("scrolledwindow" + str(i)).get_vscrollbar()) != "NoneType":
                    self.builder.get_object("scrolledwindow" + str(i)).get_vscrollbar().modify_bg(
                            gtk.STATE_INSENSITIVE, blue)
                    self.builder.get_object("scrolledwindow" + str(i)).get_vscrollbar().modify_bg(
                            gtk.STATE_NORMAL, blue)
        self.builder.get_object("toolbar").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("menu_vm").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("hpaned1").modify_bg(gtk.STATE_NORMAL, blue)
        for i in range(1,12):
            self.builder.get_object("menu" + str(i)).modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("vpaned1").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("vpaned2").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("vpaned3").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("vpaned4").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("vpaned5").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("tabbox").modify_bg(gtk.STATE_NORMAL, white)
        self.builder.get_object("tabbox").modify_bg(gtk.STATE_ACTIVE, blue)
        self.builder.get_object("treesearch").modify_bg(gtk.STATE_NORMAL, white)
        self.builder.get_object("treesearch").modify_bg(gtk.STATE_ACTIVE, white)
        self.builder.get_object("treesearch").modify_bg(gtk.STATE_PRELIGHT, white)
        self.builder.get_object("treesearch").modify_bg(gtk.STATE_SELECTED, white)
        self.builder.get_object("treesearch").modify_bg(gtk.STATE_INSENSITIVE, white)
        self.builder.get_object("framesearch").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("scrolledwindow13").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("newstgreattachnfs").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("newstgreattachaoe").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("formatiscsidisk").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("reattachformatiscsidisk").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("dialog-vbox39").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("confirmreboot").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("confirmshutdown").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("hostdmesg").modify_bg(gtk.STATE_NORMAL, blue)
 

    def visible_func_templates(self, model, iter_ref, user_data=None): 
        name = self.builder.get_object("listtemplates").get_value(iter_ref, 1)
        txttemplatesearch = self.builder.get_object("txttemplatesearch")
        if txttemplatesearch.get_text().strip() == "":
            return True
        else:
            return name.lower().count(txttemplatesearch.get_text().lower()) > 0

    def visible_func(self, model, iter_ref, user_data=None): 
        """
        This function define if a element should be showed or not in left tree
        This function checks configuration values and show/hide elements
        Returning False you hide the element, returning True you show the element
        """
        host =  self.treestore.get_value(iter_ref, 5)
        ref =  self.treestore.get_value(iter_ref, 6)
        seltype =  self.treestore.get_value(iter_ref, 3)
        if len(self.txttreefilter.get_text())>0 and \
           ((seltype == "vm" or seltype == "template" or seltype == "storage" or seltype == "custom_template") and 
            self.treestore.get_value(iter_ref, 1).lower().count(self.txttreefilter.get_text().lower()) == 0):
             return False
        if seltype == "vm" and str(self.config["gui"]["show_hidden_vms"]) == "False" and host and ref and \
                self.xc_servers[host].all_vms[ref].get("other_config") and \
                str(self.xc_servers[host].all_vms[ref]["other_config"].get("HideFromXenCenter")).lower() == "true":
             return False
        if seltype == "template":
             if self.config["gui"]["show_xs_templates"] == "False" or \
                 not self.config["gui"]["show_xs_templates"]:
                return False
        elif seltype == "custom_template":
             if self.config["gui"]["show_custom_templates"] == "False" or \
                not self.config["gui"]["show_custom_templates"]:
                return False
        elif seltype == "storage":
             if self.config["gui"]["show_local_storage"] == "False" or \
                not self.config["gui"]["show_local_storage"]:
                if host and ref:
                    if not self.xc_servers[host].all_storage[ref]['shared']:
                        return False
        return True
    def foreach_connect(self, model, path, iter_ref, user_data):
        """
        This function connect or disconnect depends user_data value
        if user_data is True then connect all disconnected servers
        if user_data is False then disconnect all connected servers
        No code commented because doesn't work so well.. 
        """
        if self.treestore.get_value(iter_ref, 3) == "server":
            if self.treestore.get_value(iter_ref, 4) == "Disconnected":
                if user_data:
                    name = self.treestore.get_value(iter_ref, 1)
                    if self.config_hosts[name][1]:
                        path = self.modelfilter.convert_path_to_child_path(path)
                        self.treeview.get_selection().select_path(path)
                        iter_ref= self.treestore.get_iter(path)
                        self.selected_iter = iter_ref
                        self.selected_name = self.treestore.get_value(iter_ref, 1)
                        self.selected_uuid = self.treestore.get_value(iter_ref, 2)
                        self.selected_type = self.treestore.get_value(iter_ref, 3)
                        self.selected_state = self.treestore.get_value(iter_ref, 4)
                        self.selected_host = self.treestore.get_value(iter_ref, 5)
                        self.selected_ip = self.treestore.get_value(iter_ref, 8)

                        self.on_m_connect_activate(self.treestore, None)
                        self.treesearch.expand_all()

        if self.treestore.get_value(iter_ref, 3) == "host" or self.treestore.get_value(iter_ref, 3) == "pool":
            if self.treestore.get_value(iter_ref, 4) == "Running":
                if not user_data:
                    path = self.modelfilter.convert_path_to_child_path(path)
                    self.treeview.get_selection().select_path(path)
                    iter_ref= self.treestore.get_iter(path)
                    self.selected_iter = iter_ref
                    self.selected_name = self.treestore.get_value(iter_ref, 1)
                    self.selected_uuid = self.treestore.get_value(iter_ref, 2)
                    self.selected_type = self.treestore.get_value(iter_ref, 3)
                    self.selected_state = self.treestore.get_value(iter_ref, 4)
                    self.selected_host = self.treestore.get_value(iter_ref, 5)
                    self.selected_ip = self.treestore.get_value(iter_ref, 8)

                    self.on_m_disconnect_activate(self.treestore, None)
                    self.treesearch.expand_all()

            else:
                print "**", self.treestore.get_value(iter_ref, 4)
    def on_window1_configure_event(self, widget, data=None):
        self.on_window1_size_request(widget, data)
        
    def on_window1_size_request(self, widget, data=None):
        if self.hWnd != 0:
            console_area = self.builder.get_object("frameconsole")
            console_area.realize()
            console_alloc = console_area.get_allocation()
            window_alloc = self.window.get_position()
            x = console_alloc.x + window_alloc[0] + 10
            y = console_alloc.y + window_alloc[1] + 47
            win32gui.MoveWindow(self.hWnd, x, y, console_alloc.width-10, console_alloc.height-5, 1)
        
    def on_console_area_key_press_event(self, widget, event):
        self.tunnel.key = hex(event.hardware_keycode - 8)

    def on_aboutdialog_close(self, widget, data=None):
        """
        Function to hide about dialog when you close it
        """
        self.builder.get_object("aboutdialog").hide()
    
    def on_acceptmasterpassword_clicked(self, widget, data=None):
        """
        Function what checks ff you typed a master password is right
        """
        # Create a md5 object
        m = hashlib.md5()
        password = self.builder.get_object("txtaskmasterpassword").get_text()
        # Add password typed to md5 object
        m.update(password)
        # m.hexdigest() is a md5 ascii password (as saved in the configuration)
        if self.config["gui"]["master_password"] != m.hexdigest():
            # If is wrong show the label indicating is a wrong password
            self.builder.get_object("lblwrongpassword").show()
        else:
            # If is a good password set to global variable "password" and hide dialog
            self.password = password
            self.builder.get_object("masterpassword").hide()
    def on_cancelmasterpassword_clicked(self, widget, data=None):
        """
         Function called when you cancel the master password dialog.
         """
        #If you cancel the dialog, then set global variable "password" to None
        self.password = None
        self.builder.get_object("masterpassword").hide()
    def on_txtaskmasterpassword_changed(self, widget, data=None):
        """
        Function called when you write or remove characters on master password entry
        """
        # If you check "save server passwords" then you need specify a master password
        # If len of master password is 0, then disable "Accept" button in options dialog
        self.builder.get_object("acceptmasterpassword").set_sensitive(len(widget.get_text()))
        
    def update_tabs(self):
        """
        Function called when you select a element from left tree
        Depending selected type show or hide differents tabs
        """
        frames = ("framestggeneral", "framememory","framestgdisks","framevmgeneral", "framevmstorage", "framevmnetwork", "framehostgeneral", "framehostnetwork", "framehoststorage",  "frameconsole", "framehostnics", "framesnapshots","frameperformance","frametplgeneral","framehome","frameconsole", "framepoolgeneral", "framelogs", "framesearch", "frameusers", "framemaps", "framehosthw")
        showframes = {
            "pool" : ["framepoolgeneral", "framelogs", "framesearch", "framemaps"],
            "home" : ["framehome"],
            "vm"   : ["framevmgeneral", "framememory", "framevmstorage", "framevmnetwork", "framelogs", "framesnapshots","frameperformance"],
            "host" : ["framesearch","framehostgeneral", "framehostnetwork", "framehoststorage", "framelogs", "frameconsole", "framehostnics", "frameperformance", "frameusers", "framemaps"],
            "template" : ["frametplgeneral","framevmnetwork","framehostgeneral"],
            "custom_template" : ["frametplgeneral","framevmnetwork", "framevmstorage", "framelogs"],
            "storage" :  ["framestggeneral","framestgdisks", "framelogs"],
        } 
        if self.selected_type in showframes:
            [self.builder.get_object(frame).show() for frame in showframes[self.selected_type]]
            [self.builder.get_object(frame).hide() for frame in frames if frame not in showframes[self.selected_type]]
 
        if self.selected_type == "pool":
            self.xc_servers[self.selected_host].update_tab_pool_general(self.selected_ref, self.builder)     

        elif self.selected_type == "vm":
            # If "VM" is running, show console tab, else hide
            if self.selected_state == "Running":
                self.builder.get_object("frameconsole").show()
            else:
                self.builder.get_object("frameconsole").hide()
            self.xc_servers[self.selected_host].update_tab_vm_general(self.selected_ref, self.builder)     
        elif self.selected_type == "host":
            self.xc_servers[self.selected_host].update_tab_host_general(self.selected_ref, self.builder)    
            if self.xc_servers[self.selected_host].has_hardware_script(self.selected_ref):
                self.builder.get_object("framehosthw").show()
            else:
                self.builder.get_object("framehosthw").hide()


        elif self.selected_type == "template":
            self.xc_servers[self.selected_host].update_tab_template(self.selected_ref, self.builder)     
        elif self.selected_type == "custom_template":
            self.xc_servers[self.selected_host].update_tab_template(self.selected_ref, self.builder)     

        elif self.selected_type == "storage":
            operations = self.xc_servers[self.selected_host].all_storage[self.selected_ref]['allowed_operations']
            if operations.count("vdi_create"):
                self.builder.get_object("btstgnewdisk").show()
            else:
                self.builder.get_object("btstgnewdisk").hide()
            self.xc_servers[self.selected_host].update_tab_storage(self.selected_ref, self.builder)     

        # Experimental only
        try: 
            import webkit 
            import glob
            for deletepage in self.delete_pages:
                # FIXME: remove doesn't work
                self.builder.get_object("tabbox").get_nth_page(deletepage).hide_all()

            self.delete_pages = []
            for infile in glob.glob("plugins/*.xml"):
                data = open(infile).read()
                """
                dom = xml.dom.minidom.parseString(data)
                nodes = dom.getElementsByTagName("XenCenterPlugin")
                applicable = False
                if len(nodes[0].getElementsByTagName("TabPage")):
                    for tabpage in  nodes[0].getElementsByTagName("TabPage"):
                        if tabpage.attributes.getNamedItem("search"):
                            search_uuid = tabpage.attributes.getNamedItem("search").value
                            tabname = tabpage.attributes.getNamedItem("name").value # REVISE
                            url = tabpage.attributes.getNamedItem("url").value # REVISE
                            if len(nodes[0].getElementsByTagName("Search")):
                               host = self.selected_host
                [applicable, ip] = self.plugin_get_search(nodes, search_uuid, host, ref)
                """
                host = self.selected_host
                ref = self.selected_ref
                [applicable, ip, url, tabname] = self.process_xml(data, host, ref)
                if applicable:
                    view = webkit.WebView()
                    browser = gtk.ScrolledWindow()
                    url = url.replace("{$ip_address}", ip)
                    view.open(url)
                    browser.add_with_viewport(view)
                    tablabel = gtk.Label(tabname)
                    self.delete_pages.append( \
                        self.builder.get_object("tabbox").append_page(\
                            browser, tablabel))
                    browser.show_all()
        except:
            pass
    def process_xml(self, data, host, ref):
        dom = xml.dom.minidom.parseString(data)
        if dom.documentElement.nodeName != u'XenCenterPlugin':
            print "no XenCenterPlugin"
            return
        node = dom.documentElement
        ip = None
        applicable = False
        for tabpage in node.getElementsByTagName("TabPage"):
            search_uuid = tabpage.getAttribute('search')
            tabname = tabpage.getAttribute("name")  # REVISE
            url = tabpage.getAttribute("url")  # REVISE
            if search_uuid and tabname and url:
                for search in [e for e in node.getElementsByTagName("Search") if e.getAttribute("uuid") == search_uuid]:
                    for query in search.getElementsByTagName("Query"):
                        for queryscope in [e for e in query.getElementsByTagName("QueryScope")[0].childNodes if e.nodeType != dom.TEXT_NODE]:
                            if queryscope.nodeName == "LocalSR":
                                if self.selected_type == "storage":
                                    shared =  self.xc_servers[self.selected_host].all_storage[self.selected_ref]['shared']
                                    if not shared:
                                        applicable = True
                            elif queryscope.nodeName == "RemoteSR":
                                if self.selected_type == "storage":
                                    shared =  self.xc_servers[self.selected_host].all_storage[self.selected_ref]['shared']
                                    if shared:
                                        applicable = True
                            elif queryscope.nodeName == "Pool": # REVISE
                                if self.selected_type == "pool":
                                        applicable = True
                            elif queryscope.nodeName == "Vm": # REVISE
                                if self.selected_type == "vm":
                                        applicable = True
                            elif queryscope.nodeName == "Host": # REVISE
                                if self.selected_type == "host":
                                        applicable = True
        if applicable:
                for enumpropertyquery in query.getElementsByTagName("EnumPropertyQuery"):
                    data = None
                    if self.selected_type == "storage":
                        data =  self.xc_servers[host].all_storage[ref]
                        pbds = data['PBDs']
                        ip = ""
                        if "target" in self.xc_servers[host].all_pbd[pbds[0]]["device_config"]:
                            ip =  self.xc_servers[host].all_pbd[pbds[0]]["device_config"]['target']
                        #ip = data["name_description"].split(" ")[2][1:]
                    elif self.selected_type == "vm":
                        data =  self.xc_servers[host].all_vms[ref]
                        ip = self.selected_ip
                    if self.selected_type == "host":
                        data =  self.xc_servers[host].all_hosts[ref]
                        ip = self.selected_ip
                    if self.selected_type == "pool":
                        data =  self.xc_servers[host].all_pools[ref]
                        ip = self.selected_ip
                    if data:
                        prop = enumpropertyquery.attributes.getNamedItem("property").value
                        equals = enumpropertyquery.attributes.getNamedItem("equals").value
                        value = enumpropertyquery.attributes.getNamedItem("query").value
                        if prop in data:
                            if equals == "no":
                                if isinstance(data[prop], str):
                                    applicable = data[prop].count(value)>0
                                else: # REVISE
                                    applicable = False
                            else:
                                applicable = (data == value)
                        else:
                            if "XenCenter.CustomFields." + prop in data["other_config"]:
                                applicable = True
                                url = url.replace("{$%s}" % prop, data["other_config"]["XenCenter.CustomFields." + prop])
                            else:
                                applicable = False
        return [applicable, ip, url, tabname]

    def plugin_get_search(self, nodes, search_uuid, host, ref):
        """
        Determine if plugin is applicable
        """
        applicable = False
        ip = None
        for search in  nodes[0].getElementsByTagName("Search"):
            if search.attributes.getNamedItem("uuid").value == search_uuid:
                for query in search.getElementsByTagName("Query"):
                    queryscopes = query.getElementsByTagName("QueryScope")
                    for queryscope in queryscopes[0].childNodes:
                        if queryscope.nodeName != "#text":
                            if queryscope.nodeName == "LocalSR":
                                if self.selected_type == "storage":
                                    shared =  self.xc_servers[host].all_storage[ref]['shared']
                                    if not shared:
                                        applicable = True
                            elif queryscope.nodeName == "RemoteSR":
                                if self.selected_type == "storage":
                                    shared =  self.xc_servers[host].all_storage[ref]['shared']
                                    if shared:
                                        applicable = True
                            elif queryscope.nodeName == "Pool": # REVISE
                                if self.selected_type == "pool":
                                        applicable = True
                            elif queryscope.nodeName == "Vm": # REVISE
                                if self.selected_type == "VM":
                                        applicable = True
                            elif queryscope.nodeName == "Host": # REVISE
                                if self.selected_type == "host":
                                        applicable = True
        if applicable:
            for enumpropertyquery in query.getElementsByTagName("EnumPropertyQuery"):
                data = None
                if self.selected_type == "storage":
                    data =  self.xc_servers[host].all_storage[ref]
                    ip = data["name_description"].split(" ")[2][1:]
                elif self.selected_type == "vm":
                    data =  self.xc_servers[host].all_vms[ref]
                    ip = self.selected_ip
                if self.selected_type == "host":
                    data =  self.xc_servers[host].all_hosts[ref]
                    ip = self.selected_ip
                if self.selected_type == "pool":
                    data =  self.xc_servers[host].all_pools[ref]
                    ip = self.selected_ip
                if data:
                    prop = enumpropertyquery.attributes.getNamedItem("property").value
                    equals = enumpropertyquery.attributes.getNamedItem("equals").value
                    value = enumpropertyquery.attributes.getNamedItem("query").value
                    if prop in data:
                        if equals == "no":
                            if isinstance(data[prop], str):
                                applicable = data[prop].count(value)>0
                            else: # REVISE
                                applicable = False
                        else:
                            applicable = (data == value)
                    else:
                        applicable = False
        return [applicable, ip]

    def on_window_destroy(self, widget, data=None):
        """
        Function called when you close the window or press Quit
        """
        # For each server
        if self.tunnel:
            self.tunnel.close()

        for sh in  self.xc_servers:
            # Stop the threads setting True the condition variables
            self.xc_servers[sh].halt = True
            self.xc_servers[sh].halt_search = True
            self.xc_servers[sh].halt_import = True
            self.xc_servers[sh].halt_performance = True
            # Do a logout, remember logout disconnect to server and unregister events
            self.xc_servers[sh].logout()
        # For windows only: close the tightvnc console
        if self.hWnd != 0:
            win32gui.PostMessage(self.hWnd, win32con.WM_QUIT, 0, 0)
            self.hWnd = 0
        # Save unsaved changes
        self.config.write()
        # Exit!
        gtk.main_quit()
        if self.tunnel:
            self.tunnel.close()


    def count_list(self, model, path, iter_ref, user_data):
        """
        Function to count elements from list.. 
        """
        #TODO: remove and use __len__()
        self.nelements = self.nelements + 1
    def on_tabbox_focus_tab(self, widget, data=None, data2=None):
        """
        Function called when you click on a tab
        Tabbox contains all possible tabs, when you click on a tab first we will check the name
        Depending of this name we will do differents actions
        """
        # Get the Tab name
        #tab_label = widget.get_tab_label(widget.get_nth_page(data2)).name
        tab_label =  gtk.Buildable.get_name(widget.get_tab_label(widget.get_nth_page(data2)))
        # Set as selected
        self.selected_tab = tab_label
        if tab_label != "VM_Console":
            if self.tunnel and not self.noclosevnc:
                self.tunnel.close()
            # If vnc console was opened and we change to another, close it
            self.builder.get_object("menuitem_tools_cad").set_sensitive(False)
            if hasattr(self,"vnc") and self.vnc and not self.noclosevnc:
                self.vnc.destroy()
                self.builder.get_object("windowvncundock").hide()
                self.vnc = None
            # Same on Windows
            if self.hWnd != 0:
                win32gui.PostMessage(self.hWnd, win32con.WM_QUIT, 0, 0)
                self.hWnd = 0
        if tab_label != "HOST_Search" and self.selected_host:
            # If we change tab to another different to HOST Search, then stop the filling thread
                self.xc_servers[self.selected_host].halt_search = True
        if tab_label != "VM_Performance" and self.selected_host:
            self.xc_servers[self.selected_host].halt_performance = True
            
        if tab_label == "VM_Console":
            self.builder.get_object("menuitem_tools_cad").set_sensitive(True)
            self.treeview = self.builder.get_object("treevm") 
            if hasattr(self,"vnc") and self.vnc:
                if self.tunnel:
                    self.tunnel.close()
                self.vnc.destroy()
                self.builder.get_object("windowvncundock").hide()
                self.vnc = None

            if self.treeview.get_cursor()[1]:
                state = self.selected_state
                host =  self.selected_host
                # First checks if VM is running
                self.builder.get_object("btenterfullscreen").grab_focus()
                self.builder.get_object("console_area").grab_focus()
                if  state == "Running":
                    if sys.platform != "win32" and sys.platform != "darwin":
                        # Create a gtkvnc object
                        self.vnc = gtkvnc.Display()
                        # Add to gtkvnc to a console area
                        console_area = self.builder.get_object("console_area")


                        console_area.add(self.vnc)
                        console_area.show_all()

                        self.vnc.activate()
                        self.vnc.grab_focus()
                        self.vnc.set_pointer_grab(False)
                        self.vnc.set_pointer_local(False)
                        self.vnc.set_keyboard_grab(True)
                        self.vnc.set_shared_flag(True)
                        self.vnc.connect("vnc-disconnected", self.vnc_disconnected)
                        self.vnc.connect("key_press_event", self.on_console_area_key_press_event)
                        from tunnel import Tunnel
                        if self.selected_type == "host":
                            ref = self.xc_servers[self.selected_host].host_vm[self.selected_ref][0]
                        else:
                            ref = self.selected_ref
                        if self.xc_servers[self.selected_host].all_vms[ref]["consoles"]:
                            console_ref = self.xc_servers[self.selected_host].all_vms[ref]["consoles"][0]
                            location = self.xc_servers[self.selected_host].all_console[console_ref]["location"]
                            self.tunnel = Tunnel(self.xc_servers[self.selected_host].session_uuid, location)
                            port = self.tunnel.get_free_port()
                            Thread(target=self.tunnel.listen, args=(port,)).start()
                            time.sleep(1)
                            # And open the connection
                            try:
                                self.vnc.set_depth(1)
                            except:
                                pass

                            self.vnc.connect("vnc-server-cut-text", self.vnc_button_release) 
                            self.vnc.open_host("localhost", str(port))
                        else:
                            print "No console available"

                    elif sys.platform == "darwin":
                        from tunnel import Tunnel
                        if self.selected_type == "host":
                            ref = self.xc_servers[self.selected_host].host_vm[self.selected_ref][0]
                        else:
                            ref = self.selected_ref
                        # Run ./vncviewer with host, vm renf and session ref
                        if self.xc_servers[self.selected_host].all_vms[ref]["consoles"]:
                            console_ref = self.xc_servers[self.selected_host].all_vms[ref]["consoles"][0]
                            location = self.xc_servers[self.selected_host].all_console[console_ref]["location"]
                            self.tunnel = Tunnel(self.xc_servers[self.selected_host].session_uuid, location)
                            port = self.tunnel.get_free_port()
                            Thread(target=self.tunnel.listen, args=(port,)).start()
                            time.sleep(1)
                            os.spawnl(os.P_NOWAIT,"./vncviewer", "vncviewer", "localhost::%s" % port)
                            console_area = self.builder.get_object("console_area")
                            console_alloc = console_area.get_allocation()
                        else:
                            print "No console available"

                    else:
                        if self.selected_type == "host":
                            ref = self.xc_servers[self.selected_host].host_vm[self.selected_ref][0]
                        else:
                            ref = self.selected_ref
                        # Run vncviewer.exe with host, vm renf and session ref
                        param = self.xc_servers[host].get_connect_parameters(ref, self.selected_ip)
                        os.spawnl(os.P_NOWAIT,"vncviewer.exe", "vncviewer.exe", "%s" % (param))
                        console_area = self.builder.get_object("frameconsole")
                        console_area.realize()
                        console_alloc = console_area.get_allocation()
                        window_alloc = self.window.get_position()
                        x = console_alloc.x + window_alloc[0] + 10
                        y = console_alloc.y + window_alloc[1] + 47
                        # On windows we'll move the window.. 
                        while win32gui.FindWindow(None, "HVMXEN-%s" % (self.selected_uuid)) == 0 \
                              and win32gui.FindWindow(None, "XenServer Virtual Terminal") == 0:
                            pass
                        self.hWnd = win32gui.FindWindow(None, "HVMXEN-%s" % (self.selected_uuid))
                        if self.hWnd == 0:
                            self.hWnd = win32gui.FindWindow(None, "XenServer Virtual Terminal")
                        #win32gui.ShowWindow(self.hWnd, win32con.SW_HIDE)
                        
                        win32gui.MoveWindow(self.hWnd, x, y, console_alloc.width-10, console_alloc.height-5, 1)
                        #win32gui.ShowWindow(self.hWnd, win32con.SW_SHOW)
                        
                        
                else:
                    print  state
        if tab_label == "VM_Memory":
            self.update_memory_tab()
            

        if tab_label == "VM_Storage":
            if self.treeview.get_cursor()[1]:
                # liststorage contains the storage on VM
                liststorage = self.builder.get_object("listvmstorage")
                # liststoragdvd contains the possibles dvd/isos to mount on VM
                liststoragedvd = self.builder.get_object("listvmstoragedvd")
                #liststoragedvd.set_sort_func(1, self.compare_data)
                host =  self.selected_host
                # Fill liststorage
                self.xc_servers[host].fill_vm_storage(self.selected_ref, \
                                         liststorage)
                # Fill liststoragedvd, fill_vm_storage_dvd return the current dvd/iso mounted
                active = self.xc_servers[host].fill_vm_storage_dvd(self.selected_ref, \
                                         liststoragedvd)
                # Flag variable to no emit signal
                self.set_active = True
                # Set as the active dvd/iso mounted
                self.builder.get_object("combovmstoragedvd").set_active(active)
                self.set_active = False
        elif tab_label == "VM_Network":
            if self.treeview.get_cursor()[1]:
                treenetwork = self.builder.get_object("treevmnetwork")
                # listvmnetwork contains the networks of a vm
                listnetwork = self.builder.get_object("listvmnetwork")
                host =  self.selected_host
                # Fill the list of networks
                self.xc_servers[host].fill_vm_network(self.selected_ref, \
                                         treenetwork, listnetwork)
        elif tab_label == "VM_Snapshots":
            if self.treeview.get_cursor()[1]:
                treevmsnapshots = self.builder.get_object("treevmsnapshots")
                # listvmsnapshots contains the snapshots of a vm
                listvmsnapshots = self.builder.get_object("listvmsnapshots")
                host =  self.selected_host
                # Fill the list of snapshots
                self.xc_servers[host].fill_vm_snapshots(self.selected_ref, \
                                         treevmsnapshots, listvmsnapshots)
        elif tab_label == "VM_Performance":
            if self.treeview.get_cursor()[1]:
                # Thread to update performance images
                ref = self.selected_ref
                host = self.selected_host
                if self.selected_type == "vm":
                    self.builder.get_object("scrolledwindow50").show()
                    self.builder.get_object("labeldiskusage").show()
                    Thread(target=self.xc_servers[host].update_performance, args=(self.selected_uuid, ref, \
                                             self.selected_ip, False)).start()
                else:
                    self.builder.get_object("scrolledwindow50").hide()
                    self.builder.get_object("labeldiskusage").hide()
                    if self.selected_host and self.selected_ref in self.xc_servers[self.selected_host].host_vm:
                        uuid = self.xc_servers[self.selected_host].host_vm[self.selected_ref][1]
                        Thread(target=self.xc_servers[host].update_performance, args=(uuid, ref, \
                                                 self.selected_ip, True)).start()

        elif tab_label == "VM_Logs":
            if self.treeview.get_cursor()[1]:
                treeviewlog = self.builder.get_object("treeviewlog")
                # listlog contains the snapshots of a vm/host
                listlog = self.builder.get_object("listlog")
                host =  self.selected_host
                # Fill the list of logs
                if self.selected_type == "vm":
                    self.xc_servers[host].fill_vm_log(self.selected_uuid, \
                                             treeviewlog, listlog)
                else:
                    self.xc_servers[host].fill_vm_log(self.selected_uuid, \
                                             treeviewlog, listlog)

        elif tab_label == "HOST_Users":
            if self.selected_type == "pool":
                name =  self.xc_servers[self.selected_host].all_pools[self.selected_ref]['name_label']
                externalauth =  self.xc_servers[self.selected_host].get_external_auth(self.xc_servers[self.selected_host]['master'])
            else:
                name = self.xc_servers[self.selected_host].all_hosts[self.selected_ref]['name_label']
                externalauth =  self.xc_servers[self.selected_host].get_external_auth(self.selected_ref)


            listusers = self.builder.get_object("listusers")
            self.xc_servers[self.selected_host].fill_domain_users(self.selected_ref, listusers)


            if externalauth[0] == "":
                self.builder.get_object("btjoindomain").set_sensitive(True)
                self.builder.get_object("btleavedomain").set_sensitive(False)
                self.builder.get_object("lblusersdomain").set_text("AD is not currently configured for '" + self.selected_name + "'. To enable AD authentication, click Join.")
            else:
                self.builder.get_object("btleavedomain").set_sensitive(True)
                self.builder.get_object("btjoindomain").set_sensitive(False)
                self.builder.get_object("lblusersdomain").set_text("Pool/host " + self.selected_name + " belongs to domain '" + externalauth[1] + "'. To enable AD authentication, click Join.")


        elif tab_label == "HOST_Storage":
            if self.treeview.get_cursor()[1]:
                # listhoststorage contains the snapshots of a vm/host
                liststorage = self.builder.get_object("listhoststorage")
                host =  self.selected_host
                # Fill the list of storage
                self.xc_servers[host].fill_host_storage(self.selected_ref, \
                                         liststorage)
        elif tab_label == "HOST_Nics":
            if self.treeview.get_cursor()[1]:
                """
                liststorage = self.builder.get_object("listhostnics")
                host =  self.selected_host
                self.xc_servers[host].fill_host_nics(self.selected_ref, \
                                         liststorage)
                """
                # Call to update_tab_host_nics to fill the host nics
                self.update_tab_host_nics()
        elif tab_label == "HOST_Search":
            if self.treeview.get_cursor()[1]:
                host =  self.selected_host
                self.xc_servers[host].halt_search = False
                # Host_Search contains a live monitoring status of VM
                # Create a thread to fill "listsearch"
                self.xc_servers[host].thread_host_search(self.selected_ref, self.listsearch)
                # Expand "treesearch"
                self.treesearch.expand_all()

        elif tab_label == "HOST_Hardware":
            if self.selected_host:
                self.xc_servers[self.selected_host].fill_host_hardware(self.selected_ref)
                
        elif tab_label == "HOST_Network":
            # Call to update_tab_host_network to fill the host networks
            self.update_tab_host_network()
        elif tab_label == "Local_Storage":
            if self.treeview.get_cursor()[1]:
                # liststg contains the vdi under storage
                liststg = self.builder.get_object("liststg")
                liststg.set_sort_func(1, self.compare_data)
                liststg.set_sort_column_id(1, gtk.SORT_ASCENDING)
                host =  self.selected_host
                # Fill the list of storage
                if host:
                    self.xc_servers[host].fill_local_storage(self.selected_ref, \
                                    liststg)
        elif tab_label == "Maps":
            self.update_maps()

    def compare_data(self, model, iter1, iter2):
        data1 = model.get_value(iter1,1)
        data2 = model.get_value(iter2,1)
        return cmp(data1, data2)

    def update_maps(self):
            dotcode = """
            digraph G {
                      overlap=false;
                      bgcolor=white;
                      node [shape=polygon, sides=6, fontname="Verdana", fontsize="8"];
                      edge [color=deepskyblue3, fontname="Verdana", fontsize="5"];
            """

            if self.selected_host:
                show_halted_vms = self.builder.get_object("check_show_halted_vms").get_active()
                if self.builder.get_object("check_show_network").get_active():
                    relation = self.xc_servers[self.selected_host].get_network_relation(self.selected_ref, show_halted_vms)
                    for network in relation:
                        uuid, name = network.split("_", 1)
                        safename = name.replace("&","&amp;").replace("<", "&lt;").replace("\"", "&quot;")
                        if self.builder.get_object("check_unused_network").get_active() or relation[network]:
                            dotcode += '"%s"[shape=plaintext, label=<<table border="0" cellpadding="0" cellspacing="0"><tr><td><img src="images_map/network.png"/></td></tr><tr><td> </td></tr><tr><td>%s</td></tr></table>> tooltip="%s"];' % (uuid, safename, name)
                            dotcode += "\n"
                        for vm in relation[network]:
                            uuid2, name2 = vm.split("_", 1)
                            dotcode += '"%s"[shape=plaintext, label=<<table border="0" cellpadding="0" cellspacing="0"><tr><td><img src="images_map/server.png"/></td></tr><tr><td> </td></tr><tr><td>%s</td></tr></table>>URL="%s" tooltip="%s"];' % (uuid2, name2, uuid2, name2)
                            dotcode += "\n"
                            dotcode += '"%s" -> "%s"' % (uuid, uuid2)
                            dotcode += "\n"

                if self.builder.get_object("check_show_storage").get_active():
                    dotcode += 'edge [color=forestgreen, fontname="Verdana", fontsize="5"];'
                    relation = self.xc_servers[self.selected_host].get_storage_relation(self.selected_ref, show_halted_vms)
                    for storage in relation:
                        uuid, name = storage.split("_", 1)
                        safename = name.replace("&","&amp;").replace("<", "&lt;").replace("\"", "&quot;")
                        if self.builder.get_object("check_unused_storage").get_active() or relation[storage]:
                            dotcode += '"%s"[shape=plaintext, label=<<table border="0" cellpadding="0" cellspacing="0"><tr><td><img src="images_map/storage.png"/></td></tr><tr><td> </td></tr><tr><td>%s</td></tr></table>>URL="%s" tooltip="%s"];' % (uuid, safename, uuid, name)
                            dotcode += "\n"
                        for vm in relation[storage]:
                            uuid2, name2 = vm.split("_", 1)
                            safename2 = name2.replace("&","&amp;").replace("<", "&lt;").replace("\"", "&quot;")
                            dotcode += '"%s"[shape=plaintext, label=<<table border="0" cellpadding="0" cellspacing="0"><tr><td><img src="images_map/server.png"/></td></tr><tr><td> </td></tr><tr><td>%s</td></tr></table>>URL="%s" tooltip="%s"];' % (uuid2, safename2, uuid2, name2)
                            dotcode += "\n"
                            dotcode += '"%s" -> "%s"' % (uuid2, uuid)
                            dotcode += "\n"


                dotcode += "}"                    

                self.windowmap.set_dotcode(dotcode)
                self.builder.get_object("viewportmap").show_all()



    def on_btopenfile_activate(self, widget, data=None):
        """
        Obsoleted function 
        """
        filechooser = self.fileopen.get_children()[0].get_children()[0]
        if filechooser.get_filename():
            self.xc_servers[self.selected_host].import_vm(self.selected_ref,  filechooser.get_filename()) 
            self.fileopen.hide()
        else:
            self.show_error_dlg("Select a file")
    def on_btsavefile_activate(self, widget, data=None):
        """
        Function called when you press "Export VM"
        """
        filechooser = self.filesave.get_children()[0].get_children()[0]
        if filechooser.get_filename():
            # Call to export_vm function with vm renf and filename choosed
            if self.export_snap:
                print "Export snap.."
                self.xc_servers[self.selected_host].export_vm(self.selected_snap_ref,  filechooser.get_filename(), self.selected_ref) 
                self.export_snap = False
            elif  self.export_snap_vm:
                print "Export snap as VM.."
                self.xc_servers[self.selected_host].export_vm(self.selected_snap_ref,  filechooser.get_filename(), self.selected_ref, as_vm = True) 
                self.export_snap_vm = False
            else:
                self.xc_servers[self.selected_host].export_vm(self.selected_ref,  filechooser.get_filename()) 
            self.filesave.hide()
            self.builder.get_object("tabbox").set_current_page(17)
        else:
            self.show_error_dlg("Select a file")
    def on_filesave_confirm_overwrite(self, widget, data=None):
        """
        Not used function
        """
        print widget
        print data

            
    def on_btcancelsavefile_activate(self, widget, data=None):
        """
        If you press cancel on "Export VM" dialog, then close the dialog
        """
        self.export_snap = False
        self.filesave.hide()
    def on_btcancelopenfile_activate(self, widget, data=None):
        """
        Not used function
        """
        self.fileopen.hide()
    def on_treevm_button_press_event(self, widget, event):
        """
        Function is called when you do click (or double click) on left tree
        """
        x = int(event.x)
        y = int(event.y)
        time = event.time
        if x == -10 and y == -10:
            pthinfo = [self.modelfilter.get_path(self.treeview.get_selection().get_selected()[1]), None, 0, 0]
        else:
            pthinfo = widget.get_path_at_pos(x, y)
        if event.type == gtk.gdk._2BUTTON_PRESS: 
            # On double click, if server is disconnected then connect to it
            if self.selected_state == "Disconnected":
                self.on_m_connect_activate(widget, None)
 
        elif pthinfo is not None:
            # On single click
            path, col, cellx, celly = pthinfo
            widget.grab_focus()
            widget.set_cursor( path, col, 0)
            path = self.modelfilter.convert_path_to_child_path(path)
            iter_ref= self.treestore.get_iter(path)
            # Define selected variables
            self.selected_iter = iter_ref
            self.selected_name = self.treestore.get_value(iter_ref, 1)
            self.selected_uuid = self.treestore.get_value(iter_ref, 2)
            self.selected_type = self.treestore.get_value(iter_ref, 3)
            self.selected_state = self.treestore.get_value(iter_ref, 4)
            self.selected_host = self.treestore.get_value(iter_ref, 5)
            self.selected_ip = self.treestore.get_value(iter_ref, 8)
            # Used to prevent not manual changes
            previous_ref = self.selected_ref
            self.selected_ref = self.treestore.get_value(iter_ref, 6)

            # Define the possible actions for VM/host/storage..
            if self.selected_type == "vm": 
                self.selected_actions = self.xc_servers[self.selected_host].get_actions(self.selected_ref)
            else:
                self.selected_actions = self.treestore.get_value(iter_ref, 7)
            #if type(self.selected_actions) == type(""):
            #    self.selected_actions = eval(self.selected_actions)
            # Update menubar and tabs with new selection
            self.update_menubar() 
            self.update_tabs()
            if self.selected_ref  != previous_ref:
                # If you selected a different element than previous
                # then select the correct tab for selected type
                if self.selected_type == "vm": 
                   self.builder.get_object("tabbox").set_current_page(5)
                else:
                   self.builder.get_object("tabbox").set_current_page(3)
                if self.selected_type == "pool":
                   self.builder.get_object("tabbox").set_current_page(0)
                elif self.selected_type == "host": 
                   self.builder.get_object("tabbox").set_current_page(1)
                   self.builder.get_object("tabbox").set_current_page(4)
                elif self.selected_type == "server": 
                   self.builder.get_object("tabbox").set_current_page(2)
                elif self.selected_type == "template": 
                   self.builder.get_object("tabbox").set_current_page(2)
                elif self.selected_type == "custom_template": 
                   self.builder.get_object("tabbox").set_current_page(2)
                elif self.selected_type == "storage": 
                   self.builder.get_object("tabbox").set_current_page(1)
            if event.button == 3:
                # On right click..
                # Show the menu
                menu_vm = self.builder.get_object("menu_vm")
                collapsed = False
                expanded = False
                can_expand_or_collapse = False
                for child in range(0,self.treestore.iter_n_children(self.selected_iter)):
                    iter_ref= self.treestore.iter_nth_child(self.selected_iter, child)
                    if self.treestore.iter_n_children(iter_ref):
                        can_expand_or_collapse = True
                        path = self.treestore.get_path(iter_ref)
                        if self.treeview.row_expanded(path):
                            expanded = True 
                        else:
                            collapsed = True

                if can_expand_or_collapse:
                    if collapsed:
                        self.builder.get_object("expandall").show()
                    else:
                        self.builder.get_object("expandall").hide()
                    if expanded: 
                        self.builder.get_object("collapsechildren").show()
                    else:
                        self.builder.get_object("collapsechildren").hide()
                else:
                    self.builder.get_object("expandall").hide()
                    self.builder.get_object("collapsechildren").hide()
                     
                for child in menu_vm.get_children():
                    # Menuitems are with name "m_action"
                    # Checks if "action" is on selected_actions"
                    typestg = None
                    pbdstg = 1
                    broken = False
                    if self.selected_type == "storage":
                        typestg = self.xc_servers[self.selected_host].all_storage[self.selected_ref]["type"]
                        pbdstg = len(self.xc_servers[self.selected_host].all_storage[self.selected_ref]["PBDs"])
                    if gtk.Buildable.get_name(child)[0:2] == "m_":
                        if not self.selected_actions or \
                                self.selected_actions.count(gtk.Buildable.get_name(child)[2:]) \
                           == 0:
                            child.hide()
                        else:
                            # If selected_type is storage and typestg is not "lvm" or "udev"
                            if typestg != "lvm" and typestg != "udev":
                                # If has not pbds.. then enable only "Reattach" and "Forget"
                                if pbdstg == 0 and (gtk.Buildable.get_name(child) == "m_plug" or gtk.Buildable.get_name(child) == "m_forget"):
                                    child.show()
                                else:
                                    # Disable else
                                    if pbdstg == 0:
                                        child.hide()
                                    else:
                                        # If has pbds.. disable "Reattach"
                                        if gtk.Buildable.get_name(child) != "m_plug":
                                            child.show()
                                        else:
                                            child.hide()
                            else:
                                child.hide()
                    # Properties will be showed always else on home and disconnected servers
                    if gtk.Buildable.get_name(child) == "properties":
                        if self.selected_type == "home":
                            child.hide()
                        elif self.selected_type == "server" and not self.selected_ref:
                            child.hide()
                        else:
                            child.show()
                    # Delete will be showed only on pool
                    elif gtk.Buildable.get_name(child) == "delete":
                        if self.selected_type == "pool":
                            child.show()
                        else:
                            child.hide()
                    # Install XenServer Tools only on 
                    elif gtk.Buildable.get_name(child) == "installxenservertools":
                        if self.selected_type == "vm" and self.selected_state == "Running":
                            self.builder.get_object("separator1").show()
                            self.builder.get_object("separator2").show()
                            child.show()
                        else:
                            self.builder.get_object("separator1").hide()
                            self.builder.get_object("separator2").hide()
                            child.hide()
                    # Repair storage, only on broken storage
                    elif gtk.Buildable.get_name(child) == "m_repair_storage":
                        if self.selected_type == "storage":
                            broken = self.xc_servers[self.selected_host].is_storage_broken(self.selected_ref)
                            if broken:
                                child.show()
                            else:
                                child.hide()
                    # Add to pool, only for servers without pools
                    elif gtk.Buildable.get_name(child) == "m_add_to_pool":
                        if self.selected_type == "host":
                            pool_ref = self.xc_servers[self.selected_host].all_pools.keys()[0]
                            if self.xc_servers[self.selected_host].all_pools[pool_ref]["name_label"] == "":
                                child.show()
                            else:
                                child.hide()
                        else:
                            child.hide()
                    # Add server to pool from pool menu
                    elif gtk.Buildable.get_name(child) == "m_pool_add_server":
                        if self.selected_type == "pool":
                            child.show()
                        else:
                            child.hide()
                menu_vm.popup( None, None, None, event.button, time)

            # Update toolbar and set label/image on top right pane
            self.update_toolbar()
            self.headlabel.set_label(self.selected_name)
            self.headimage.set_from_pixbuf(self.treestore.get_value(iter_ref, 0))
    def vnc_disconnected(self, info): 
        print "VNC disconnected..", info
    def on_txttreefilter_changed(self, widget, data=None):
        """
        Function called when on left top entry you write text to filter
        """
        self.modelfilter.refilter()
        self.treeview.expand_all()
    def show_error_dlg(self, error_string, error_title="Error"):
        """This Function is used to show an error dialog when
        an error occurs.
        error_string - The error string that will be displayed
        on the dialog.
        http://www.pygtk.org/articles/extending-our-pygtk-application/extending-our-pygtk-application.htm
        """
        self.builder.get_object("walert").set_title(error_title)
        self.builder.get_object("walerttext").set_text(error_string)
        self.builder.get_object("walert").show()

    def on_closewalert_clicked(self, widget, data=None):
        self.builder.get_object("walert").hide()


    def push_alert(self, alert):
        """
        Function to set in statusbar an alert
        """
        self.statusbar.get_children()[0].get_children()[0].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#000000'))
        self.statusbar.push(1, alert)

    def push_error_alert(self, alert):
        """
        Function to set in statusbar an error alert
        """
        self.statusbar.get_children()[0].get_children()[0].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FF0000'))
        self.statusbar.push(1, alert)

    def not_implemented_yet(self, widget, data=None):
        """
        Some functions are not implemented yet, show the dialog
        """
        self.show_error_dlg("Not implemented yet") 

    def dump(self, obj):
        """
        Internal use only
        """
        for attr in dir(obj):
           print "obj.%s = %s" % (attr, getattr(obj, attr))

    def signal_handler(self):
        """
        Function called when oxc gets a signal
        """
        print "Exiting..."
        for sh in  self.xc_servers:
            self.xc_servers[sh].halt = True
            self.xc_servers[sh].halt_search = True
            self.xc_servers[sh].halt_performance = True
            self.xc_servers[sh].logout()
        self.config.write()
        if self.hWnd != 0:
            win32gui.PostMessage(self.hWnd, win32con.WM_QUIT, 0, 0)
            self.hWnd = 0
    def on_delete_event(self, widget, event):
         """
         Returning True, the window will not be destroyed
         """
         widget.hide()
         return True
    def convert_bytes(self, bytes):
        """
        Convert bytes to string
        http://www.5dollarwhitebox.org/drupal/node/84
        """
        bytes = float(bytes)
        if bytes >= 1099511627776:
            terabytes = bytes / 1099511627776
            size = '%.1fT' % terabytes
        elif bytes >= 1073741824:
            gigabytes = bytes / 1073741824
            size = '%.1fG' % gigabytes
        elif bytes >= 1048576:
            megabytes = bytes / 1048576
            size = '%.1fM' % megabytes
        elif bytes >= 1024:
            kilobytes = bytes / 1024
            size = '%.1fK' % kilobytes
        else:
            size = '%.1fb' % bytes
        return size


    def convert_bytes_mb(self, n):
        """
        Convert byes to mb string
        """
        n = float(n)
        K, M = 1 << 10, 1 << 20
        if n >= M:
            return '%d' % (float(n) / M)
        elif n >= K:
            return '%d' % (float(n) / K)
        else:
            return '%d' % n


if __name__ == "__main__":
        # Main function
        wine = oxcWindow()
        gtk.main()
