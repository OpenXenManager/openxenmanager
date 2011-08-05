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
from window_vm_network import *
from window_vm_storage import *
from window_vm_snapshot import *
from window_vm_performance import *
import gtk
import time
selection = None
class oxcWindowVM(oxcWindowVMNetwork,oxcWindowVMStorage,oxcWindowVMSnapshot,oxcWindowVMPerformance):
    """
    Class to manage window actions
    """

    def update_memory_tab(self):
        if self.treeview.get_cursor()[1]:
                dynamicmin = self.xc_servers[self.selected_host].all_vms[self.selected_ref]["memory_dynamic_min"]
                dynamicmax = self.xc_servers[self.selected_host].all_vms[self.selected_ref]["memory_dynamic_max"]
                staticmin = self.xc_servers[self.selected_host].all_vms[self.selected_ref]["memory_static_min"]
                staticmax = self.xc_servers[self.selected_host].all_vms[self.selected_ref]["memory_static_max"]
                ishvm = self.xc_servers[self.selected_host].all_vms[self.selected_ref]["HVM_boot_policy"]
                if ishvm:
                    self.builder.get_object("lbldynamicmin").set_label(self.convert_bytes_mb(dynamicmin) + " MB")
                    self.builder.get_object("lbldynamicmax").set_label(self.convert_bytes_mb(dynamicmax) + " MB")
                    self.builder.get_object("lblstaticmax").set_label(self.convert_bytes_mb(staticmax) + " MB")

                    self.builder.get_object("txtdynamicmin").set_text(self.convert_bytes_mb(dynamicmin))
                    self.builder.get_object("txtdynamicmax").set_text(self.convert_bytes_mb(dynamicmax))
                    self.builder.get_object("txtstaticmax").set_text(self.convert_bytes_mb(staticmax))
                    self.builder.get_object("tabboxmem").set_current_page(0)
                else:
                    self.builder.get_object("lbldynamicmin1").set_label(self.convert_bytes_mb(dynamicmin) + " MB")
                    self.builder.get_object("lbldynamicmax1").set_label(self.convert_bytes_mb(dynamicmax) + " MB")
                    self.builder.get_object("txtfixedmemory").set_text(self.convert_bytes_mb(staticmax))

                    self.builder.get_object("txtdynamicmin1").set_text(self.convert_bytes_mb(dynamicmin))
                    self.builder.get_object("txtdynamicmax1").set_text(self.convert_bytes_mb(dynamicmax))

                    self.builder.get_object("radiomemstatic").set_active(dynamicmin == dynamicmax)
                    self.builder.get_object("radiomemdynamic").set_active(dynamicmin != dynamicmax)
                    self.builder.get_object("tabboxmem").set_current_page(1)


    def on_btapplymemory_clicked(self, widget, data=None):
        dynamicmin = self.builder.get_object("txtdynamicmin").get_text()
        dynamicmax = self.builder.get_object("txtdynamicmax").get_text()
        staticmax = self.builder.get_object("txtstaticmax").get_text()
        self.xc_servers[self.selected_host].set_memory(self.selected_ref, dynamicmin, dynamicmax, staticmax)

    def on_btapplymemory1_clicked(self, widget, data=None):
        if self.builder.get_object("radiomemstatic").get_active():
            minimun = maximun = self.builder.get_object("txtfixedmemory").get_text()
            self.xc_servers[self.selected_host].set_memory_limits(self.selected_ref, minimun, maximun, minimun, maximun)
        else:
            minimun = self.builder.get_object("txtdynamicmin1").get_text()
            maximun = self.builder.get_object("txtdynamicmax1").get_text()
            self.xc_servers[self.selected_host].set_memory_limits(self.selected_ref, minimun, maximun, minimun, maximun)

    def on_btsendctraltdel_clicked(self, widget, data=None):
        """
        Function called when you press "send ctrl alt del" on vm console
        """
        self.on_menuitem_tools_cad_activate(widget, data)


    def vnc_button_release(self, clipboard, data, user=None):
        global selection
        selection = data
        self.vnc.client_cut_text(data)
        return 

    def copy_cb(self, clipboard, data, info, user=None):
        global selection
        data.set_text(selection, -1)

    def clear_cb(self, clipboard, data, user=None):
        return

    def on_btcopytext_clicked(self, widget, data=None):
        """
        Function called when you press "Copy selected text" on console tab
        """
        clipboard = self.vnc.get_clipboard(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.connect("owner-change", self.vnc_button_release)
        text = clipboard.wait_for_text()
        targets = [('TEXT', 0, 1), ('STRING', 0, 2), ('COMPOUND_TEXT', 0, 3), ('UTF8_STRING', 0, 4)]
        clipboard.set_with_data(targets, self.copy_cb, self.clear_cb, None);
        def text_get_func(clipboard, text, data):
            if text:
                self.vnc.client_cut_text(text)
        clipboard.request_text(text_get_func)


    def on_btundockconsole_clicked(self, widget, data=None):
        """
        Function called when you press "undock"
        """
        self.noclosevnc = True
        self.builder.get_object("windowvncundock").show()
        self.builder.get_object("console_area").remove(self.vnc)
        self.builder.get_object("console_area3").add(self.vnc)

    def on_btredockconsole_clicked(self, widget, data=None):
        """
        Function called when you press "redock"
        """
        self.builder.get_object("windowvncundock").hide()
        self.builder.get_object("console_area3").remove(self.vnc)
        self.builder.get_object("console_area").add(self.vnc)



    def on_btenterfullscreen_clicked(self, widget, data=None):
        """
        Function called when you press "enter fullscreen"
        """
        self.builder.get_object("windowvnc").show()
        self.builder.get_object("console_area").remove(self.vnc)
        self.builder.get_object("console_area2").add(self.vnc)
        self.builder.get_object("windowvnc").fullscreen()

    def on_btexitfullscreen_clicked(self, widget, data=None):
        """
        Function called when you press "exit fullscreen"
        """
        self.builder.get_object("windowvnc").hide()
        self.builder.get_object("console_area2").remove(self.vnc)
        self.builder.get_object("console_area").add(self.vnc)

    def on_windowcopyvm_cancel_activate(self, widget, data=None):
        """
        Function called when you cancel "window copy" window
        """
        self.builder.get_object("windowcopyvm").hide()

    def on_windowcopyvm_copy_activate(self, widget, data=None):
        """
        Function called when you accept "window copy" window
        """
        listcopystg = self.builder.get_object("listcopystg")
        treecopystg = self.builder.get_object("treecopystg")
        # Get the name and description
        name = self.builder.get_object("txtcopyvmname").get_text()
        desc = self.builder.get_object("txtcopyvmdesc").get_text()
        full = False
        # Check if "fast clone" is selected or "full clone"
        if self.builder.get_object("radiofullclone").get_active():
            full = True
        # Get the selected storage
        selection = treecopystg.get_selection()
        if selection.get_selected()[1] == None:
            iter = listcopystg.get_iter((0,1))
        else:
            iter = selection.get_selected()[1]
        sr = listcopystg.get_value(iter, 1)
        # Call to function to copy the vm
        self.xc_servers[self.selected_host].copy_vm(self.selected_ref, name, desc, sr, full)
        self.builder.get_object("windowcopyvm").hide()

    def on_btimportaddnetwork_clicked(self, widget, data=None):
        """
        Function called whe you press add a new network when you are doing "import" process
        """
        treeimportservers = self.builder.get_object("treeimportservers")
        listimportservers = self.builder.get_object("listimportservers")
        selection = treeimportservers.get_selection()
        host = listimportservers.get_value(selection.get_selected()[1], 3)
        listimportnetworks = self.builder.get_object("listimportnetworks")
        # Get first network as default and network ref
        network = self.xc_servers[host].first_network()
        network_ref = self.xc_servers[host].first_network_ref()
        # Add to network list
        listimportnetworks.append(["interface " + str(listimportnetworks.__len__()),
                "auto-generated",
                network, network_ref
            ])
    def on_btimportdeletenetwork_clicked(self, widget, data=None):
        """
        Function called whe you press delete a network when you are doing "import" process
        """
        listimportnetworks = self.builder.get_object("listimportnetworks")
        treeimportnetworks = self.builder.get_object("treeimportnetworks")
        selection = treeimportnetworks.get_selection()
        # Get selected
        iter = selection.get_selected()[1]
        # And remove from list
        listimportnetworks.remove(iter)
 

    def on_dialogdelete_cancel_activate(self, widget, data=None):
        """
        Function called when you cancel the "delete vm" confirmation
        """
        self.builder.get_object("dialogdeletevm").hide()
    def on_dialogdelete_accept_activate(self, widget, data=None):
        """
        Function called when you cancel the "delete vm" confirmation
        """
        # Get if "delete disks" and "delete snapshots" are active
        delete_vdi = self.builder.get_object("dialogdelete_vdi").get_active()
        delete_snap = self.builder.get_object("dialogdelete_snap").get_active()
        # Remove first from list
        self.treestore.remove(self.selected_iter)
        # And late remove from server
        self.xc_servers[self.selected_host].destroy_vm(self.selected_ref, delete_vdi, delete_snap)
        # And hide confirmation window
        self.builder.get_object("dialogdeletevm").hide()
    def on_filechooserimportvm_file_set(self, widget, data=None):
        """"
        Function called when you select a file to import
        """
        # Enable "Next >" button because filename was selected
        self.builder.get_object("nextvmimport").set_sensitive(True)
    def on_tabboximport_switch_page(self, widget, data=None, data2=None):
        """
        Function called when you change the page in "import vm" process
        """
        # Set colors..
        white = gtk.gdk.color_parse("white")
        blue = gtk.gdk.color_parse("#d5e5f7")
        for i in range(0,5):
             self.builder.get_object("eventimport" + str(i)).modify_bg(gtk.STATE_NORMAL, white)
        self.builder.get_object("eventimport" + str(data2)).modify_bg(gtk.STATE_NORMAL, blue)
        # If page is the first, you cannot go to previous page
        self.builder.get_object("previousvmimport").set_sensitive(data2 != 0)
    def on_nextvmimport_clicked(self, widget, data=None):
        """
        Function called when you press "Next" button on Import VM process
        """
        # Get the current page
        page = self.builder.get_object("tabboximport").get_current_page()
        # Move the tabbox to next tab
        self.builder.get_object("tabboximport").set_current_page(page+1)
        if page+1 == 1:
            # If next page is the second.. 
            treeimportservers = self.builder.get_object("treeimportservers")
            selection = treeimportservers.get_selection().get_selected()[1]
            # If in possible servers to import there is one element, enable "Next" button
            self.builder.get_object("nextvmimport").set_sensitive(selection != None)
        if page+1 == 2:
            # If next page is the third..
            treeimportservers = self.builder.get_object("treeimportservers")
            listimportservers = self.builder.get_object("listimportservers")
            selection = treeimportservers.get_selection()
            # Get selected host
            host = listimportservers.get_value(selection.get_selected()[1], 3)
            listimportstg = self.builder.get_object("listimportstg")
            # Fill the list of possible storage to import the VM, returns default storage position
            defstg = self.xc_servers[host].fill_importstg(listimportstg)
            treeimportstg = self.builder.get_object("treeimportstg")
            # Select the "default storage"
            treeimportstg.set_cursor((defstg, ), treeimportstg.get_column(0))
            treeimportstg.get_selection().select_path((defstg, ))
            listimportnetworks = self.builder.get_object("listimportnetworks")
            listimportnetworkcolumn = self.builder.get_object("listimportnetworkcolumn")
            # Fill the list the networks with option "automatically add to new servers"
            self.xc_servers[host].fill_list_networks(listimportnetworks, listimportnetworkcolumn)
            # If page is the third, button is called "Import >"
            widget.set_label("Import >")
        else:
            # If next page is different to third, the button is called "Next >"
            widget.set_label("Next >")
        if page+1 == 3:
            # If page is the fourth..
            filename = self.builder.get_object("filechooserimportvm").get_filename()
            treeimportservers = self.builder.get_object("treeimportservers")
            listimportservers = self.builder.get_object("listimportservers")
            selection = treeimportservers.get_selection()
            # Get selected host
            host = listimportservers.get_value(selection.get_selected()[1], 3)
            treeimportstg = self.builder.get_object("treeimportstg")
            listimportstg = self.builder.get_object("listimportstg")
            selection = treeimportstg.get_selection()
            # Get selected storage
            sr = listimportstg.get_value(selection.get_selected()[1], 1)
            self.xc_servers[host].halt_import = False
            # Show a progress with import progerss
            self.builder.get_object("wprogressimportvm").show()
            # And begin to import the VM
            self.xc_servers[host].thread_import_vm(sr, filename)
        if page+1 == 4:
            # If page is the last..
            widget.set_sensitive(False)
            # Then enable "finish" button
            self.builder.get_object("finishvmimport").set_sensitive(True)
    def on_previousvmimport_clicked(self, widget, data=None):
        """"
        Function called when you press "< Previous" button
        """
        page = self.builder.get_object("tabboximport").get_current_page()
        # Move to previous tab
        self.builder.get_object("tabboximport").set_current_page(page-1)
        # And set next button with correct label
        self.builder.get_object("nextvmimport").set_label("Next >")

    def on_cancelvmimport_clicked(self, widget, data=None):
        """
        Function called when you cancel the import vm process
        """
        treeimportservers = self.builder.get_object("treeimportservers")
        listimportservers = self.builder.get_object("listimportservers")
        selection = treeimportservers.get_selection()
        if selection.get_selected()[1]:
            # Get the selected host
            host = listimportservers.get_value(selection.get_selected()[1], 3)
            # Stop the import
            self.xc_servers[host].halt_import = False
        # hide the window
        self.builder.get_object("vmimport").hide()
    def on_finishvmimport_clicked(self, widget, data=None):
        """
        Function called when you press the "Finish" button
        """
        treeimportservers = self.builder.get_object("treeimportservers")
        listimportservers = self.builder.get_object("listimportservers")
        selection = treeimportservers.get_selection()
        host = listimportservers.get_value(selection.get_selected()[1], 3)
        vif_cfg = {
            'name': 'API_VIF',
            'type': 'ioemu',
            'device': '0',
            'network': '',
            'MAC': '',
            'MTU': '0',
            "qos_algorithm_type":   "ratelimit",
            "qos_algorithm_params": {},
            "other_config":         {}
        }

        selection = self.builder.get_object("treeimportnetworks").get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.select_all()
        model, selected = selection.get_selected_rows()
        iters = [model.get_iter(path) for path in selected]
        # For each network... 
        for iter in iters:
            network = self.builder.get_object("listimportnetworks").get_value(iter, 3)
            vm  = self.xc_servers[host].import_ref
            # Add to new imported VM
            self.xc_servers[host].vm_add_interface(vm, network, None, "0")
            # Sleep 1 second between action
            time.sleep(1)
        # Set if "file is a imported template" or/and "start after import"
        self.xc_servers[host].import_start = self.builder.get_object("checkstartvmafterimport").get_active()
        self.xc_servers[host].import_make_into_template = self.builder.get_object("radioexportedtpl").get_active()
        # Hide the window
        selection.set_mode(gtk.SELECTION_SINGLE)
        self.builder.get_object("vmimport").hide()
 
    def on_networkcolumn1_changed(self, widget, data=None, data2=None):
        """
        Function called when you change the network combo for selected interface
        """
        treeimportnetworks = self.builder.get_object("treeimportnetworks")
        listimportnetworks = self.builder.get_object("listimportnetworks")
        listnetworkcolumn = self.builder.get_object("listimportnetworkcolumn")
        selection = treeimportnetworks.get_selection()
        iter = selection.get_selected()[1]
        listimportnetworks.set_value(iter, 2,
             listnetworkcolumn.get_value(data2, 0))
        listimportnetworks.set_value(iter, 3,
             listnetworkcolumn.get_value(data2, 1))                                                                 
    def on_radiofastclone_toggled(self, widget, data=None):
        """
        Function called when you toggle "fast clone" or "full clone"
        """
        if widget.get_active():
            if gtk.Buildable.get_name(widget) == "radiofastclone":
                self.builder.get_object("treecopystg").set_sensitive(False)
            else:
                self.builder.get_object("treecopystg").set_sensitive(True)

