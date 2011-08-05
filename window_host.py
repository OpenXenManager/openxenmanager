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
from window_host_nics import * 
from window_host_network import * 
from capabilities import capabilities_conf_text
from threading import Thread
from messages import messages_header
import gtk

class oxcWindowHost(oxcWindowHostNics, oxcWindowHostNetwork):
    """
    Class to manage host tabs, host properties and host functions 
    """

    def on_btleavedomain_clicked(self, widget, data=None):
        """
        Press "Leave Domain" on Users tab
        """
        pass

    def on_btjoindomain_clicked(self, widget, data=None):
        """
        Press "Join Domain" on Users tab
        """
        pass

    def on_btadduser_clicked(self, widget, data=None):
        """
        Press "Add user" on Users tab
        """
        pass

    def on_btremoveuser_clicked(self, widget, data=None):
        """
        Press "Remove user" on Users tab
        """
        pass

    def on_btlogoutuser_clicked(self, widget, data=None):
        """
        Press "Logout User" on Users tab
        """
        pass

    def on_treeusers_cursor_changed(self, widget, data=None):
        """
        Selected row in treeusers treeview
        """
        pass

    def on_btchangerole_clicked(self, widget, data=None):
        """
        Press "Join Domain" on Users tab
        """
        pass

    def on_cancelfileexportmap_clicked(self, widget, data=None):
        """
        Cancel dialog file export map to png
        """
        self.builder.get_object("fileexportmap").hide() 
    def on_acceptfileexportmap_clicked(self, widget, data=None):
        """
        Accept dialog file export map to png
        """
        filename = self.builder.get_object("fileexportmap").get_filename()
        pixbuf = gtk.gdk.Pixbuf( gtk.gdk.COLORSPACE_RGB, False, 8, 640, 480)
        pixmap = self.windowmap.widget.get_snapshot()
        pixbuf.get_from_drawable(pixmap, pixmap.get_colormap(), 0, 0, 0, 0, -1, -1)
        pixbuf.save(filename, 'png')
        self.builder.get_object("fileexportmap").hide() 
    
    def on_btexportmap_clicked(self, widget, data=None):
        """
        Function to export current map to PNG file
        """
        self.builder.get_object("fileexportmap").set_current_name(self.selected_name + ".png") 
        self.builder.get_object("fileexportmap").show() 
    def on_check_map_options(self, widget, data=None):
        """
        Function called when you check or uncheck a map option
        """
        if not "maps" in self.config:
             self.config["maps"] = {}
        self.config["maps"][gtk.Buildable.get_name(widget)] = str(widget.get_active())
        self.config.write()
        self.update_maps()

    def on_acceptfilenewupdate_clicked(self, widget, data=None):
        # When you press accept "new update" file chooser
        filename = self.builder.get_object("filenewupdate").get_filename()
        Thread(target=self.xc_servers[self.selected_host].upload_patch, \
                args=(self.selected_ref, filename)).start()

        self.builder.get_object("updatemanager").hide()
        self.builder.get_object("filenewupdate").hide()

    def on_cancelfilenewupdate_clicked(self, widget, data=None):
        # When you press cancel "new update" file chooser
        self.builder.get_object("filenewupdate").hide()

    def on_btuploadnewupdate_clicked(self, widget, data=None):
        # When you press "Upload new update" (patch)
        self.builder.get_object("filterfilenewupdate").add_pattern("*.xsupdate")
        self.builder.get_object("filenewupdate").show()

    def on_btremoveupdate_clicked(self, wiget, data=None):
        # When you press "remove" (patch)
        treeupdates = self.builder.get_object("treeupdates")
        iter = treeupdates.get_selection().get_selected()[1]
        if iter:                
            listupdates = self.builder.get_object("listupdates")
            patch_ref = listupdates.get_value(iter, 0)
            self.xc_servers[self.selected_host].remove_patch(self.selected_ref, patch_ref)
        self.builder.get_object("updatemanager").hide()

    def on_btapplypatch_clicked(self, widget, data=None):
        # When you press "apply patch"
        treeupdates = self.builder.get_object("treeupdates")
        treeupdatestatus = self.builder.get_object("treeupdatestatus")
        iter = treeupdates.get_selection().get_selected()[1]
        if iter:                
            listupdates = self.builder.get_object("listupdates")
            patch_ref = listupdates.get_value(iter, 0)
            iter = treeupdatestatus.get_selection().get_selected()[1]
            if iter:                
                listupdatestatus = self.builder.get_object("listupdatestatus")
                host_ref = listupdatestatus.get_value(iter, 0)
                self.xc_servers[self.selected_host].apply_patch(host_ref, patch_ref)
        self.builder.get_object("updatemanager").hide()

    def on_treeupdatestatus_cursor_changed(self, widget, data=None):
        # When you select a host in update manager
        iter = widget.get_selection().get_selected()[1]
        if iter:                
            listupdatestatus = self.builder.get_object("listupdatestatus")
            self.builder.get_object("btapplypatch").set_sensitive(listupdatestatus.get_value(iter, 2))
    def on_treeupdates_cursor_changed(self, widget, data=None):
        # When you select a patch
        iter = widget.get_selection().get_selected()[1]
        if iter:                
            listupdates = self.builder.get_object("listupdates")
            ref = listupdates.get_value(iter, 0)
            name = self.xc_servers[self.selected_host].all_pool_patch[ref]['name_label']
            desc = self.xc_servers[self.selected_host].all_pool_patch[ref]['name_description']
            version = self.xc_servers[self.selected_host].all_pool_patch[ref]['version']
            guidance = self.xc_servers[self.selected_host].all_pool_patch[ref]['after_apply_guidance']
            self.builder.get_object("lblupdatename").set_label(name)
            self.builder.get_object("lblupdatedesc").set_label(desc)
            self.builder.get_object("lblupdateversion").set_label(version)
            guidance_text = ""
            for guid in guidance:
                if guid in messages_header:
                    guidance_text += messages_header[guid] + "\n"
                else:
                    guidance_text += guid
            self.builder.get_object("lblupdateguidance").set_label(guidance_text)
            host_patches = self.xc_servers[self.selected_host].all_pool_patch[ref]["host_patches"]
            self.builder.get_object("btremoveupdate").set_sensitive(len(host_patches) == 0)
            listupdatestatus = self.builder.get_object("listupdatestatus")
            listupdatestatus.clear()
            for host in self.xc_servers[self.selected_host].all_hosts.keys():
                name = self.xc_servers[self.selected_host].all_hosts[host]['name_label']
                found = False
                for host_patch in host_patches:
                    host2 = self.xc_servers[self.selected_host].all_host_patch[host_patch]['host']
                    if host == host2:
                        found = True
                        timestamp = self.xc_servers[self.selected_host].all_host_patch[host_patch]['timestamp_applied'] 
                        patch_text = "<span foreground='green'>%s - applied (%s)</span>" % (name, \
                            self.xc_servers[self.selected_host].format_date(timestamp))
                        listupdatestatus.append([host, patch_text, False])
                        
                if not found:
                    patch_text = "<span foreground='red'>%s - not applied</span>" % (name)
                    listupdatestatus.append([host, patch_text, True])

    
    def on_closeupdatemanager_clicked(self, widget, data=None):
        """
        Function called when you close "update manager" window
        """
        self.builder.get_object("updatemanager").hide()

    def on_txttemplatesearch_changed(self, widget, data=None):
        """
        Function called when you type something on search template list (newvm)
        """
        self.modelfiltertpl.refilter()

    def update_report_total_size_time(self):
        """
        Update the total size and the total time on report status window
        """
        treereport = self.builder.get_object("treereport")
        listreport = self.builder.get_object("listreport")
        totalsize, totaltime = 0, 0
        for i in range(0, listreport.__len__()):
            iter = listreport.get_iter((i,))
            if listreport.get_value(iter, 1):
                totalsize += listreport.get_value(iter, 7)
                totaltime += listreport.get_value(iter, 8)

        self.builder.get_object("lblreportotalsize").set_label("< %s" % (self.convert_bytes(totalsize)))
        self.builder.get_object("lblreportotaltime").set_label("< %d minutes" % (int(totaltime)/60))
    def on_cellrenderertoggle1_toggled(self, widget, data=None):
        """
        Function called when you change the state of checkbox on report tree
        """                                 
        treereport = self.builder.get_object("treereport")
        listreport = self.builder.get_object("listreport")
        iter = treereport.get_selection().get_selected()[1]
        if iter:                
            listreport.set_value(iter, 1, not widget.get_active())
            self.update_report_total_size_time()
    def on_treereport_cursor_changed(self, widget, data=None):
        """
        Function called when you select a item on report
        """                                 
        treereport = self.builder.get_object("treereport")
        listreport = self.builder.get_object("listreport")
        iter = treereport.get_selection().get_selected()[1]
        if iter:
            self.builder.get_object("lblreportdesc").set_label(listreport.get_value(iter, 4))
            self.builder.get_object("lblreportsize").set_label(listreport.get_value(iter, 5))
            self.builder.get_object("lblreporttime").set_label(listreport.get_value(iter, 6) + " seconds")
            conf = listreport.get_value(iter, 9)
            self.builder.get_object("lblreportconf").set_label(capabilities_conf_text[conf-1])

    def on_acceptstatusreport_clicked(self, widget, data=None):
        """
        Function called when you accept status report dialog
        """
        from time import strftime
        self.builder.get_object("filesavereport").set_current_name(strftime("status-report-%Y-%m-%d-%H-%M-%S.tar"))
        self.builder.get_object("filesavereport").show()
        self.builder.get_object("statusreport").hide()
    def on_acceptfilereport_clicked(self, widget, data=None):
        """
        Function called when you accept save report file chooser dialog
        """
        treereport = self.builder.get_object("treereport")
        listreport = self.builder.get_object("listreport")
        totalsize, totaltime = 0, 0
        refs = []
        for i in range(0, listreport.__len__()):
            iter = listreport.get_iter((i,))
            if listreport.get_value(iter, 1):
                refs.append(listreport.get_value(iter, 0))
        destination = self.builder.get_object("filesavereport").get_filename()
        Thread(target=self.xc_servers[self.selected_host].host_download_status_report, \
                args=(self.selected_ref, ",".join(refs), destination, self.selected_name)).start()
        self.builder.get_object("filesavereport").hide()

    def on_cancelfilereport_clicked(self, widget, data=None):
        """
        Function called when you cancel save report file chooser dialog
        """
        self.builder.get_object("filesavereport").hide()

    def on_cancelstatusreport_clicked(self, widget, data=None):
        """
        Function called when you cancel status report dialog
        """
        self.builder.get_object("statusreport").hide()

    def on_clearallstatusreport_clicked(self, widget, data=None):
        """
        Uncheck all checkbox for each status report
        """
        treereport = self.builder.get_object("treereport")
        listreport = self.builder.get_object("listreport")
        for i in range(0, listreport.__len__()):
            iter = listreport.get_iter((i,))
            listreport.set_value(iter, 1, False)
        self.update_report_total_size_time()    
    def on_selectallstatusreport_clicked(self, widget, data=None):
        """
        Check all checkbox for each status report
        """
        treereport = self.builder.get_object("treereport")
        listreport = self.builder.get_object("listreport")
        for i in range(0, listreport.__len__()):
            iter = listreport.get_iter((i,))
            listreport.set_value(iter, 1, True) 
        self.update_report_total_size_time()    

    def on_txtcurrentpw_changed(self, widget, data=None):
        """
        Function called when you change text on "current password", "type new password" or "re-enter new password"
        On change server password window
        """
        # If some textfield is empty, then disable button
        if len(self.builder.get_object("txtcurrentpw").get_text()) and \
           len(self.builder.get_object("txtnewpw").get_text()) and \
           len(self.builder.get_object("txtrenewpw").get_text()) and \
           (self.builder.get_object("txtnewpw").get_text() == self.builder.get_object("txtrenewpw").get_text()):
            self.builder.get_object("acceptchangepassword").set_sensitive(True)
        else:
            self.builder.get_object("acceptchangepassword").set_sensitive(False)
    def on_cancelchangepassword_clicked(self, widget, data=None):
        """
        Function called when you press "Cancel" button on "Change Server Password" window
        """
        self.builder.get_object("changepassword").hide()
    def on_acceptchangepassword_clicked(self, widget, data=None):
        """
        Function called when you press "OK" button on "Change Server Password" window
        """
        old = self.xc_servers[self.selected_host].password
        typed = self.builder.get_object("txtcurrentpw").get_text()
        if typed != old:
            self.builder.get_object("lblwrongpw").show()
        else:
            new = self.builder.get_object("txtnewpw").get_text()
            self.xc_servers[self.selected_host].change_server_password(old, new) 
            self.builder.get_object("changepassword").hide()
    def update_tab_host_nics(self):
        """
        Function called to fill host nics
        """
        if self.treeview.get_cursor()[1]:
            listhostnics = self.builder.get_object("listhostnics")
            host =  self.selected_host
            # Fill list "listhostnics" 
            self.xc_servers[host].fill_host_nics(self.selected_ref, \
                            listhostnics)
            treehostnics = self.builder.get_object("treehostnics")
            # Select the first as default
            treehostnics.set_cursor((0,), treehostnics.get_column(0))
            treehostnics.get_selection().select_path((0, ))
            iter = listhostnics.get_iter((0, ))
            # Get the reference of first selected
            ref = self.builder.get_object("listhostnics").get_value(iter, 8)
            nic_bond_master_of = self.xc_servers[self.selected_host].all_pif[ref]['bond_master_of']
            # If is already on a bond
            if len(nic_bond_master_of):
                # Enable remove bond button
                self.builder.get_object("bthostnicremove").set_sensitive(True)
            else:
                # Disable remove bond button
                self.builder.get_object("bthostnicremove").set_sensitive(False)

    def update_tab_host_network(self):
        """
        Function called to fill host networks
        """
        if self.treeview.get_cursor()[1]:
            listhostnetwork= self.builder.get_object("listhostnetwork")
            host =  self.selected_host
            # Fill list "listhostnetwork" 
            self.xc_servers[host].fill_host_network(self.selected_ref, \
                            listhostnetwork)
            treehostnetwork = self.builder.get_object("treehostnetwork")
            # Select the first as default
            treehostnetwork.set_cursor((0,), treehostnetwork.get_column(0))
            treehostnetwork.get_selection().select_path((0, 0))
            iter = listhostnetwork.get_iter((0,0))
            # Get the reference of first selected
            ref = self.builder.get_object("listhostnetwork").get_value(iter, 7)
            # Get the pifs from selected network 
            network_pifs = self.xc_servers[self.selected_host].all_network[ref]['PIFs']
            # Enable "remove network" by default
            self.builder.get_object("bthostnetworkremove").set_sensitive(True)
            for pif in network_pifs:
                # If is physical then disable it
                if self.xc_servers[self.selected_host].all_pif[pif]['physical'] == True:
                    self.builder.get_object("bthostnetworkremove").set_sensitive(False)
                    break
    def on_radiomgmtipmanual_toggled(self, widget, data=None):
        """
        On "management interface" radio "manual ip" selected
        """
        self.builder.get_object("txtmgmtip").set_sensitive(widget.get_active())
        self.builder.get_object("txtmgmtmask").set_sensitive(widget.get_active())
        self.builder.get_object("txtmgmtgw").set_sensitive(widget.get_active())

    def on_radiomgmtdnsmanual_toggled(self, widget, data=None):
        """
        On "management interface" radio "manual dns" selected
        """
        self.builder.get_object("txtmgmtdns1").set_sensitive(widget.get_active())
        self.builder.get_object("txtmgmtdns2").set_sensitive(widget.get_active())

    def on_cancelmgmtinterface_clicked(self, widget, data=None):
        """
        On "cancel" button pressed on "management interface"
        """
        self.builder.get_object("mgmtinterface").hide()

    def on_checkpoolserver_toggled(self, widget, data=None):
        """
        Function called on "new pool" window, when you check a server to join to pool
        """
        listpoolvms = self.builder.get_object("listpoolvms")
        iter = listpoolvms.get_iter((int(data),))
        # Field 4 (beginning on 0) contains if check could be modified
        if listpoolvms.get_value(iter, 4):
            # widget.get_active() contains last state: enabled o disabled
            listpoolvms.set(iter, 2, not widget.get_active())
        
    def on_cancelnewpool_clicked(self, widget, data=None):
        """
        On "cancel" button pressed on "new pool"
        """
        self.builder.get_object("newpool").hide()
    def on_acceptnewpool_clicked(self, widget, data=None):
        """
        On "accept" button pressed on "new pool"
        """
        listpoolvms = self.builder.get_object("listpoolvms")
        listpoolmaster = self.builder.get_object("listpoolmaster")
        combopoolmaster = self.builder.get_object("combopoolmaster")
        # If a master pool is selected..
        if combopoolmaster.get_active_iter():
            name = self.builder.get_object("txtpoolname").get_text()
            desc = self.builder.get_object("txtpooldesc").get_text()
            # Get the reference the selected iter
            ref = listpoolmaster.get_value(combopoolmaster.get_active_iter(), 0)
            # Create a pool
            self.xc_servers[ref].create_pool(name, desc)
            # For each server on treeview
            for i in range(0, listpoolvms.__len__()):
                iter = listpoolvms.get_iter((int(i),))
                # If is checked
                if listpoolvms.get_value(iter, 2):
                    host = listpoolvms.get_value(iter, 0)
                    # And is not "Master"
                    if listpoolvms.get_value(iter, 3) == "":
                        # Join to pool
                        self.xc_servers[host].join_pool(self.xc_servers[ref].host, self.xc_servers[ref].user, self.xc_servers[ref].password)
                    
        self.builder.get_object("newpool").hide()
    def on_combopoolmaster_changed(self, widget, data=None):
        # FIXME: active the selected on treeview and set as "Master"
        listpoolvms = self.builder.get_object("listpoolvms")
        listpoolmaster = self.builder.get_object("listpoolmaster")
        combopoolmaster = self.builder.get_object("combopoolmaster")
        if widget.get_active_iter():
            ref = listpoolmaster.get_value(widget.get_active_iter(),0)
            for i in range(0, listpoolvms.__len__()):
                iter = listpoolvms.get_iter((int(i),))
                if listpoolvms.get_value(iter, 3) == "Master":
                    listpoolvms.set(iter, 3, "", 2, False, 4, True)
                if listpoolvms.get_value(iter, 0) == ref:
                    listpoolvms.set(iter, 3, "Master", 2, True, 4, False)
    def on_canceldialogreconfigure_clicked(self, widget, data=None):
        """
        On "cancel" button pressed on confirmation of "management interface"
        """
        self.builder.get_object("dialogreconfigure").hide()
    def on_closewarninglicense_clicked(self, widget, data=None):
        """
        On "close" button pressed on warning alert
        """
        self.builder.get_object("warninglicense").hide()
    def on_accepthostdmesg_clicked(self, widget, data=None):
        """
        On "accept" button pressed on dmesg dialog
        """
        self.builder.get_object("hostdmesg").hide()

    def on_acceptdialogreconfigure_clicked(self, widget, data=None):
        """
        On "accept" button pressed on confirmation dialog to reconfigure interface
        """ 
        listmgmtinterfaces = self.builder.get_object("listmgmtinterfaces")
        treemgmtinterfaces = self.builder.get_object("treemgmtinterfaces")
        selection = treemgmtinterfaces.get_selection()
        pif_ref = listmgmtinterfaces.get_value(selection.get_selected()[1],0)
        combomgmtnetworks = self.builder.get_object("combomgmtnetworks")
        listmgmtnetworks = self.builder.get_object("listmgmtnetworks")
        iter = combomgmtnetworks.get_active_iter()
        # Get selected network and rest of elements
        network_ref = listmgmtnetworks.get_value(iter, 0)
        ip = self.builder.get_object("txtmgmtip").get_text()
        mask  = self.builder.get_object("txtmgmtmask").get_text()
        gw = self.builder.get_object("txtmgmtgw").get_text()
        dns1 = self.builder.get_object("txtmgmtdns1").get_text()
        dns2 = self.builder.get_object("txtmgmtdns2").get_text()
        radiomgmtipdhcp = self.builder.get_object("radiomgmtipdhcp")
        radiomgmtdnsdhcp = self.builder.get_object("radiomgmtdnsdhcp")
        if radiomgmtdnsdhcp.get_active():
            dns = ""
        else:
            dns = dns1 + "," + dns2
        if radiomgmtipdhcp.get_active():
            configuration_mode = "DHCP"
        else:
            configuration_mode = "Static"    
        # Call to reconfigure interface with specified configuration
        self.xc_servers[self.selected_host].reconfigure_pif(pif_ref, configuration_mode, ip, mask, gw, dns, self.selected_ref)
        # Hide both windows: management window and confirmation
        self.builder.get_object("dialogreconfigure").hide()
        self.builder.get_object("mgmtinterface").hide()
    def on_acceptmgmtinterface_clicked(self, widget, data=None):
        """
        On "accept" button pressed on confirmation dialog to reconfigure interface
        change is a variable, if is False doesn't change anything, if is True show reconfigure window confirmation
        """ 
        listmgmtinterfaces = self.builder.get_object("listmgmtinterfaces")
        treemgmtinterfaces = self.builder.get_object("treemgmtinterfaces")
        # Get selected pif
        selection = treemgmtinterfaces.get_selection()
        pif_ref = listmgmtinterfaces.get_value(selection.get_selected()[1],0)
        combomgmtnetworks = self.builder.get_object("combomgmtnetworks")
        listmgmtnetworks = self.builder.get_object("listmgmtnetworks")
        # Get selected pif info
        pif = self.xc_servers[self.selected_host].all_pif[pif_ref]
        iter = combomgmtnetworks.get_active_iter()
        # Get selected network_ref
        pif = self.xc_servers[self.selected_host].all_pif[pif_ref]
        network_ref = listmgmtnetworks.get_value(iter, 0)
        if pif['network'] != network_ref:
            change = True
        radiomgmtipmanual = self.builder.get_object("radiomgmtipmanual")
        radiomgmtipdhcp = self.builder.get_object("radiomgmtipdhcp")
        radiomgmtdnsmanual = self.builder.get_object("radiomgmtdnsmanual")
        radiomgmtdnsdhcp = self.builder.get_object("radiomgmtdnsdhcp")
        ip = self.builder.get_object("txtmgmtip").get_text()
        mask  = self.builder.get_object("txtmgmtmask").get_text()
        gw = self.builder.get_object("txtmgmtgw").get_text()
        dns1 = self.builder.get_object("txtmgmtdns1").get_text()
        dns2 = self.builder.get_object("txtmgmtdns2").get_text()
        change = False
        if pif['ip_configuration_mode'] == "DHCP" and radiomgmtipmanual.get_active():
            change = True
        if pif['ip_configuration_mode'] != "DHCP" and radiomgmtipdhcp.get_active():
            change = True
        if ip != pif['IP'] or mask != pif['netmask'] or gw != pif['gateway']:
            change = True
        if pif['DNS'] == "" and radiomgmtdnsmanual.get_active():
            change = True
        if pif['DNS'] != "" and radiomgmtdnsdhcp.get_active():  
            change = True
        if dns1 + "," + dns2 != pif['DNS']:
            change = True
        # If some parameter was changed, show confirmation dialog, if not hide magement interface window
        if change:
            self.builder.get_object("dialogreconfigure").show()
        else:
            self.builder.get_object("mgmtinterface").hide()
    

