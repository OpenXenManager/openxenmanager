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

class oxcWindowVMStorage:
    """
    Class to manage storage tab in a VM
    """
    def on_btcancelattachdisk_clicked(self, widget, data=None):
        """
        Function called when you cancel the "attack disk" window
        """
        # Hide the dialog
        self.builder.get_object("vmattachdisk").hide()
    def on_btacceptattachdisk_clicked(self, widget, data=None):
        """
        Function called when you accept the "attack disk" window
        """
        treeattachdisk = self.builder.get_object("treeattachdisk")
        listattachdisk = self.builder.get_object("listattachdisk")
        iter_ref= treeattachdisk.get_selection().get_selected()[1]
        # Get if "read only" is checked
        ro =  self.builder.get_object("checkattachdisk").get_active()
        # Get selected disk
        disk = listattachdisk.get_value(iter_ref, 1)
        vm = self.selected_ref
        # Attack the selected disk 
        self.xc_servers[self.selected_host].attach_disk_to_vm(vm, disk, ro)
        # Hide the dialog
        self.builder.get_object("vmattachdisk").hide()

    def on_cancelnewvmdisk_clicked(self, widget, data=None):
        """
        Function called when you cancel the "new disk" window
        """
        # Hide the dialog
        self.builder.get_object("newvmdisk").hide()
    def on_addnewvmstorage_clicked(self, widget, data=None):
        """
        Function called when you press "add new storage"
        """
        self.newvmdata['storage_editing'] = False
        # Show the dialog
        self.builder.get_object("newvmdisk").show()
    def on_btstorageattach_clicked(self, widget, data=None):
        """
        Function called when you press "Attach disk"
        """
        self.builder.get_object("vmattachdisk").show()
        listattachdisk = self.builder.get_object("listattachdisk")
        # Fill the possible disks to attach
        self.xc_servers[self.selected_host].fill_vm_storageattach(listattachdisk)
        # Expand list
        self.builder.get_object("treeattachdisk").expand_all()
    def on_btstoragedelete_clicked(self, widget, data=None):
        """
        Function called when you press "Delete disk"
        """
        # Show a confimration dialog
        self.builder.get_object("dialogdeletedisk").show()
    def on_canceldeletedisk_clicked(self, widget, data=None):
        """
        Function called when you cancel "delete disk" confirmation dialog
        """
        self.builder.get_object("dialogdeletedisk").hide()
    def on_acceptdeletedisk_clicked(self, widget, data=None):
        """
        Function called when you accept "delete disk" confirmation dialog
        """
        treevmstorage = self.builder.get_object("treevmstorage")
        listvmstorage = self.builder.get_object("listvmstorage")
        selection = treevmstorage.get_selection()
        if selection.get_selected()[1] == None:
            self.builder.get_object("btstorageproperties").set_sensitive(False)
            iter_ref= listvmstorage.get_iter((0,))
        else:
            self.builder.get_object("btstorageproperties").set_sensitive(True)
            iter_ref= selection.get_selected()[1]
        # Get selected disk
        vdi = listvmstorage.get_value(iter_ref, 9)
        # Delete it
        self.xc_servers[self.selected_host].delete_vdi(vdi, self.selected_ref)
        # Select the first of a list
        treevmstorage.set_cursor((0,), treevmstorage.get_column(0))
        treevmstorage.get_selection().select_path((0, 0))
        # Hide the dialog
        self.builder.get_object("dialogdeletedisk").hide()
    def on_btstoragedeactivate_clicked(self, widget, data=None):
        """
        Function called when you press "Deactivate"/"Activate" button
        """
        listvmstorage = self.builder.get_object("listvmstorage")
        treevmstorage = self.builder.get_object("treevmstorage")
        # Get selected disk
        iter_ref= treevmstorage.get_selection().get_selected()[1]
        # Dettach disk
        if widget.get_label() == "Activate":
            self.xc_servers[self.selected_host].vm_storageplug(listvmstorage.get_value(iter_ref,10))
        else:
            self.xc_servers[self.selected_host].vm_storageunplug(listvmstorage.get_value(iter_ref,10))

    def on_btstoragedetach_clicked(self, widget, data=None):
        """
        Function called when you press "Detach" button
        """
        listvmstorage = self.builder.get_object("listvmstorage")
        treevmstorage = self.builder.get_object("treevmstorage")
        # Get selected disk
        iter_ref= treevmstorage.get_selection().get_selected()[1]
        # Dettach disk
        self.xc_servers[self.selected_host].vm_storagedetach(listvmstorage.get_value(iter_ref,10))

    def on_treeattachdisk_cursor_changed(self, widget, data=None):
        """
        Function called when you select a disk to attach
        """
        treeattachdisk = self.builder.get_object("treeattachdisk")
        listattachdisk = self.builder.get_object("listattachdisk")
        iter_ref= treeattachdisk.get_selection().get_selected()[1]
        # Element fourth from list indicates if disk could be used to attach
        # Then enable or disable button depends its value
        self.builder.get_object("btacceptattachdisk").set_sensitive(listattachdisk.get_value(iter_ref, 4))
    def on_btstorageproperties_clicked(self, widget, data=None):
        """
        Function not used
        """
        listvmstorage = self.builder.get_object("listvmstorage")
        treevmstorage = self.builder.get_object("treevmstorage")
        iter_ref= treevmstorage.get_selection().get_selected()[1]
        ref = listvmstorage.get_value(iter_ref,10)
        print self.xc_servers[self.selected_host].get_allowed_vbd_devices(self.selected_ref)


    def on_combovmstoragedvd_changed(self, widget, data=None):
        """
        Function called when you change the "DVD Drive" combobox
        """
        if widget.get_active_iter() != None and self.set_active == False:
            # If a element is selected..
            # Get the element
            vdi = self.builder.get_object("listvmstoragedvd").get_value(widget.get_active_iter(), 1)
            # And call to function "set_vm_dvd" to insert into VM
            self.xc_servers[self.selected_host].set_vm_dvd(self.selected_ref, vdi)
    def on_btvmaddstorage_clicked(self, widget, data=None):
        """
        Function called when you press the "New disk" button
        """
        vmaddnewdisk = self.builder.get_object("vmaddnewdisk")
        # Set a default name
        self.builder.get_object("vmaddnewdisk_name").set_text("New virtual disk on " + self.selected_name)
        self.builder.get_object("vmaddnewdisk_desc").set_text("")
        listnewvmdisk1 = self.builder.get_object("listnewvmdisk1")
        # Fill the possible storage and return the defalt
        defsr = self.xc_servers[self.selected_host].fill_listnewvmdisk(listnewvmdisk1, self.selected_host)
        # Set the cursor on default storage
        treenewvmstorage1 = self.builder.get_object("treenewvmdisk1")
        treenewvmstorage1.set_cursor((defsr,), treenewvmstorage1.get_column(0))
        treenewvmstorage1.get_selection().select_path((defsr, 0))
        # Set as default 5GB
        self.builder.get_object("disksize2").set_value(float(5))
        # Show the window
        vmaddnewdisk.show()
    def on_cancelvmaddnewdisk_clicked(self, widget, data=None):
        """
        Function called when you press "cancel" button on "add new disk" window
        """
        self.builder.get_object("vmaddnewdisk").hide()
    def on_treevmstorage_cursor_changed(self, widget, data=None):
        """
        Function called when you select a storage on storage tree
        """
        treevmstorage = self.builder.get_object("treevmstorage")
        listvmstorage = self.builder.get_object("listvmstorage")
        selection = treevmstorage.get_selection()
        # If some storage is selected, then enable "properties window"
        if selection.get_selected()[1] == None:
            self.builder.get_object("btstorageproperties").set_sensitive(False)
            iter_ref= listvmstorage.get_iter((0,))
        else:
            self.builder.get_object("btstorageproperties").set_sensitive(True)
            iter_ref= selection.get_selected()[1]
        # Get selected disk (vdi)
        vdi = listvmstorage.get_value(iter_ref, 9)
        vdi_info = self.xc_servers[self.selected_host].all_vdi[vdi]
        vbd_info = self.xc_servers[self.selected_host].all_vbd[vdi_info['VBDs'][0]]
        # Depends the type of disk and if is attached, enable or disable buttons

        if vdi_info['type'] == "user":
            self.builder.get_object("btstoragedeactivate").set_sensitive(True)
            if vbd_info['currently_attached']:
                self.builder.get_object("btstoragedeactivate").set_label("Deactivate")
            else:
                self.builder.get_object("btstoragedeactivate").set_label("Activate")
                self.builder.get_object("btstoragedetach").set_sensitive(True)
        else:
            self.builder.get_object("btstoragedeactivate").set_sensitive(False)
            self.builder.get_object("btstoragedetach").set_sensitive(False)

        if vdi_info['allowed_operations'].count("destroy") > 0:
            self.builder.get_object("btstoragedelete").set_sensitive(True)
        else:
            self.builder.get_object("btstoragedelete").set_sensitive(False)

    def on_treevmnetwork_cursor_changed(self, widget, data=None):
        """
        Function called when you select a storage on storage tree
        """
        treevmnetwork = self.builder.get_object("treevmnetwork")
        listvmnetwork = self.builder.get_object("listvmnetwork")
        selection = treevmnetwork.get_selection()
        # If some storage is selected, then enable "properties window"
        if selection.get_selected()[1] == None:
            self.builder.get_object("btpropertiesinterface").set_sensitive(False)
            self.builder.get_object("btremoveinterface").set_sensitive(False)
            iter_ref= listvmnetwork.get_iter((0,))
        else:
            self.builder.get_object("btpropertiesinterface").set_sensitive(True)
            self.builder.get_object("btremoveinterface").set_sensitive(True)
            iter_ref = selection.get_selected()[1]
        # Get selected disk (vdi)
        vif = listvmnetwork.get_value(iter_ref, 6)
        vif_info = self.xc_servers[self.selected_host].all_vif[vif]
        unplug = vif_info["allowed_operations"].count("unplug")
        self.builder.get_object("btpropertiesinterface").set_sensitive(unplug or self.selected_state == "Halted")
        self.builder.get_object("btremoveinterface").set_sensitive(unplug or self.selected_state == "Halted")

    def on_acceptvmaddnewdisk_clicked(self, widget, data=None):
        """
        Function called when you accept the "new disk" window
        """
        treenewvmstorage = self.builder.get_object("treenewvmdisk1")
        listnewvmdisk1 = self.builder.get_object("listnewvmdisk1")
        selection = treenewvmstorage.get_selection()
        # Get selected storage
        if selection.get_selected()[1] == None:
            iter_ref= listnewvmdisk1.get_iter((0,1))
        else:
            iter_ref= selection.get_selected()[1]
        name = self.builder.get_object("vmaddnewdisk_name").get_text()
        description = self.builder.get_object("vmaddnewdisk_desc").get_text()
        sr = listnewvmdisk1.get_value(iter_ref, 4)
        virtual_size = int(self.builder.get_object("disksize2").get_value()*1024*1024*1024)
        # Add new disk with the selected options (size, name, description..)
        self.xc_servers[self.selected_host].add_disk_to_vm(
            name, description, sr, virtual_size, self.selected_uuid,
            self.selected_ref)
        self.builder.get_object("vmaddnewdisk").hide()


