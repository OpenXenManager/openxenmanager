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

class oxcWindowHostNics:
    """
    Class to manage "nics" tab on host
    """
    # Host NIC tab 
    def on_treehostnics_button_press_event(self, widget, event):
        """
        Function called when you select a nic on "host nics"
        """
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = widget.get_path_at_pos(x, y)
        if pthinfo is not None:
           path, col, cellx, celly = pthinfo
           # Get selected nic
           iter = self.builder.get_object("listhostnics").get_iter(path)
           ref = self.builder.get_object("listhostnics").get_value(iter, 8)
           nic = self.xc_servers[self.selected_host].all_pif[ref]
           # Check if already is on a bond
           if len(nic['bond_master_of']):
               # If is already is on a bond enable remove button
               self.builder.get_object("bthostnicremove").set_sensitive(True)
           else:
               # If is already is on a bond disable remove button
               self.builder.get_object("bthostnicremove").set_sensitive(False)

    def on_bthostnicreadd_clicked(self, widget, data=None):
        """
        Function called when you press on "Add bond" button
        """
        # Show "Add Bond" window
        self.builder.get_object("addbond").show()
        # Hide below frame showing nic information
        self.builder.get_object("framenic").hide()
        listavailnics = self.builder.get_object("listavailnics")
        listbondnics = self.builder.get_object("listbondnics")
        # Fill the possible nics to create bond
        self.xc_servers[self.selected_host].fill_available_nics(listavailnics, listbondnics)

    def on_bthostnicremove_clicked(self, widget, data=None):
        """
        Function called when you press on "Delete bond" button
        """
        # Show confirmation dialog
        self.builder.get_object("dialogdeletehostnic").show()
    def on_acceptdialogdeletehostnic_clicked(self, widget, data=None):
        """
        Function called when you accept delete nic confirmation dialog
        """
        listhostnics = self.builder.get_object("listhostnics")
        treehostnics = self.builder.get_object("treehostnics")
        # Get the selected NIC
        selection = treehostnics.get_selection()
        if selection.get_selected()[1] != None:
            iter = selection.get_selected()[1]
            ref = listhostnics.get_value(iter,8)
            # Call to delete nic function
            self.xc_servers[self.selected_host].delete_nic(ref, self.selected_ref)

        self.builder.get_object("dialogdeletehostnic").hide()
    def on_canceldialogdeletehostnic_clicked(self, widget, data=None):
        """
        Function called when you cancel delete nic confirmation dialog
        """
        self.builder.get_object("dialogdeletehostnic").hide()

    # Add Bond Window
    def on_treeavailnics_button_press_event(self, widget, event):
        """
        Function called when you press on available nics to create a bond
        """
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = widget.get_path_at_pos(x, y)
        if pthinfo is not None:
           path, col, cellx, celly = pthinfo
           listbondnics = self.builder.get_object("listbondnics")
           listavailnics = self.builder.get_object("listavailnics")
           # Get selected available NIC
           iter = self.builder.get_object("listavailnics").get_iter(path)
           ref = listavailnics.get_value(iter, 0)
           # Show all information for selected nic
           self.xc_servers[self.selected_host].fill_nic_info(ref)
           # Show nic information frame
           self.builder.get_object("framenic").show()
           if listbondnics.__len__() < 2:
               # If number of selected nics to create bond are less than 2, enable "Add >" button
               self.builder.get_object("btaddbondednic").set_sensitive(
                       listavailnics.get_value(iter, 3))
           else:
               # Else disable "add" button
               self.builder.get_object("btaddbondednic").set_sensitive(False)
           # Disable "< Remove" nic button
           self.builder.get_object("btrembondednic").set_sensitive(False)
    def on_btaddbondednic_clicked(self, widget, data=None):
        """
        Function called when you press on "Add >" button to move from available to selected nic
        """
        treeavailnics = self.builder.get_object("treeavailnics")
        listavailnics = self.builder.get_object("listavailnics")
        listbondnics = self.builder.get_object("listbondnics")
        # Get selected NIC
        selection = treeavailnics.get_selection()
        if selection.get_selected()[1] != None:
            iter = selection.get_selected()[1]
            # Append to "selected nics" tree
            listbondnics.append([listavailnics.get_value(iter,0), listavailnics.get_value(iter,1)])
            # Remove from "available nics" tree
            listavailnics.remove(iter)
        # If selected nics tree has two elements then enable "accept" (create bond) button
        self.builder.get_object("btacceptaddbond").set_sensitive(listbondnics.__len__() == 2)
    def on_btrembondednic_clicked(self, widget, data=None):
        """
        Function called when you press on "< Remove" button to move from available to selected nic
        """
        treebondnics = self.builder.get_object("treebondnics")
        listavailnics = self.builder.get_object("listavailnics")
        listbondnics = self.builder.get_object("listbondnics")
        selection = treebondnics.get_selection()
        # Get selected NIC
        if selection.get_selected()[1] != None:
            iter = selection.get_selected()[1]
            ref = listbondnics.get_value(iter,0)
            name = listbondnics.get_value(iter,1)
            # Append to "available nics" tree
            listavailnics.append([ref, name, None,True])
            # Remove from "selected nics" tree
            listbondnics.remove(iter)
        # Disable "accept" (create bond) button because available nics is not 2 
        self.builder.get_object("btacceptaddbond").set_sensitive(False)
    def on_treebondnics_button_press_event(self, widget, event):
        """
        Function called when you select a bond on "bonded nics" (selected nics) to create a bond
        """
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = widget.get_path_at_pos(x, y)
        if pthinfo is not None:
           path, col, cellx, celly = pthinfo
           listbondnics = self.builder.get_object("listbondnics")
           iter = listbondnics.get_iter(path)
           # Get selected NIC on "bonded nics" tree
           ref = listbondnics.get_value(iter, 0)
           # Fill NIC info
           self.xc_servers[self.selected_host].fill_nic_info(ref)
           # Show frame and disable "Add >" button and enable "< Remove Button"
           self.builder.get_object("framenic").show()
           self.builder.get_object("btaddbondednic").set_sensitive(False)
           self.builder.get_object("btrembondednic").set_sensitive(True)
    def on_btacceptaddbond_clicked(self, widget, data=None):
        """
        Function called when you accept "create bond" window
        """
        listbondnics = self.builder.get_object("listbondnics")
        # Get two selected nics on right tree
        iter = listbondnics.get_iter((0,0))
        ref = listbondnics.get_value(iter, 0)
        name = listbondnics.get_value(iter, 1)
        iter = listbondnics.get_iter((1,0))
        ref2 = listbondnics.get_value(iter, 0)
        name2 = listbondnics.get_value(iter, 1)
        # Get if bond will be automatically add to new servers
        auto = self.builder.get_object("checkautoaddbond").get_active()
        # Call to function to create a new bond
        self.xc_servers[self.selected_host].create_bond(ref, ref2, name, name2,auto)
        # Hide "new bond" window
        self.builder.get_object("addbond").hide()
    def on_btcanceladdbond_clicked(self, widget, data=None):
        """
        Function called when you cancel "create bond" window
        """
        self.builder.get_object("addbond").hide()

