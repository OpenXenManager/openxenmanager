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
from threading import Thread
class oxcWindowVMSnapshot:
    """
    Class to manage "snapshots" of a VM
    """
    def on_btcancelsnapshotname_clicked(self, widget, data=None):
        """
        Function called when you cancel the "set snapshot name" dialog
        """
        # Hide dialog
        self.builder.get_object("dialogsnapshotname").hide()
    def on_btacceptsnapshotname_clicked(self, widget, data=None):
        """
        Function called when you cancel the "set snapshot name" dialog
        """
        # Call to take_snapshot function with typed name
        self.xc_servers[self.selected_host].take_snapshot(self.selected_ref, self.builder.get_object("snapshotname").get_text())
        # Hide dialog
        self.builder.get_object("dialogsnapshotname").hide()
    def on_bttakesnapshot_clicked(self, widget, data=None):
        """
        Function called when you press "Take snapshot"
        """
        # Empty the name of snapshot
        self.builder.get_object("snapshotname").set_text("")
        # Show the dialog asking snapshot name
        self.builder.get_object("dialogsnapshotname").show()
    def on_m_snap_newvm_activate(self, widget, data=None):
        # print self.selected_snap_ref
        # TODO -> select vm with name_label
        """
        Function called when you press "Take snapshot"
        """
        self.on_m_newvm_activate(widget, data)
    def on_m_snap_createtpl_activate(self, widget, data=None):
        """
        Function called when you press "create template from snapshot"
        """
        self.builder.get_object("snaptplname").set_text("Template from snapshot '" + \
            self.xc_servers[self.selected_host].all_vms[self.selected_snap_ref]['name_label'] + "'")
        # Show the dialog asking the new template name
        self.builder.get_object("dialogsnaptplname").show()
    def on_m_snap_delete_activate(self, widget, data=None):
        """
        Function called when you press "delete snapshot"
        """
        # Show the confirmation dialog
        self.builder.get_object("dialogsnapshotdelete").show()
    def on_m_snap_export_activate(self, widget, data=None):
        """
        Function called when you press "export snapshot"
        """
        # Set default name
        self.export_snap = True
        self.filesave.set_current_name(self.xc_servers[self.selected_host].all_vms[self.selected_snap_ref]['name_label'] + ".xva")
        # Show the choose dialog
        self.filesave.show()

    def on_m_snap_export_vm_activate(self, widget, data=None):
        """
        Function called when you press "export snapshot"
        """
        # Set default name
        self.export_snap_vm = True
        self.filesave.set_current_name(self.xc_servers[self.selected_host].all_vms[self.selected_snap_ref]['name_label'] + ".xva")
        # Show the choose dialog
        self.filesave.show()

    def on_btacceptsnapshotdelete_clicked(self, widget, data=None):
        """
        Function called when you accept the "delete snapshot" confirmation dialog
        """
        # Delete the snapshot
        Thread(target=self.xc_servers[self.selected_host].delete_snapshot, args=(self.selected_snap_ref, self.selected_ref)).start()
        # And hide the confirmation dialog
        self.builder.get_object("dialogsnapshotdelete").hide()
    def on_btcancelsnapshotdelete_clicked(self, widget, data=None):
        """
        Function called when you cancel the "delete snapshot" confirmation dialog
        """
        # Hide the confirmation dialog
        self.builder.get_object("dialogsnapshotdelete").hide()

    def on_btacceptsnaptplname_clicked(self, widget, data=None):
        """
        Function called when you accept the "specify name" dialog to create a template from snapshot
        """
        # Call to function to create a new template from snapshot
        self.xc_servers[self.selected_host].create_template_from_snap(self.selected_snap_ref, \
           self.builder.get_object("snaptplname").get_text())
        # Hide the dialog
        self.builder.get_object("dialogsnaptplname").hide()
    def on_btcancelsnaptplname_clicked(self, widget, data=None):
        """
        Function called when you cancel the "specify name" dialog to create a template from snapshot
        """
        # Hide the dialog
        self.builder.get_object("dialogsnaptplname").hide()
    def on_treevmsnapshots_button_press_event(self, widget, event):
        """
        Function called when you press with the mouse inside "snapshots" tree
        """
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = widget.get_path_at_pos(x, y)
        if pthinfo is not None:
           path, col, cellx, celly = pthinfo
           widget.grab_focus()
           widget.set_cursor( path, col, 0)
           iter = self.builder.get_object("listvmsnapshots").get_iter(path)
           self.builder.get_object("btsnapnewvm").set_sensitive(iter != None)
           self.builder.get_object("btsnapcreatetpl").set_sensitive(iter != None)
           self.builder.get_object("btsnapexport").set_sensitive(iter != None)
           self.builder.get_object("btsnapdelete").set_sensitive(iter != None)
           # Set in a global variable the selected snapshot
           self.selected_snap_ref  = self.builder.get_object("listvmsnapshots").get_value(iter, 0)
           ops = self.xc_servers[self.selected_host].all_vms[self.selected_snap_ref]['allowed_operations']
           self.builder.get_object("btsnaprevert").set_sensitive("revert" in ops)
           if event.button == 3:
               # If button pressed is the right.. 
               # Show a menu with snapshot options
               menu_snapshot = self.builder.get_object("menu_snapshot")
               menu_snapshot.popup( None, None, None, event.button, time)

    def on_btsnaprevert_clicked(self, widget, data=None):
        """
        Function called when you press "Revert to..." on a snapshot
        """
        self.builder.get_object("dialogrevert").show()

    def on_canceldialogrevert_clicked(self, widget, data=None):
        """
        Function called when you cancel revert dialog
        """
        self.builder.get_object("dialogrevert").hide()

    def on_acceptdialogrevert_clicked(self, widget, data=None):
        """
            Function called when you cancel revert dialog
        """
        self.xc_servers[self.selected_host].revert_to_snapshot(self.selected_ref, self.selected_snap_ref) 
        self.builder.get_object("dialogrevert").hide()

