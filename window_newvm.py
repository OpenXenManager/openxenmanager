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
import datetime
import gtk
from threading import Thread
class oxcWindowNewVm:
    """
    Class to manage "new vm" window
    """
    def on_finishwindownewvm_clicked(self, widget, data=None):
        """
        Function called when you press "Finish" on newvm window
        """
        treetemplates = self.builder.get_object("treetemplates")
        listtemplates = self.modelfiltertpl
        treenewvmhosts = self.builder.get_object("treenewvmhosts")
        listnewvmhosts = self.builder.get_object("listnewvmhosts")

        selection = treetemplates.get_selection()
        if selection.get_selected()[1] == None:
            iter = listtemplates.get_iter((0,1))
        else:
            iter = selection.get_selected()[1]
        ref = listtemplates.get_value(iter, 2)

        selection = treenewvmhosts.get_selection()
        if selection.get_selected()[1] == None:
            iter = listnewvmhosts.get_iter((0,1))
        else:
            iter = selection.get_selected()[1]
        host = listnewvmhosts.get_value(iter, 3)
        newvmdata = {}
        newvmdata['ref'] = ref
        newvmdata['host'] = host
        newvmdata['name'] = self.builder.get_object("entrynewvmname").get_text()
        tb = self.builder.get_object("entrynewvmdescription").get_buffer()
        newvmdata['description'] =  tb.get_text(tb.get_start_iter(), tb.get_end_iter())
        newvmdata['startvm'] = self.builder.get_object("checkstartvm").get_active()
        newvmdata['location_url'] = self.builder.get_object("radiobutton1_data").get_text()
        newvmdata['location'] = self.newvmdata['location']
        data = self.builder.get_object(newvmdata['location'] + "_data")
        if newvmdata['location'] != "radiobutton1" and data and data.get_active_iter():
            newvmdata['vdi'] = data.get_model().get_value(data.get_active_iter(), 1)
        else:
            newvmdata['vdi'] = None
        newvmdata['numberofvcpus'] =  self.builder.get_object("numberofvcpus").get_value()
        newvmdata['memorymb'] =  self.builder.get_object("initialmemory").get_value()
        newvmdata['entrybootparameters'] = self.builder.get_object("entrybootparameters").get_text()

        Thread(target=self.xc_servers[self.selected_host].create_newvm, args=(newvmdata,)).start()
        self.builder.get_object("window_newvm").hide()

    def on_nextwindownewvm_clicked(self, widget, data=None):
        """
        Function called when you press "Next" on newvm window
        """
        tabboxnewvm = self.builder.get_object("tabboxnewvm")

        if not self.builder.get_object("lblnewvm2").get_property("visible") \
                and tabboxnewvm.get_current_page() == 1:
            step = 2
        else:
            step = 1

        tabboxnewvm.set_current_page(tabboxnewvm.get_current_page()+step)

        exlabel = self.builder.get_object("lblnewvm" + str(tabboxnewvm.get_current_page()-step)).get_label()
        label = self.builder.get_object("lblnewvm" + str(tabboxnewvm.get_current_page())).get_label()
        exlabel = exlabel.replace('<span background="blue" foreground="white">', '').replace('<b>', '').replace('</span>', '').replace('</b>', '')
        exlabel = "  <b>%-35s</b>" % exlabel.strip()
        label = '  <span background="blue" foreground="white"><b>%-35s</b></span>' % label[2:]
        self.builder.get_object("lblnewvm" + str(tabboxnewvm.get_current_page()-step)).set_markup(exlabel)
        self.builder.get_object("lblnewvm" + str(tabboxnewvm.get_current_page())).set_markup(label)

    def on_previouswindownewvm_clicked(self, widget, data=None):
        """
        Function called when you press "Previous" on newvm window
        """
        tabboxnewvm = self.builder.get_object("tabboxnewvm")
        if not self.builder.get_object("lblnewvm2").get_property("visible") \
                and tabboxnewvm.get_current_page() == 3:
            step = 2
        else:
            step = 1

        tabboxnewvm.set_current_page(tabboxnewvm.get_current_page()-step)

        exlabel = self.builder.get_object("lblnewvm" + str(tabboxnewvm.get_current_page()+1)).get_label()
        label = self.builder.get_object("lblnewvm" + str(tabboxnewvm.get_current_page())).get_label()
        exlabel = exlabel.replace('<span background="blue" foreground="white">', '').replace('<b>', '').replace('</span>', '').replace('</b>', '')
        exlabel = "  <b>%-35s</b>" % exlabel.strip()
        label = '  <span background="blue" foreground="white"><b>%-35s</b></span>' % label[2:]
        self.builder.get_object("lblnewvm" + str(tabboxnewvm.get_current_page()+step)).set_markup(exlabel)
        self.builder.get_object("lblnewvm" + str(tabboxnewvm.get_current_page())).set_markup(label)

    def on_cancelwindownewvm_clicked(self, widget, data=None):
        """
        Function called when you press "Cancel" on newvm window
        """
        self.builder.get_object("window_newvm").hide()

    def on_tabboxnewvm_switch_page(self, widget, data=None, data2=None):
        """
        Function called when you press "Switch page" on newvm tabbox
        """
        self.builder.get_object("previouswindownewvm").set_sensitive(widget.get_current_page() > 0)
        self.builder.get_object("nextwindownewvm").set_sensitive(widget.get_current_page() != 7)
        self.builder.get_object("finishwindownewvm").set_sensitive(widget.get_current_page() == 7)
        if widget.get_current_page() == 1:
            listnewvmstorage = self.builder.get_object("listnewvmstorage")
            treetemplates = self.builder.get_object("treetemplates")
            listtemplates = self.modelfiltertpl
            treenewvmhosts = self.builder.get_object("treenewvmhosts")
            listnewvmhosts = self.builder.get_object("listnewvmhosts")

            selection = treetemplates.get_selection()
            if selection.get_selected()[1] == None:
                iter = listtemplates.get_iter((0,1))
            else:
                iter = selection.get_selected()[1]
            ref = listtemplates.get_value(iter, 2)

            selection = treenewvmhosts.get_selection()
            if selection.get_selected()[1] == None:
                iter = listnewvmhosts.get_iter((0,1))
            else:
                iter = selection.get_selected()[1]
            host = listnewvmhosts.get_value(iter, 3)

            self.xc_servers[self.selected_host].fill_listnewvmstorage(listnewvmstorage,
            ref, host, self.xc_servers[self.selected_host].default_sr)

            # Fill list new disk 
            listnewvmstorage = self.builder.get_object("listnewvmstorage")
            treenewvmstorage = self.builder.get_object("treenewvmstorage")
            listnewvmdisk = self.builder.get_object("listnewvmdisk")
            treenewvmdisk = self.builder.get_object("treenewvmdisk")
            # And fill disks from template information
            defsr = self.xc_servers[self.selected_host].fill_listnewvmdisk(listnewvmdisk, host)
            # And set the selection in the first disk
            treenewvmstorage.set_cursor((defsr,0), treenewvmstorage.get_column(0))
            treenewvmstorage.get_selection().select_path((defsr,0))
            treenewvmdisk.set_cursor((defsr,0), treenewvmdisk.get_column(0))
            treenewvmdisk.get_selection().select_path((defsr,0))

            # Installation method
            self.builder.get_object("entrybootparameters").set_text(
                self.xc_servers[self.selected_host].all_vms[ref]['PV_args']
                )
            # Get "other_config" from selected template, other_config contains information about install
            other_config = self.xc_servers[self.selected_host].all_vms[ref]['other_config']
            # If other_config contains "install-methods" (ftp, nfs, http) or via cdrom
            if "install-methods" in other_config:
               methods = other_config["install-methods"]
               # If contains nfs/http or ftp, show fields
               if methods.count("nfs") == 0 and methods.count("http") == 0 and methods.count("ftp") == 0:
                   self.builder.get_object("radiobutton1_data").hide()
                   self.builder.get_object("radiobutton1").hide()
                   self.builder.get_object("fixed22").hide()
                   self.builder.get_object("radiobutton1").set_active(False)
                   self.builder.get_object("radiobutton2").set_active(True)
                   self.builder.get_object("radiobutton2_data").set_sensitive(True)
                   self.builder.get_object("radiobutton2_data").set_active(0)
               else:
                   # Else disable installation via network
                   self.builder.get_object("radiobutton1_data").show()
                   self.builder.get_object("radiobutton1").show()
                   self.builder.get_object("fixed22").show()
                   self.builder.get_object("radiobutton1").set_active(True)
                   self.builder.get_object("radiobutton2").set_active(False)
                   self.builder.get_object("radiobutton2_data").set_sensitive(False)


    def on_cancelnewvmdisk_clicked(self, widget, data=None):
        """
        Function called when you cancel the "new disk" window on "new vm" assistant
        """
        newvmdisk = self.builder.get_object("newvmdisk")
        newvmdisk.hide()

    def on_addnewvmstorage_clicked(self, widget, data=None):
        """
        Function called when you press "new disk" window on "new vm" assistant
        """
        newvmdisk = self.builder.get_object("newvmdisk")
        self.newvmdata['storage_editing'] = False
        newvmdisk.show()

    def on_deletenewvmnetwork_clicked(self, widget, data=None):
        """
        Function called when you remove a network interface from new vm networks list
        """
        treenewvmnetwork =  self.builder.get_object("treenewvmnetwork")
        listnewvmnetwork =  self.builder.get_object("listnewvmnetworks")
        selection = treenewvmnetwork.get_selection()
        if selection.get_selected()[1] == None:
            iter = listnewvmnetwork.get_iter((0,1))
        else:
            iter = selection.get_selected()[1]
        self.listnetworks.remove(iter)
    def on_addnewvmnetwork_clicked(self, widget, data=None):
        """
        Function called when add a new network
        """
        # Increase n_networks value
        n_networks = self.listnetworks.__len__()+1
        # Get the first network by default
        network = self.xc_servers[self.selected_host].first_network()
        # Get the ref of first network
        network_ref = self.xc_servers[self.selected_host].first_network_ref()
        # Add to list
        self.listnetworks.append(["interface " + str(n_networks),
                "auto-generated",
                network, network_ref
               ])
    def on_editnewvmstorage_clicked(self, widget, data=None):
        """
        Function called when you press edit storage on "new vm" process
        """
        newvmdisk = self.builder.get_object("newvmdisk")
        self.newvmdata['storage_editing'] = True
        # Set the current values to differents elements
        listnewvmstorage = self.builder.get_object("listnewvmstorage")
        self.builder.get_object("disksize").set_value(
            float(listnewvmstorage.get_value(self.newvmdata['last_diskiter_selected'],0)))
        treenewvmdisk =  self.builder.get_object("treenewvmdisk")
        listnewvmdisk =  self.builder.get_object("listnewvmdisk")
        selection = treenewvmdisk.get_selection()
        ref = listnewvmstorage.get_value(self.newvmdata['last_diskiter_selected'],3)
        for i in range(0, listnewvmdisk.__len__()):
            if ref == listnewvmdisk.get_value(listnewvmdisk.get_iter((i,)), 4):
                print ref
                treenewvmdisk.set_cursor((i,), treenewvmdisk.get_column(1))
                treenewvmdisk.get_selection().select_path((i,))

        # Show a "new vm disk" window
        newvmdisk.show()
    def on_acceptnewvmdisk_clicked(self, widget, data=None):
        """
        Function called when you press add a new storage on "new vm" process or accept "edit storage"
        """
        listnewvmstorage = self.builder.get_object("listnewvmstorage")
        size =  self.builder.get_object("disksize").get_value()
        disk =  self.newvmdata['last_disk_selected']
        disk_name = self.xc_servers[self.selected_host].all_storage[disk]['name_label'] + " on " \
                  +  self.xc_servers[self.selected_host].all_hosts[self.newvmdata['host']]['name_label']
        shared = str(self.xc_servers[self.selected_host].all_storage[disk]['shared'])
        if self.newvmdata['storage_editing'] == False:
            # If we are not editing, then add to list
            listnewvmstorage.append([size, disk_name, shared, disk])
        else:
            # Else update values from list
            iter = self.newvmdata['last_diskiter_selected']
            listnewvmstorage.set_value(iter, 0, size)
            listnewvmstorage.set_value(iter, 1, disk_name)
            listnewvmstorage.set_value(iter, 2, shared)
            listnewvmstorage.set_value(iter, 3, disk)
        # Hide the window
        self.builder.get_object("newvmdisk").hide()
    def on_deletenewvmstorage_clicked(self, widget, data=None):
        """
        Function called when you delete a storage on "new vm" process
        """
        listnewvmstorage = self.builder.get_object("listnewvmstorage")
        # Remove from list
        listnewvmstorage.remove(self.newvmdata['last_diskiter_selected'])
    def on_newvmtreeviewhosts_row_activated(self, widget, data=None):
        """
        Function called when you select a host on "new vm" assistant
        """
        listnewvmhosts = self.builder.get_object("listnewvmhosts")
        treenewvmhosts =  self.builder.get_object("treenewvmhosts")
        selection = treenewvmhosts.get_selection()
        # Get selected host
        if selection.get_selected()[1] == None:
            # If none selected, get the first available host
            iter = listnewvmhosts.get_iter((self.xc_servers[self.selected_host].get_path_available_host(),1))
        else:
            iter = selection.get_selected()[1]
        # Set reference host to "newvmdata" struct
        self.newvmdata['host'] = listnewvmhosts.get_value(iter, 3)
        host= self.xc_servers[self.selected_host].all_hosts[self.newvmdata['host']]
        host_metrics = self.xc_servers[self.selected_host].all_host_metrics[host['metrics']]
        # Fill host info on "set memory/vcpu" window (only for information) 
        self.builder.get_object("lblnewvmhost").set_label(host['name_label'])
        self.builder.get_object("lblnewvmcpus").set_label(str(len(host['host_CPUs'])))
        self.builder.get_object("lblnewvmtotalmemory").set_label(self.convert_bytes(host_metrics['memory_total']))
        self.builder.get_object("lblnewvmfreememory").set_label(self.convert_bytes(host_metrics['memory_free']))
    def on_treetemplates_row_activated(self, widget, data=None, data2=None):
        """
        Function called when you select a template to create a new vm
        """
        treetemplates =  self.builder.get_object("treetemplates")
        listtemplates =  self.modelfiltertpl
        selection = treetemplates.get_selection()
        # Get the selected template
        if selection.get_selected()[1] == None:
            # Get the first template if selection is empty
            iter = listtemplates.get_iter((0,))
        else:
            iter = selection.get_selected()[1]
        # Fill template info
        self.builder.get_object("lblnewvmname").set_label(listtemplates.get_value(iter, 1))
        self.builder.get_object("lblnewvminfo").set_label(
          self.xc_servers[self.selected_host].all_vms[listtemplates.get_value(iter, 2)]['name_description'])
        self.builder.get_object("entrynewvmname").set_text(listtemplates.get_value(iter, 1) + " (" + str(datetime.date.today()) + ")")

        ref = listtemplates.get_value(iter, 2)
        vm = self.xc_servers[self.selected_host].all_vms[ref]
        self.builder.get_object("numberofvcpus").set_value(float(int(vm['VCPUs_max'])))
        self.builder.get_object("initialmemory").set_value(float(int(vm['memory_static_max'])/1024/1024))
        self.builder.get_object("disksize").set_value(float(5))



        # Check if selected template should be installed with cd or not
        # If postinstall is true, then will be cloned, else you will be specifiy a method of installation
        if "postinstall" in self.xc_servers[self.selected_host].all_vms[listtemplates.get_value(iter, 2)]['other_config'] or \
                 self.xc_servers[self.selected_host].all_vms[listtemplates.get_value(iter, 2)]['last_booted_record'] != "":
            self.builder.get_object("lblnewvm2").hide()
        else:
            self.builder.get_object("lblnewvm2").show()

    def on_treenewvmdisk_row_activated(self, widget, data=None, data2=None):
        """
        Function called when you select a disk on "new disk" in "new vm" assistant only for set "last_disk_selected" variable
        """
        treenewvmdisk =  self.builder.get_object("treenewvmdisk")
        listnewvmdisk =  self.builder.get_object("listnewvmdisk")
        selection = treenewvmdisk.get_selection()
        # Get the selected disk
        if selection.get_selected()[1] == None:
            # Or get the first
            iter = listnewvmdisk.get_iter((0,1))
        else:
            iter = selection.get_selected()[1]
        # Set inside newvmdata struct
        self.newvmdata['last_disk_selected'] = listnewvmdisk.get_value(iter, 4)
    def on_treenewvmstorage_row_activated(self, widget, data=None, data2=None):
        """
        Function called when you select a disk, is used to set a variable called "last_disk_selected"
        """
        treenewvmstorage =  self.builder.get_object("treenewvmstorage")
        listnewvmstorage =  self.builder.get_object("listnewvmstorage")
        selection = treenewvmstorage.get_selection()
        # Get the selected disk
        selection.set_mode(gtk.SELECTION_SINGLE)
        if selection.get_selected()[1] == None:
            if listnewvmstorage.__len__() > 0:
                # Or get the first
                iter = listnewvmstorage.get_iter((0,))
            else:
                iter = None
        else:
            iter = selection.get_selected()[1]
        # Set inside newvmdata struct
        self.newvmdata['last_diskiter_selected'] = iter

    def on_treenewvmnetwork_cursor_changed(self, widget, data=None, data2=None):
        """
        Function called when you select a network, is used to set a variable called "last_networkiter_selected"
        """
        treenewvmnetwork =  self.builder.get_object("treenewvmnetwork")
        listnewvmnetwork =  self.builder.get_object("listnewvmnetworks")
        selection = treenewvmnetwork.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        if selection.get_selected()[1] == None:
            iter = listnewvmnetwork.get_iter((0,1))
        else:
            iter = selection.get_selected()[1]
        self.newvmdata['last_networkiter_selected'] = iter

    def on_newvm_prepare(self, widget, data=None):
        """
        Function called when you select a network, is used to set a variable called "last_networkiter_selected"
        """
        if widget.get_current_page() == 2:
            # If page is  "installation method" then enable/disable installation options
            # Set the boot parameters in specify label from selected template
            pass    
        if widget.get_current_page() == 3:
            # After specify name and description.. set to newvmdata struct
            tb = self.builder.get_object("entrynewvmdescription").get_buffer()
            self.newvmdata['name'] =  self.builder.get_object("entrynewvmname").get_text()
            self.newvmdata['description'] =  tb.get_text(tb.get_start_iter(), tb.get_end_iter())
        if widget.get_current_page() == 3:
            # After the choose installation method.. set the location on newvmdata struct
            self.newvmdata['location_url'] = self.builder.get_object("radiobutton1_data").get_text()
            if self.newvmdata['location'] != "radiobutton1":
                data = self.builder.get_object(self.newvmdata['location'] + "_data")
                self.newvmdata['vdi'] = data.get_model().get_value(data.get_active_iter(), 1)
            else:
                self.newvmdata['vdi'] = None
            #print self.newvmdata['vdi']
            #print "Elegido location"
        if widget.get_current_page() == 4:
            # After choose installation method, set vcpus and memory from template information
            if "ref" in self.newvmdata:
                vm = self.xc_servers[self.selected_host].all_vms[self.newvmdata['ref']]
                self.builder.get_object("numberofvcpus").set_value(float(int(vm['VCPUs_max'])))
                self.builder.get_object("initialmemory").set_value(float(int(vm['memory_static_max'])/1024/1024))
                self.builder.get_object("disksize").set_value(float(5))


            
        if widget.get_current_page() == 5:
            # After specify number of VCPUs, memory and boot parameters, set into newvmdata struct
            self.newvmdata['numberofvcpus'] =  self.builder.get_object("numberofvcpus").get_value()
            self.newvmdata['memorymb'] =  self.builder.get_object("initialmemory").get_value()
            self.newvmdata['entrybootparameters'] = self.builder.get_object("entrybootparameters").get_text()
            #print "Elegido number of vcpus and memory"
        self.newvm.set_page_complete(widget.get_nth_page(widget.get_current_page()), True)
    def forward_page(self, current_page, user_data):
        """
        Function called to know what is the next page
        """
        if current_page == 1:
            # If has not installation method (template clone), then step to page 3
            if "ref" in self.newvmdata:
                if "postinstall" in self.xc_servers[self.selected_host].all_vms[self.newvmdata['ref']]['other_config']:
                    return current_page+2
        # Else only increment one to actual page
        return current_page+1
    def on_radiobutton1_activate(self, widget, data=None):
        """
        FIXME: enable or disable elements depends the selection
        """
        if widget.state == 2:
            for data in ['radiobutton1', 'radiobutton2', 'radiobutton3']:
                if data == gtk.Buildable.get_name(widget): 
                    self.builder.get_object(data + "_data").set_sensitive(True)
                    if data != "radiobutton1":
                        if self.builder.get_object(data + "_data").get_active() == -1:
                             self.builder.get_object(data + "_data").set_active(0)
                else:
                    self.builder.get_object(data + "_data").set_sensitive(False)
        self.newvmdata['location'] = gtk.Buildable.get_name(widget) 
    def on_networkcolumn_changed(self, widget, data=None, data2=None):
        """
        Function called when you change the "network" listbox on list of networks
        """
        if "last_networkiter_selected" in self.newvmdata:
            self.listnetworks.set_value(self.newvmdata['last_networkiter_selected'], 2,
                 self.listnetworkcolumn.get_value(data2, 0))
            self.listnetworks.set_value(self.newvmdata['last_networkiter_selected'], 3,
                 self.listnetworkcolumn.get_value(data2, 1))

