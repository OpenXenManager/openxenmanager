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
import re
class oxcWindowHostNetwork:
    """
    Class to manage "network" tab on host
    """
    def on_treehostnetwork_button_press_event(self, widget, event):
        """
        Function called when button is pressed on network treeview
        """
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = widget.get_path_at_pos(x, y)
        if pthinfo is not None:
           path, col, cellx, celly = pthinfo
           iter = self.builder.get_object("listhostnetwork").get_iter(path)
           # Get the network reference
           ref = self.builder.get_object("listhostnetwork").get_value(iter, 7)
           # Get all pifs on selected network
           pifs = self.xc_servers[self.selected_host].all_network[ref]['PIFs']
           # By default all networks could be removed
           self.builder.get_object("bthostnetworkremove").set_sensitive(True)
           for pif in pifs:
               if self.xc_servers[self.selected_host].all_pif[pif]['physical'] == True:
                   # Except if network is physical
                   self.builder.get_object("bthostnetworkremove").set_sensitive(False)
                   break
    def on_bthostnetworkadd_clicked(self, widget, data=None):
        """
        Function called when "Add Network..." is pressed
        """
        # Show new network dialog
        self.builder.get_object("newnetwork").show()
        # Set default texts
        self.builder.get_object("txtnetworkname").set_text("New Network")
        self.builder.get_object("txtnetworkdesc").set_text("")
        listnetworknic = self.builder.get_object("listnetworknic")
        # Fill the possible nics for this network, returns the first vlan free
        vlan = self.xc_servers[self.selected_host].fill_listnetworknic(listnetworknic)
        # Select the first as default
        self.builder.get_object("combonetworknic").set_active(0)
        # Set the first vlan free
        self.builder.get_object("spinnetworkvlan").set_value(vlan)

    def on_acceptdialogdeletehostnetwork_clicked(self, widget, data=None):
        """
        Function called when you accept the confirmation dialog to delete a network
        """
        listhostnetwork = self.builder.get_object("listhostnetwork")
        treehostnetwork = self.builder.get_object("treehostnetwork")
        # Get selected network
        selection = treehostnetwork.get_selection()
        if selection.get_selected()[1] != None:
            iter = selection.get_selected()[1]
            ref = listhostnetwork.get_value(iter,7)
            # Call to function to remove selected network
            self.xc_servers[self.selected_host].delete_network(ref, self.selected_ref)
        # Hide the confirmation dialog
        self.builder.get_object("dialogdeletehostnetwork").hide()
    def on_canceldialogdeletehostnetwork_clicked(self, widget, data=None):
        """
        Function called when you cancel the confirmation dialog to delete a network
        """
        # Hide the confirmation dialog
        self.builder.get_object("dialogdeletehostnetwork").hide()
    def on_acceptnewnetwork_clicked(self, widget, data=None):
        """
        Function called when you accept the "new network" window
        """ 
        if self.builder.get_object("radioexternalnetwork").get_active():
            # External Network
            # Get text typed
            name = self.builder.get_object("txtnetworkname").get_text()
            desc = self.builder.get_object("txtnetworkdesc").get_text()
            auto = self.builder.get_object("checkautonetwork").get_active()
            listnetworknic = self.builder.get_object("listnetworknic")
            combonetworknic = self.builder.get_object("combonetworknic")
            iter = listnetworknic.get_iter((combonetworknic.get_active(),0))
            # Get the pif selected
            pif = self.builder.get_object("listnetworknic").get_value(iter,0)
            # And the vlan selected
            vlan = int(self.builder.get_object("spinnetworkvlan").get_value())
            # Call to function to create a external network
            self.xc_servers[self.selected_host].create_external_network(name, desc, auto,  pif, vlan)
        else:
            # Internal Network
            # Get text typed
            name = self.builder.get_object("txtnetworkname").get_text()
            desc = self.builder.get_object("txtnetworkdesc").get_text()
            auto = self.builder.get_object("checkautonetwork").get_active()
            # Call to function to create a internal network
            self.xc_servers[self.selected_host].create_internal_network(name, desc, auto)
        self.builder.get_object("newnetwork").hide()
    def on_cancelnewnetwork_clicked(self, widget, data=None):
        """
        Function called when you accept the "new network" dialog
        """ 
        self.builder.get_object("newnetwork").hide()
    def on_spinnetworkvlan_change_value(self, widget):
        """
        Function called when you changes the value on "vlan"
        """ 
        data = self.builder.get_object("spinnetworkvlan").get_value()
        # Checks if selected vlan is available
        if self.xc_servers[self.selected_host].is_vlan_available(data):
            # If is available hide the alert text
            self.builder.get_object("lblvlaninuse").hide()
            # And enable accept button
            self.builder.get_object("acceptnewnetwork").set_sensitive(True)
        else:
            # If is unavailable show the alert text
            self.builder.get_object("lblvlaninuse").show()
            # And disable accept button
            self.builder.get_object("acceptnewnetwork").set_sensitive(False)
    def on_bthostnetworkremove_clicked(self, widget, data=None):
        """
        Function called when you click in "Remove network" button on selected network
        """ 
        self.builder.get_object("dialogdeletehostnetwork").show()

    def on_canceladdnetwork_clicked(self, widget, data=None):
        """
        Function called when you cancel "Add network" dialog
        """ 
        self.builder.get_object("dialogaddnetwork").hide()

    def on_radiointernalnetwork_toggled(self, widget, data=None):
        """
        Function called when you select "create external network" or "create internal network"
        """ 
        # If external is selected, enable follow widgets
        for wid in ["label255", "label256", "combonetworknic", "label257", \
                "label258", "spinnetworkvlan"]:
                self.builder.get_object(wid).set_sensitive(self.builder.get_object("radioexternalnetwork").get_active())

