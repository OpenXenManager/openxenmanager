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
import hashlib
import gtk
import xml.dom.minidom

class oxcWindowProperties:
    """
    Class to manage the properties window (vm, template, host, network, storage..) and window options
    """
    changes = {}
    selected_prop_path = None
    freedevices = {}
    other_config = None
    def on_addcustomfield_clicked(self, widget, data=None):
        """
        Function called when you press "Add" on custom fields window
        """
        if self.builder.get_object("namecustomfields").get_text():
            combocustomfields = self.builder.get_object("combocustomfields")
            listcombocustomfields = self.builder.get_object("listcombocustomfields")
            listcustomfields = self.builder.get_object("listcustomfields")
            name = self.builder.get_object("namecustomfields").get_text()
            ctype =  listcombocustomfields.get_value(combocustomfields.get_active_iter(), 1)
            listcustomfields.append((["%s (%s)" % (name, ctype), name, ctype]))
            self.builder.get_object("namecustomfields").set_text("")

    def on_deletecustomfield_clicked(self, widget, data=None):
        listcustomfields = self.builder.get_object("listcustomfields")
        treecustomfields = self.builder.get_object("treecustomfields")
        selection = treecustomfields.get_selection()
        iter_ref = selection.get_selected()[1]
        if iter_ref:
            listcustomfields.remove(iter_ref)
        
    def on_bteditcustomfields_clicked(self, widget, data=None):
        """
        Function called when you press "Edit Custom Fields..."
        """
        listcustomfields = self.builder.get_object("listcustomfields") 
        self.xc_servers[self.selected_host].fill_listcustomfields(listcustomfields)
    
        self.builder.get_object("wcustomfields").show()

    def on_acceptwcustomfields_clicked(self, widget, data=None):
        """
        Function called when you press close button on custom fields window
        """
        listcustomfields = self.builder.get_object("listcustomfields") 
        xml = "<CustomFieldDefinitions>"
        for i in range(listcustomfields.__len__()):
            iter_ref = listcustomfields.get_iter((i,))
            xml = xml + '<CustomFieldDefinition name="%s" type="%s" defaultValue="" />' % (listcustomfields.get_value(iter_ref, 1),
                listcustomfields.get_value(iter_ref, 2).split(" ")[0])
        xml = xml + "</CustomFieldDefinitions>"
        self.xc_servers[self.selected_host].set_pool_custom_fields(xml)
        self.builder.get_object("wcustomfields").hide()
        self.fill_custom_fields_table(add=True)

    def on_cancelwcustomfields_clicked(self, widget, data=None):
        """
        Function called when you press close button on custom fields window
        """
        self.builder.get_object("wcustomfields").hide()

    def on_acceptdialogoptions_clicked(self, widget, data=None):
        """
        Function called when you apply changes on "options" dialog
        """
        # Set in config If "save server passwords" is checked
        self.config["gui"]["save_password"] = str(self.builder.get_object("checksavepassword").get_active())
        # If "save server passwords" is checked
        if self.builder.get_object("checksavepassword").get_active():
            # Convert master password to md5
            m = hashlib.md5()
            m.update(self.builder.get_object("txtmasterpassword").get_text())
            # And set it on configuration
            self.config["gui"]["master_password"] = m.hexdigest()
        # Save configuration in disk
        self.config.write()
        # Hide options dialog
        self.builder.get_object("dialogoptions").hide()
    def on_radiologlocal_toggled(self, widget, data=None):
        """
        Function called when you set server system log destination to "local"
        """
        # Set if enabled or not depends radiologlocal state
        self.builder.get_object("lbllogserver").set_sensitive(not widget.get_active())
        self.builder.get_object("txtlogserver").set_sensitive(not widget.get_active())

    def on_canceldialogoptions_clicked(self, widget, data=None):
        """
        Function called when you cancel changes on "options" dialog
        """
        # Hide options dialog
        self.builder.get_object("dialogoptions").hide()
    def on_btvmpropcancel_activate(self, widget, data=None):
        """
        Function called when you cancel changes on "properties" window
        """
        # Hide properties window
        self.builder.get_object("dialogvmprop").hide()
        # And unset used variables
        self.selected_widget = None
        self.changes = {}
        self.freedevices = {}
    def on_treebootorder_button_press_event(self, widget, event):
        """
        Function called when you select a element on bootorder tree 
        """
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = widget.get_path_at_pos(x, y)
        if pthinfo is not None:
           path, col, cellx, celly = pthinfo
           iter = self.builder.get_object("listpropbootorder").get_iter(path)
           # If is not separated line
           if self.builder.get_object("listpropbootorder").get_value(iter, 2):
               # If is the first disable "up" button, else enable it
               self.builder.get_object("btmoveup").set_sensitive(path[0] != 0)
               # If is the last disable "down" button, else enable it
               self.builder.get_object("btmovedown").set_sensitive(path[0] != 0)
           else:
               # Disable both buttons
               self.builder.get_object("btmoveup").set_sensitive(False)
               self.builder.get_object("btmovedown").set_sensitive(False)
    def on_btmoveup_clicked(self, widget, data=None):
        """
        Function called when you press "Up" button
        """
        rows = self.builder.get_object("treebootorder").get_selection().get_selected_rows()[1][0]
        # Get actual iter
        iter1 = self.builder.get_object("listpropbootorder").get_iter(rows)
        # Get below iter
        iter2 = self.builder.get_object("listpropbootorder").get_iter((rows[0]-1,))
        # Swap
        self.builder.get_object("listpropbootorder").swap(iter1, iter2)
        if rows[0]-1 == 0:
            # If is the first now, disable "up" button and enable "down" button
            self.builder.get_object("btmoveup").set_sensitive(False)
            self.builder.get_object("btmovedown").set_sensitive(True)
    def on_btmovedown_clicked(self, widget, data=None):
        """
        Function called when you press "Down" button
        """
        rows = self.builder.get_object("treebootorder").get_selection().get_selected_rows()[1][0]
        # Get actual iter
        iter1 = self.builder.get_object("listpropbootorder").get_iter(rows)
        # Get above iter
        iter2 = self.builder.get_object("listpropbootorder").get_iter((rows[0]+1,))
        self.builder.get_object("listpropbootorder").swap(iter1, iter2)
        if (rows[0]+1) == 3:
            # If is the last now, disable "down" button and enable "up" button
            self.builder.get_object("btmovedown").set_sensitive(False)
            self.builder.get_object("btmoveup").set_sensitive(True)
    def prop_visible_func(self, model, iter, user_data=None):
        """
        Function to know if a menu element should be showed or hidden
        """
        # aka contains properties element (vm, host, storage, network or vdi)
        aka =  self.listprop.get_value(iter, 2)
        # List of menu options to show
        vm = ["general", "custom", "cpumemory", "startup", "homeserver"]
        host = ["general","custom", "multipath", "logdest"]
        storage = ["general","custom"]
        network = ["general","custom","networksettings"]
        vdi = ["general","custom","sizelocation","stgvm"]
        pool = ["general", "custom"]
        # For different elements show or hidde menu options
        # If return false, element will be not showed, else will be showed
        if self.selected_type == "host":
            if self.selected_widget and gtk.Buildable.get_name(self.selected_widget) == "bthostnetworkproperties":
                # If element is not on "Network" array
                if not network.count(aka):
                    # hide it
                    return False
            else:
                if not host.count(aka):
                    return False
        elif self.selected_widget and (gtk.Buildable.get_name(self.selected_widget) == "btstorageproperties" or 
                gtk.Buildable.get_name(self.selected_widget) == "btstgproperties"):
            # same
            if not vdi.count(aka):
                return False

        elif self.selected_widget and gtk.Buildable.get_name(self.selected_widget) == "menuitem_server_prop":
            # same
            if not host.count(aka):
                return False
        elif self.selected_type == "storage":
            # same
            if not storage.count(aka):
                return False
        elif self.selected_type == "pool":
            # same
            if not pool.count(aka):
                return False

        elif self.selected_type == "vm" or self.selected_type == "template" or self.selected_type == "custom_template":
            if "HVM_shadow_multiplier" in self.xc_servers[self.selected_host].all_vms[self.selected_ref] and \
               "HVM_boot_policy" in self.xc_servers[self.selected_host].all_vms[self.selected_ref] and \
               self.xc_servers[self.selected_host].all_vms[self.selected_ref]["HVM_boot_policy"]:
                vm.append("advancedoptions")
            # same
            if not vm.count(aka):
                return False
        return True
    def on_combostgmodeposition_changed(self, widget, data=None):
        """
        Function called when you change element on combostgmode or combostgposition
        """
        #TODO: comment code

        if self.selected_widget:
            listprop = self.builder.get_object("listprop")
            treeprop = self.builder.get_object("treeprop")
            if gtk.Buildable.get_name(self.selected_widget) == "btstgproperties":
                liststorage = self.builder.get_object("liststg")
                treestorage = self.builder.get_object("treestg")
                column = 0
            else:
                liststorage = self.builder.get_object("listvmstorage")
                treestorage = self.builder.get_object("treevmstorage")
                column = 10
            selection = treestorage.get_selection()
            iter = selection.get_selected()[1]
            ref = liststorage.get_value(iter,column)


            path = self.selected_prop_path 
            if gtk.Buildable.get_name(self.selected_widget) == "btstgproperties":
                ref = self.xc_servers[self.selected_host].all_vdi[ref]['VBDs'][path[0]-9]
                device = self.xc_servers[self.selected_host].all_vbd[ref]['userdevice']
                mode = self.xc_servers[self.selected_host].all_vbd[ref]['mode']
                vm_ref = self.xc_servers[self.selected_host].all_vbd[ref]['VM']
            else:
                device = self.xc_servers[self.selected_host].all_vbd[ref]['userdevice']
                mode = self.xc_servers[self.selected_host].all_vbd[ref]['mode']
                vm_ref = self.xc_servers[self.selected_host].all_vbd[ref]['VM']
            if ref not in self.changes:
                self.changes[ref] = {}
            if gtk.Buildable.get_name(widget) == "combostgmode":
                if mode != widget.get_active_text():
                    self.changes[ref]['mode'] = widget.get_active_text()
                else:
                    if "mode" in self.changes[ref]:
                        del self.changes[ref]['mode'] 
            else:
                if device != widget.get_active_text():
                    self.changes[ref]['position'] = widget.get_active_text()
                else:
                    if "position" in self.changes[ref]:
                        del self.changes[ref]['position']
                if device != widget.get_active_text() and \
                        not self.freedevices[vm_ref].count(widget.get_active_text()):
                    self.builder.get_object("lblinuse").show()
                    self.builder.get_object("btvmpropaccept").set_sensitive(False)
                else:
                    self.builder.get_object("lblinuse").hide()
                    self.builder.get_object("btvmpropaccept").set_sensitive(True)

    def on_checkisbootable_clicked(self, widget, data=None):
        """
        Function called when you change bootable check state
        """
        if self.selected_widget:
            listprop = self.builder.get_object("listprop")
            treeprop = self.builder.get_object("treeprop")
            if gtk.Buildable.get_name(self.selected_widget) == "btstgproperties":
                liststorage = self.builder.get_object("liststg")
                treestorage = self.builder.get_object("treestg")
                column = 0
            else:
                liststorage = self.builder.get_object("listvmstorage")
                treestorage = self.builder.get_object("treevmstorage")
                column = 10
            selection = treestorage.get_selection()
            iter = selection.get_selected()[1]
            ref = liststorage.get_value(iter,column)
            path = self.selected_prop_path 
            if gtk.Buildable.get_name(self.selected_widget) == "btstgproperties":
                ref = self.xc_servers[self.selected_host].all_vdi[ref]['VBDs'][path[0]-9]
            bootable = self.xc_servers[self.selected_host].all_vbd[ref]['bootable']
            if ref not in self.changes:
                self.changes[ref] = {}
            if bootable != widget.get_active():
                self.changes[ref]['bootable'] = widget.get_active()

    def on_acceptdialogsyslogempty_clicked(self, widget, data=None):
        """
        If you set a empty syslog server, dialogsyslogempty is showed
        This function is called when you accept the dialog
        """
        self.builder.get_object("dialogsyslogempty").hide()

    def on_spinpropvmprio_change_value(self, widget, data, data2):
        """
        Function called when "Priority" spin value is changed
        """
        # spin get value from 0 to 10, but priority goes from 1 to 64000 (less or more)
        # then 2 ^ (2 * spin value) gets the real priority
        self.builder.get_object("spinpropvmprio").set_value(2**(2*int(data2)))
    def on_treeprop_button_press_event(self,widget, event):
        """
        Function called when you select a left property option
        """
        # TODO: comment code
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = widget.get_path_at_pos(x, y)
        if pthinfo is not None:
           path, col, cellx, celly = pthinfo
           widget.grab_focus()
           widget.set_cursor( path, col, 0)
           path = self.propmodelfilter.convert_path_to_child_path(path)
           self.selected_prop_path = path
           iter = self.listprop.get_iter(path)
           if path[0] < 9 or self.listprop.get_value(iter, 2) == "advancedoptions":
               self.builder.get_object("tabprops").set_current_page(self.listprop.get_value(iter, 3))
           else:
               self.builder.get_object("tabprops").set_current_page(9)
           if path[0] > 8 and self.listprop.get_value(iter, 2) != "advancedoptions":
               if gtk.Buildable.get_name(self.selected_widget) == "btstgproperties":
                   liststorage = self.builder.get_object("liststg")
                   treestorage = self.builder.get_object("treestg")
                   column = 0
               else:
                   liststorage = self.builder.get_object("listvmstorage")
                   treestorage = self.builder.get_object("treevmstorage")
                   column = 10
               selection = treestorage.get_selection()
               iter = selection.get_selected()[1]
               ref = liststorage.get_value(iter,column)
               if gtk.Buildable.get_name(self.selected_widget) == "btstgproperties":
                   ref = self.xc_servers[self.selected_host].all_vdi[ref]['VBDs'][path[0]-9]
                   vm_ref = self.xc_servers[self.selected_host].all_vbd[ref]['VM']
                   device = self.xc_servers[self.selected_host].all_vbd[ref]['userdevice']
                   type = self.xc_servers[self.selected_host].all_vbd[ref]['type']
                   mode = self.xc_servers[self.selected_host].all_vbd[ref]['mode']
                   bootable = self.xc_servers[self.selected_host].all_vbd[ref]['bootable']
                   vm_name = self.xc_servers[self.selected_host].all_vms[vm_ref]['name_label']
                   self.builder.get_object("lblpropstgvm").set_label(vm_name)
                   if mode == "RW":
                       self.builder.get_object("combostgmode").set_active(0)
                   else:
                       self.builder.get_object("combostgmode").set_active(1)
                   if device[0] != "x":
                       self.builder.get_object("combostgposition").set_sensitive(True)
                       self.builder.get_object("combostgposition").set_active(int(device))
                   else:
                       self.builder.get_object("combostgposition").set_sensitive(False)
                   self.builder.get_object("combostgmode").set_sensitive(type == "Disk")
                   self.builder.get_object("checkisbootable").set_active(bootable)
               else:
                   device = self.xc_servers[self.selected_host].all_vbd[ref]['userdevice']
                   mode = self.xc_servers[self.selected_host].all_vbd[ref]['mode']
                   bootable = self.xc_servers[self.selected_host].all_vbd[ref]['bootable']
                   vm_ref = self.xc_servers[self.selected_host].all_vbd[ref]['VM']
                   vm_name = self.xc_servers[self.selected_host].all_vms[vm_ref]['name_label']
                   self.builder.get_object("lblpropstgvm").set_label(vm_name)
                   if mode == "RW":
                       self.builder.get_object("combostgmode").set_active(0)
                   else:
                       self.builder.get_object("combostgmode").set_active(1)
                   self.builder.get_object("combostgposition").set_active(int(device))
                   self.builder.get_object("checkisbootable").set_active(bootable)
    def on_btvmpropaccept_activate(self, widget, data=None):
        """ 
        Function called when you accept window properties
        """
        # TODO: comment codea

        if self.selected_widget and gtk.Buildable.get_name(self.selected_widget) == "bthostnetworkproperties":
            liststorage = self.builder.get_object("listhostnetwork")
            treestorage = self.builder.get_object("treehostnetwork")
            selection = treestorage.get_selection()
            iter = selection.get_selected()[1]
            ref = liststorage.get_value(iter,7)
            network = self.xc_servers[self.selected_host].all_network[ref]
            tb = self.builder.get_object("txtpropvmdesc").get_buffer()
            if self.builder.get_object("txtpropvmname").get_text() != network['name_label']:
                self.xc_servers[self.selected_host].set_network_name_label(ref,
                        self.builder.get_object("txtpropvmname").get_text())
            if tb.get_text(tb.get_start_iter(), tb.get_end_iter()) != network['name_description']:
                self.xc_servers[self.selected_host].set_network_name_description(ref,
                        tb.get_text(tb.get_start_iter(), tb.get_end_iter()))
            if "automatic" in network['other_config'] and network['other_config']['automatic'] == "true":
                if self.builder.get_object("checknetworkautoadd").get_active() == False:
                    self.xc_servers[self.selected_host].set_network_automatically(ref,
                            self.builder.get_object("checknetworkautoadd").get_active())

            else:
                if self.builder.get_object("checknetworkautoadd").get_active():
                    self.xc_servers[self.selected_host].set_network_automatically(ref,
                            self.builder.get_object("checknetworkautoadd").get_active())
            self.changes = {}
            other_config = network["other_config"]
            change = False
            for cfield in  self.vboxchildtext:
                if "XenCenter.CustomFields." + cfield in other_config:
                    if self.vboxchildtext[cfield].get_text() != other_config["XenCenter.CustomFields." + cfield]:
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
                else:
                    if self.vboxchildtext[cfield].get_text():
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
            if change:
                self.xc_servers[self.selected_host].set_network_other_config(self.selected_ref, other_config)

        elif self.selected_widget and (gtk.Buildable.get_name(self.selected_widget) == "btstgproperties" or \
                gtk.Buildable.get_name(self.selected_widget) == "btstorageproperties"):
            if gtk.Buildable.get_name(self.selected_widget) == "btstgproperties":
               liststorage = self.builder.get_object("liststg")
               treestorage = self.builder.get_object("treestg")
               column = 0
            else:
               liststorage = self.builder.get_object("listvmstorage")
               treestorage = self.builder.get_object("treevmstorage")
               column = 10
            selection = treestorage.get_selection()
            iter = treestorage.get_selection().get_selected()[1]
            ref = liststorage.get_value(iter,column)
            if gtk.Buildable.get_name(self.selected_widget) == "btstgproperties":
               vdi_ref = ref
            else:
               vdi_ref = self.xc_servers[self.selected_host].all_vbd[ref]['VDI']
            vdi_sr = self.xc_servers[self.selected_host].all_vdi[vdi_ref]['SR']
            vdi = self.xc_servers[self.selected_host].all_vdi[vdi_ref]
            tb = self.builder.get_object("txtpropvmdesc").get_buffer()
            if self.builder.get_object("txtpropvmname").get_text() != vdi['name_label']:
               self.xc_servers[self.selected_host].set_vdi_name_label(vdi_ref,self.builder.get_object("txtpropvmname").get_text())
            if tb.get_text(tb.get_start_iter(), tb.get_end_iter()) != vdi['name_description']:
               self.xc_servers[self.selected_host].set_vdi_name_description(vdi_ref,tb.get_text(tb.get_start_iter(), tb.get_end_iter()))
            if self.builder.get_object("spinvdisize").get_value() != float(vdi['virtual_size'])/1024/1024/1024:
               size = self.builder.get_object("spinvdisize").get_value()*1024*1024*1024
               self.xc_servers[self.selected_host].resize_vdi(vdi_ref,size)
            for ref in self.changes:
               if "position" in self.changes[ref]:
                   self.xc_servers[self.selected_host].set_vbd_userdevice(ref, self.changes[ref]['position'])
               if "mode" in self.changes[ref]:
                   self.xc_servers[self.selected_host].set_vbd_mode(ref, self.changes[ref]['mode'])
               if "bootable" in self.changes[ref]:
                   self.xc_servers[self.selected_host].set_vbd_bootable(ref, self.changes[ref]['bootable'])

            self.changes = {}
            other_config = vdi["other_config"]
            change = False
            for cfield in  self.vboxchildtext:
                if "XenCenter.CustomFields." + cfield in other_config:
                    if self.vboxchildtext[cfield].get_text() != other_config["XenCenter.CustomFields." + cfield]:
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
                else:
                    if self.vboxchildtext[cfield].get_text():
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
            if change:
                self.xc_servers[self.selected_host].set_vdi_other_config(self.selected_ref, other_config)

        elif self.selected_type == "host" or (self.selected_widget and
                                gtk.Buildable.get_name(self.selected_widget) == "menuitem_server_prop"):
            vm = self.xc_servers[self.selected_host].all_hosts[self.selected_ref]
            tb = self.builder.get_object("txtpropvmdesc").get_buffer()
            if "syslog_destination" in vm["logging"] == self.builder.get_object("radiologlocal").get_active():
                if self.builder.get_object("radiologlocal").get_active():
                    self.xc_servers[self.selected_host].set_host_log_destination(self.selected_ref,
                            None)
                else:
                    if self.builder.get_object("txtlogserver").get_text():
                        self.xc_servers[self.selected_host].set_host_log_destination(self.selected_ref,
                                self.builder.get_object("txtlogserver").get_text())
                    else:
                        self.builder.get_object("dialogsyslogempty").show()
                        return
            if self.builder.get_object("txtpropvmname").get_text() != vm['name_label']:
                self.xc_servers[self.selected_host].set_host_name_label(self.selected_ref,
                        self.builder.get_object("txtpropvmname").get_text())
            if tb.get_text(tb.get_start_iter(), tb.get_end_iter()) != vm['name_description']:
                self.xc_servers[self.selected_host].set_host_name_description(self.selected_ref,
                        tb.get_text(tb.get_start_iter(), tb.get_end_iter()))

            other_config = vm["other_config"]
            change = False
            for cfield in  self.vboxchildtext:
                if "XenCenter.CustomFields." + cfield in other_config:
                    if self.vboxchildtext[cfield].get_text() != other_config["XenCenter.CustomFields." + cfield]:
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
                else:
                    if self.vboxchildtext[cfield].get_text():
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
            if change:
                self.xc_servers[self.selected_host].set_host_other_config(self.selected_ref, other_config)

        elif self.selected_type == "storage":
            stg = self.xc_servers[self.selected_host].all_storage[self.selected_ref]
            tb = self.builder.get_object("txtpropvmdesc").get_buffer()
            if self.builder.get_object("txtpropvmname").get_text() != stg['name_label']:
                self.xc_servers[self.selected_host].set_storage_name_label(self.selected_ref,
                        self.builder.get_object("txtpropvmname").get_text())
            if tb.get_text(tb.get_start_iter(), tb.get_end_iter()) != stg['name_description']:
                self.xc_servers[self.selected_host].set_storage_name_description(self.selected_ref,
                        tb.get_text(tb.get_start_iter(), tb.get_end_iter()))

            other_config = stg["other_config"]
            change = False
            for cfield in  self.vboxchildtext:
                if "XenCenter.CustomFields." + cfield in other_config:
                    if self.vboxchildtext[cfield].get_text() != other_config["XenCenter.CustomFields." + cfield]:
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
                else:
                    if self.vboxchildtext[cfield].get_text():
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
            if change:
                self.xc_servers[self.selected_host].set_storage_other_config(self.selected_ref, other_config)

        elif self.selected_type == "pool":
            pool = self.xc_servers[self.selected_host].all_pools[self.selected_ref]
            tb = self.builder.get_object("txtpropvmdesc").get_buffer()
            if self.builder.get_object("txtpropvmname").get_text() != pool['name_label']:
                self.xc_servers[self.selected_host].set_pool_name_label(self.selected_ref,
                        self.builder.get_object("txtpropvmname").get_text())
            if tb.get_text(tb.get_start_iter(), tb.get_end_iter()) != pool['name_description']:
                self.xc_servers[self.selected_host].set_pool_name_description(self.selected_ref,
                        tb.get_text(tb.get_start_iter(), tb.get_end_iter()))

            other_config = pool["other_config"]
            change = False
            for cfield in self.vboxchildtext:
                if "XenCenter.CustomFields." + cfield in other_config:
                    if self.vboxchildtext[cfield].get_text() != other_config["XenCenter.CustomFields." + cfield]:
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
                else:
                    if self.vboxchildtext[cfield].get_text():
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
            if change:
                self.xc_servers[self.selected_host].set_pool_other_config(self.selected_ref, other_config)

        elif self.selected_type == "vm" or self.selected_type == "template" or self.selected_type == "custom_template":
            vm =  self.xc_servers[self.selected_host].all_vms[self.selected_ref]
            tb = self.builder.get_object("txtpropvmdesc").get_buffer()
            if self.builder.get_object("txtpropvmname").get_text() != vm['name_label']:
                self.xc_servers[self.selected_host].set_vm_name_label(self.selected_ref,
                        self.builder.get_object("txtpropvmname").get_text())
            if tb.get_text(tb.get_start_iter(), tb.get_end_iter()) != vm['name_description']:
                self.xc_servers[self.selected_host].set_vm_name_description(self.selected_ref,
                        tb.get_text(tb.get_start_iter(), tb.get_end_iter()))

            if int(self.builder.get_object("spinpropvmmem").get_value()) != int(vm["memory_dynamic_min"])/1024/1024:
                self.xc_servers[self.selected_host].set_vm_memory(self.selected_ref,
                        self.builder.get_object("spinpropvmmem").get_value())
            if int(self.builder.get_object("spinpropvmvcpus").get_value()) != int(vm["VCPUs_at_startup"]):
                self.xc_servers[self.selected_host].set_vm_vcpus(self.selected_ref,
                        self.builder.get_object("spinpropvmvcpus").get_value())
            if "weight" in vm["VCPUs_params"]:
                if self.builder.get_object("spinpropvmprio").get_value() != float(vm["VCPUs_params"]["weight"]):
                    self.xc_servers[self.selected_host].set_vm_prio(self.selected_ref,
                        self.builder.get_object("spinpropvmprio").get_value())
            else:
                if self.builder.get_object("spinpropvmprio").get_value() != float(256):
                    self.xc_servers[self.selected_host].set_vm_prio(self.selected_ref,
                        self.builder.get_object("spinpropvmprio").get_value())

            if "auto_poweron" in vm['other_config'] and vm['other_config']["auto_poweron"] == "true":
                if self.builder.get_object("checkvmpropautostart").get_active() == False:
                    self.xc_servers[self.selected_host].set_vm_poweron(self.selected_ref,
                        self.builder.get_object("checkvmpropautostart").get_active())
            else:
                if self.builder.get_object("checkvmpropautostart").get_active():
                    self.xc_servers[self.selected_host].set_vm_poweron(self.selected_ref,
                        self.builder.get_object("checkvmpropautostart").get_active())
            if not vm['HVM_boot_policy']:
                if self.builder.get_object("txtvmpropparams").get_text() != vm['PV_args']:
                    self.xc_servers[self.selected_host].set_vm_bootpolicy(self.selected_ref,
                        self.builder.get_object("txtvmpropparams").get_text())
            else:
                order = ''
                for i in range(0,4):
                    iter = self.builder.get_object("listpropbootorder").get_iter((i,0))
                    order += self.builder.get_object("listpropbootorder").get_value(iter,0)
                    if self.builder.get_object("listpropbootorder").get_value(iter,2) == False:
                        break
                if order != vm['HVM_boot_params']['order']:
                    self.xc_servers[self.selected_host].set_vm_boot_params(self.selected_ref,
                        order)
            shared = True
            for vbd_ref in vm['VBDs']:
                vbd = self.xc_servers[self.selected_host].get_vbd(vbd_ref)
                if vbd['VDI'] != "OpaqueRef:NULL" and vbd['VDI']:
                    vdi = self.xc_servers[self.selected_host].get_vdi(vbd['VDI'])
                    if not self.xc_servers[self.selected_host].get_storage(vdi['SR'])["shared"]:
                        shared = False
                        break
            if self.builder.get_object("radioautohome").get_active() and (vm["affinity"] != "OpaqueRef:NULL"):
                self.xc_servers[self.selected_host].set_vm_affinity(self.selected_ref, "OpaqueRef:NULL")
            if self.builder.get_object("radiomanualhome").get_active():
                listhomeserver = self.builder.get_object("listhomeserver")
                treehomeserver = self.builder.get_object("treehomeserver")
                iter = treehomeserver.get_selection().get_selected()[1]
                affinity =  listhomeserver.get_value(iter, 0)
                if affinity != vm["affinity"]:
                    self.xc_servers[self.selected_host].set_vm_affinity(self.selected_ref, affinity)

            other_config = vm["other_config"]
            change = False
            for cfield in  self.vboxchildtext:
                if "XenCenter.CustomFields." + cfield in other_config:
                    if self.vboxchildtext[cfield].get_text() != other_config["XenCenter.CustomFields." + cfield]:
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
                else:
                    if self.vboxchildtext[cfield].get_text():
                        change = True
                        other_config["XenCenter.CustomFields." + cfield] = self.vboxchildtext[cfield].get_text()
            if change:
                self.xc_servers[self.selected_host].set_vm_other_config(self.selected_ref, other_config)

            if "HVM_shadow_multiplier" in vm:
                if self.builder.get_object("optimizegeneraluse").get_active():
                    multiplier = "1.00"
                elif self.builder.get_object("optimizeforxenapp").get_active():
                    multiplier = "4.00"
                else:
                    multiplier = self.builder.get_object("memorymultiplier").get_text()
                if multiplier != str(vm["HVM_shadow_multiplier"]):
                    self.xc_servers[self.selected_host].set_vm_memory_multiplier(self.selected_ref, multiplier)

        self.builder.get_object("dialogvmprop").hide()
        self.selected_widget = None

    def fill_btstorage_properties(self, widget):
        self.selected_widget = widget
        self.propmodelfilter.refilter()
        listprop = self.builder.get_object("listprop")
        treeprop = self.builder.get_object("treeprop")
        treeprop.set_cursor((0,), treeprop.get_column(0))
        if treeprop.get_selection():
            treeprop.get_selection().select_path((0,))
        if gtk.Buildable.get_name(widget) == "btstorageproperties": 
            liststorage = self.builder.get_object("listvmstorage")
            treestorage = self.builder.get_object("treevmstorage")
            column = 10
        else:
            liststorage = self.builder.get_object("liststg")
            treestorage = self.builder.get_object("treestg")
            column = 0
        selection = treestorage.get_selection()
        if selection.get_selected()[1] != None:
            self.builder.get_object("vmfreedevices").show()
            #self.builder.get_object("dialogvmprop").show()
            for i in range(listprop.__len__()-1,8,-1):
                iter = listprop.get_iter((i,))
                listprop.remove(iter)
            iter = selection.get_selected()[1]
            ref = liststorage.get_value(iter,column)
            #print self.xc_servers[self.selected_host].all_vdi[ref]
            if gtk.Buildable.get_name(widget) == "btstgproperties":
                vdi_ref = ref
            else:
                vdi_ref = self.xc_servers[self.selected_host].all_vbd[ref]['VDI']
            vdi_sr = self.xc_servers[self.selected_host].all_vdi[vdi_ref]['SR']
            vdi = self.xc_servers[self.selected_host].all_vdi[vdi_ref]
            stg_name = self.xc_servers[self.selected_host].all_storage[vdi_sr]['name_label']
            stg_pbds = self.xc_servers[self.selected_host].all_storage[vdi_sr]['PBDs']
            hosts = []
            for stg_pbd in stg_pbds:
               stg_host = self.xc_servers[self.selected_host].all_pbd[stg_pbd]['host']
               hosts.append( self.xc_servers[self.selected_host].all_hosts[stg_host]['name_label'])
            iter = listprop.get_iter((0,))
            listprop.set_value(iter, 1, "<b>General</b>\n   <i>" + vdi['name_label'] + "</i>")
            self.builder.get_object("txtpropvmname").set_text(vdi['name_label'])
            self.builder.get_object("txtpropvmdesc").get_buffer().set_text(vdi['name_description'])
            iter = listprop.get_iter((8,))
            subtext = self.convert_bytes(vdi['virtual_size']) + "," + stg_name + " on " + ",".join(hosts)
            listprop.set_value(iter, 1, "<b>Size and Location</b>\n   <i>" + subtext + "</i>")
            self.builder.get_object("adjvdisize").set_lower(float(vdi['virtual_size'])/1024/1024/1024)
            self.builder.get_object("spinvdisize").set_value(float(vdi['virtual_size'])/1024/1024/1024)
            listvdilocation = self.builder.get_object("listvdilocation")
            pos = self.xc_servers[self.selected_host].fill_vdi_location(vdi_sr, listvdilocation)
            self.builder.get_object("spinvdisize").set_sensitive(vdi['allowed_operations'].count("resize"))
            if gtk.Buildable.get_name(widget) == "btstgproperties":
                i = 9
                vbds = len(self.xc_servers[self.selected_host].all_vdi[ref]['VBDs'])
                if vbds:
                    parts = float(1)/vbds
                else:
                    parts = 1
                self.builder.get_object("progressfreedevices").set_pulse_step(parts)
                update = 0
                for ref in self.xc_servers[self.selected_host].all_vdi[ref]['VBDs']:
                    vm_ref = self.xc_servers[self.selected_host].all_vbd[ref]['VM']
                    device = self.xc_servers[self.selected_host].all_vbd[ref]['userdevice']
                    mode = self.xc_servers[self.selected_host].all_vbd[ref]['mode']
                    listprop.append([gtk.gdk.pixbuf_new_from_file("images/prop_stgvm.png"), "<b>NAME</b>", "stgvm", i])
                    iter = listprop.get_iter((i,))
                    mode = "Read / Write" if mode == "RW" else "Read Only"
                    vm_name = self.xc_servers[self.selected_host].all_vms[vm_ref]['name_label']
                    subtext = "Device %s, (%s)" % (device, mode)
                    listprop.set_value(iter, 1, "<b>" + vm_name + "</b>\n   <i>" + subtext + "</i>")
                    i = i + 1
                    self.freedevices[vm_ref] =  self.xc_servers[self.selected_host].get_allowed_vbd_devices(vm_ref)
                    update = update + parts
                    self.builder.get_object("progressfreedevices").pulse()
            else: 
                vm_ref = self.xc_servers[self.selected_host].all_vbd[ref]['VM']
                device = self.xc_servers[self.selected_host].all_vbd[ref]['userdevice']
                mode = self.xc_servers[self.selected_host].all_vbd[ref]['mode']
                listprop.append([gtk.gdk.pixbuf_new_from_file("images/prop_stgvm.png"), "<b>NAME</b>", "stgvm", 9])
                iter = listprop.get_iter((9,))
                mode = "Read / Write" if mode == "RW" else "Read Only"
                vm_name = self.xc_servers[self.selected_host].all_vms[vm_ref]['name_label']
                subtext = "Device %s, (%s)" % (device, mode)
                listprop.set_value(iter, 1, "<b>" + vm_name + "</b>\n   <i>" + subtext + "</i>")
                self.freedevices[vm_ref] =  self.xc_servers[self.selected_host].get_allowed_vbd_devices(vm_ref)
                self.builder.get_object("progressfreedevices").set_pulse_step(1)
                self.builder.get_object("progressfreedevices").pulse()

            self.builder.get_object("vmfreedevices").hide()
            self.builder.get_object("dialogvmprop").show()
            return self.xc_servers[self.selected_host].all_storage[vdi_sr]['other_config']

    def fill_host_network_properties(self, widget):
        self.selected_widget = widget
        self.propmodelfilter.refilter()
        self.builder.get_object("tabprops").set_current_page(0)
        listprop = self.builder.get_object("listprop")
        treeprop = self.builder.get_object("treeprop")
        treeprop.set_cursor((0,), treeprop.get_column(0))
        treeprop.get_selection().select_path((0,))
        liststorage = self.builder.get_object("listhostnetwork")
        treestorage = self.builder.get_object("treehostnetwork")
        selection = treestorage.get_selection()
        if selection.get_selected()[1] != None:
            self.builder.get_object("dialogvmprop").show()
            iter = selection.get_selected()[1]
            network = self.xc_servers[self.selected_host].all_network[liststorage.get_value(iter,7)]

            iter = listprop.get_iter((0,))
            listprop.set_value(iter, 1, "<b>General</b>\n   <i>" + network['name_label'] + "</i>")
            self.builder.get_object("txtpropvmname").set_text(network['name_label'])
            self.builder.get_object("txtpropvmdesc").get_buffer().set_text(network['name_description'])
            if "automatic" in network['other_config'] and network['other_config']['automatic'] == "true":
                self.builder.get_object("checknetworkautoadd").set_active(True)
            else:
                self.builder.get_object("checknetworkautoadd").set_active(False)
            return network["other_config"]

    def fill_server_properties(self, widget):
        self.selected_widget = widget
        self.propmodelfilter.refilter()
        self.builder.get_object("tabprops").set_current_page(0)
        listprop = self.builder.get_object("listprop")
        treeprop = self.builder.get_object("treeprop")
        treeprop.set_cursor((0,), treeprop.get_column(0))
        treeprop.get_selection().select_path((0,))
        if gtk.Buildable.get_name(widget) == "menuitem_server_prop":
            ref = self.treestore.get_value(self.treestore.iter_parent(self.selected_iter),6)
            if ref in self.xc_servers[self.selected_host].all_hosts:
                vm =  self.xc_servers[self.selected_host].all_hosts[ref]
            else:
                vm =  self.xc_servers[self.selected_host].all_hosts[self.selected_ref]
        else:
            vm =  self.xc_servers[self.selected_host].all_hosts[self.selected_ref]
        iter = listprop.get_iter((0,))
        listprop.set_value(iter, 1, "<b>General</b>\n   <i>" + vm['name_label'] + "</i>")
        self.builder.get_object("txtpropvmname").set_text(vm['name_label'])
        self.builder.get_object("txtpropvmdesc").get_buffer().set_text(vm['name_description'])
        if "syslog_destination" in vm['logging']:
            self.builder.get_object("radiologlocal").set_active(False)
            self.builder.get_object("radiologremote").set_active(True)
            self.builder.get_object("txtlogserver").set_text(vm["logging"]["syslog_destination"])
        else:
            self.builder.get_object("radiologlocal").set_active(True)
            self.builder.get_object("radiologremote").set_active(False)
            self.builder.get_object("txtlogserver").set_text("")
        self.builder.get_object("dialogvmprop").show()
        return vm["other_config"]

    def fill_storage_properties(self):
        listprop = self.builder.get_object("listprop")
        treeprop = self.builder.get_object("treeprop")
        treeprop.set_cursor((0,), treeprop.get_column(0))
        treeprop.get_selection().select_path((0,))
        stg =  self.xc_servers[self.selected_host].all_storage[self.selected_ref]
        iter = listprop.get_iter((0,))
        listprop.set_value(iter, 1, "<b>General</b>\n   <i>" + stg['name_label'] + "</i>")
        self.builder.get_object("txtpropvmname").set_text(stg['name_label'])
        self.builder.get_object("txtpropvmdesc").get_buffer().set_text(stg['name_description'])
        self.builder.get_object("dialogvmprop").show()
        self.builder.get_object("tabprops").set_current_page(0)
        return stg["other_config"]

    def fill_pool_properties(self):
        self.builder.get_object("tabprops").set_current_page(0)
        listprop = self.builder.get_object("listprop")
        treeprop = self.builder.get_object("treeprop")
        treeprop.set_cursor((0,), treeprop.get_column(0))
        treeprop.get_selection().select_path((0,))
        pool =  self.xc_servers[self.selected_host].all_pools[self.selected_ref]
        iter = listprop.get_iter((0,))
        listprop.set_value(iter, 1, "<b>General</b>\n   <i>" + pool['name_label'] + "</i>")
        self.builder.get_object("txtpropvmname").set_text(pool['name_label'])
        self.builder.get_object("txtpropvmdesc").get_buffer().set_text(pool['name_description'])
        self.builder.get_object("dialogvmprop").show()
        return pool["other_config"]

    def fill_vm_properties(self):
        listprop = self.builder.get_object("listprop")
        vm =  self.xc_servers[self.selected_host].all_vms[self.selected_ref]
        # Name, Description, Folder and Tags
        iter = listprop.get_iter((0,))
        listprop.set_value(iter, 1, "<b>General</b>\n   <i>" + vm['name_label'] + "</i>")
        self.builder.get_object("txtpropvmname").set_text(vm['name_label'])
        self.builder.get_object("txtpropvmdesc").get_buffer().set_text(vm['name_description'])
        if "folder" in vm['other_config']:
            self.builder.get_object("lblpropvmfolder").set_label(vm['other_config']['folder'])
        else:
            self.builder.get_object("lblpropvmfolder").set_label("")
        if vm["tags"]:
            self.builder.get_object("lblpropvmtags").set_label(", ".join(vm["tags"]))
        else:
            self.builder.get_object("lblpropvmtags").set_label("")

        # Memory and VCPUS
        iter = listprop.get_iter((2,))
        listprop.set_value(iter, 1, "<b>CPU and Memory</b>\n   <i>" \
                + "%s VCPU(s) and %s RAM" % (vm["VCPUs_at_startup"],
                    self.convert_bytes(vm["memory_dynamic_max"])) + "</i>")
        self.builder.get_object("spinpropvmmem").set_value(float(vm["memory_dynamic_min"])/1024/1024)
        self.builder.get_object("spinpropvmvcpus").set_value(float(vm["VCPUs_at_startup"]))
        if "weight" in vm["VCPUs_params"]:
            self.builder.get_object("spinpropvmprio").set_value(float(vm["VCPUs_params"]["weight"]))
            weight = float(vm["VCPUs_params"]["weight"])
            if weight == 1:
                self.builder.get_object("scalepropvmprio").set_value(0)
            elif weight <= 4:
                self.builder.get_object("scalepropvmprio").set_value(1)
            elif weight <= 16:
                self.builder.get_object("scalepropvmprio").set_value(2)
            elif weight <= 64:
                self.builder.get_object("scalepropvmprio").set_value(3)
            elif weight <= 256:
                self.builder.get_object("scalepropvmprio").set_value(4)
            elif weight <= 1024:
                self.builder.get_object("scalepropvmprio").set_value(5)
            elif weight <= 4096:
                self.builder.get_object("scalepropvmprio").set_value(6)
            elif weight <= 16384:
                self.builder.get_object("scalepropvmprio").set_value(7)
            else:
                self.builder.get_object("scalepropvmprio").set_value(8)
        else:
            self.builder.get_object("spinpropvmprio").set_value(256)
            self.builder.get_object("scalepropvmprio").set_value(4)

        # Boot Options
        iter = listprop.get_iter((3,))
        if "auto_poweron" in vm['other_config'] and vm['other_config']["auto_poweron"] == "true":
            listprop.set_value(iter, 1, "<b>Startup Options</b>\n   <i>Auto-start on server boot</i>")
        else:
            listprop.set_value(iter, 1, "<b>Startup Options</b>\n   <i>None defined</i>")
        if "auto_poweron" in vm['other_config'] and vm['other_config']["auto_poweron"] == "true":
           self.builder.get_object("checkvmpropautostart").set_active(True)
        else:
           self.builder.get_object("checkvmpropautostart").set_active(False)

        if not vm['HVM_boot_policy']:
            self.builder.get_object("txtvmpropparams").set_text(vm['PV_args'])
            self.builder.get_object("lblpropvmorder").hide()
            self.builder.get_object("scrollwindowbootorder").hide()
            self.builder.get_object("btmoveup").hide()
            self.builder.get_object("btmovedown").hide()
            self.builder.get_object("lblvmpropparams").show()
            self.builder.get_object("txtvmpropparams").show()
        else:
            self.builder.get_object("lblpropvmorder").show()
            self.builder.get_object("scrollwindowbootorder").show()
            self.builder.get_object("btmoveup").show()
            self.builder.get_object("btmovedown").show()
            self.builder.get_object("lblvmpropparams").hide()
            self.builder.get_object("txtvmpropparams").hide()
            listbootorder = self.builder.get_object("listpropbootorder")
            listbootorder.clear()
            for param in list(vm['HVM_boot_params']['order']):
                if param == 'c':
                    listbootorder.append([param, "Hard Disk", True])
                elif param == 'd':
                    listbootorder.append([param, "DVD-Drive", True])
                elif param == 'n':
                    listbootorder.append([param, "Network", True])
            listbootorder.append(["","-------------- VM will not boot from devices below this line ------------", False])
            if vm['HVM_boot_params']['order'].count("c") == 0:
                    listbootorder.append(["c", "Hard Disk", True])
            if vm['HVM_boot_params']['order'].count("d") == 0:
                    listbootorder.append(["d", "DVD-Drive", True])
            if vm['HVM_boot_params']['order'].count("n") == 0:
                    listbootorder.append(["n", "Network", True])
        # Home Server || TODO shared
        iter = listprop.get_iter((4,))
        if vm['affinity'] != "OpaqueRef:NULL" and vm['affinity'] in self.xc_servers[self.selected_host].all_hosts:
            affinity =  self.xc_servers[self.selected_host].all_hosts[vm['affinity']]
            listprop.set_value(iter, 1, "<b>Home server</b>\n   <i>" +  affinity['name_label'] + "</i>")
        else:
            listprop.set_value(iter, 1, "<b>Home server</b>\n   <i>None defined</i>")

        shared = True
        for vbd_ref in vm['VBDs']:
            vbd = self.xc_servers[self.selected_host].get_vbd(vbd_ref)
            if vbd['VDI'] != "OpaqueRef:NULL" and vbd['VDI']:
                vdi = self.xc_servers[self.selected_host].get_vdi(vbd['VDI'])
                if not vdi or self.xc_servers[self.selected_host].get_storage(vdi['SR'])["type"] != "nfs":
                    shared = False
                    break
        self.builder.get_object("radioautohome").set_sensitive(shared)
        self.builder.get_object("radioautohome").set_active(shared)
        self.builder.get_object("radiomanualhome").set_active(not shared)
        if shared:
            if vm["affinity"] == "OpaqueRef:NULL":
                self.builder.get_object("radioautohome").set_active(True)
            else:
                self.builder.get_object("radiomanualhome").set_active(True)
        listhomeserver = self.builder.get_object("listhomeserver")
        server = self.xc_servers[self.selected_host].fill_listhomeserver(listhomeserver, vm["affinity"])
        treehomeserver = self.builder.get_object("treehomeserver")
        treehomeserver.set_cursor((0,), treehomeserver.get_column(0))
        treehomeserver.get_selection().select_path((0,))

        if "HVM_shadow_multiplier" in vm:
            self.builder.get_object("memorymultiplier").set_text(str(vm["HVM_shadow_multiplier"]))
            if float(vm["HVM_shadow_multiplier"]) == 1.00:
                self.builder.get_object("optimizegeneraluse").set_active(True)
            elif float(vm["HVM_shadow_multiplier"])  == 4.00:
                self.builder.get_object("optimizeforxenapp").set_active(True)
            else:
                self.builder.get_object("optimizemanually").set_active(True)

        self.propmodelfilter.refilter()

        # Show VM window properties
        self.builder.get_object("tabprops").set_current_page(0)
        treeprop = self.builder.get_object("treeprop")
        treeprop.set_cursor((0,), treeprop.get_column(0))
        treeprop.get_selection().select_path((0,))
        self.builder.get_object("dialogvmprop").show()
        return vm["other_config"]

    def set_custom_fields_values(self):
        for config in self.other_config:
            if "XenCenter.CustomFields." in config:
                if config[23:] in self.vboxchildtext:
                     self.vboxchildtext[config[23:]].set_text(self.other_config[config])

    def fill_custom_fields_table(self, add=False):
        pool_ref =  self.xc_servers[self.selected_host].all_pools.keys()[0]
        self.vboxchildtext = {}
        if "XenCenter.CustomFields" in self.xc_servers[self.selected_host].all_pools[pool_ref]["gui_config"]:
           for ch in self.builder.get_object("vboxcustomfields").get_children():
               self.builder.get_object("vboxcustomfields").remove(ch)
            
           dom =  xml.dom.minidom.parseString(
                   self.xc_servers[self.selected_host].all_pools[pool_ref]["gui_config"]["XenCenter.CustomFields"])
           for node in dom.getElementsByTagName("CustomFieldDefinition"):
               name = node.attributes.getNamedItem("name").value
               if name not in self.vboxchildtext:
                   vboxframe = gtk.Frame()
                   vboxframe.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
                   vboxframe.set_size_request(500,30)
                   vboxchild = gtk.Fixed()
                   vboxchild.set_size_request(500,30)
                   vboxevent = gtk.EventBox()
                   vboxevent.add(vboxchild)
                   vboxchildlabel = gtk.Label()
                   vboxchildlabel.set_selectable(True)
                   vboxchildlabel.set_label(name)
                   vboxchild.put(vboxchildlabel, 5, 5)
                   self.vboxchildtext[name] = gtk.Entry()
                   self.vboxchildtext[name].set_size_request(200,20)
                   vboxchild.put(self.vboxchildtext[name], 300, 5)
                   vboxevent.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
                   self.builder.get_object("vboxcustomfields").pack_start(vboxevent, False, False, 0)
                   self.builder.get_object("vboxcustomfields").show_all()
        if add:
            self.set_custom_fields_values()
        
    def on_properties_activate(self, widget, data=None):
        """
        Function called when you click on "Properties" window/menuitem for all elements
        """
        self.fill_custom_fields_table()  

        # TODO: comment code
        self.propmodelfilter.refilter()
        self.builder.get_object("tabprops").set_current_page(0)
        if gtk.Buildable.get_name(widget) == "btstorageproperties" or gtk.Buildable.get_name(widget) == "btstgproperties":
            other_config = self.fill_btstorage_properties(widget)
        elif gtk.Buildable.get_name(widget) == "bthostnetworkproperties":
            other_config = self.fill_host_network_properties(widget)
        elif gtk.Buildable.get_name(widget) == "menuitem_server_prop" or self.selected_type == "host":
            other_config = self.fill_server_properties(widget)
        elif self.selected_type == "storage":
            other_config = self.fill_storage_properties()
        elif self.selected_type == "pool":
            other_config = self.fill_pool_properties()
        elif self.selected_type == "vm" or self.selected_type == "template" or self.selected_type == "custom_template":
            self.selected_widget = widget
            other_config = self.fill_vm_properties()

        self.other_config = other_config 
        self.set_custom_fields_values()


        

