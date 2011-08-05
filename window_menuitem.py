
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
import gtk
from oxcSERVER import *
import xtea
from thread import *
import pdb
class oxcWindowMenuItem:
    """
    Class used to manage functions called from menuitems
    """
    # HOST/SERVER
    def on_m_repair_storage_activate(self, widget, data=None):
        """
        Function called on "Repair storage"
        """
        self.builder.get_object("cancelrepairstorage").set_label("Cancel")
        self.builder.get_object("lblrepairerror").hide()
        self.builder.get_object("repairstorage").show()
        listrepairstorage = self.builder.get_object("listrepairstorage")
        self.xc_servers[self.selected_host].fill_listrepairstorage(listrepairstorage, self.selected_ref)
    def on_cancelrepairstorage_clicked(self, widget, data=None):
        """
        Function called when you press cancel on "repair storage" window
        """
        self.builder.get_object("repairstorage").hide()
    def on_acceptrepairstorage_clicked(self, widget, data=None):
        """
        Function called when you press Repair on "repair storage" window
        """
        self.builder.get_object("lblrepairerror").show()
        self.builder.get_object("lblrepairerror").set_markup(\
                "<span foreground='green'><b>Repairing... wait please.</b></span>")
        listrepairstorage = self.builder.get_object("listrepairstorage")
        Thread(target=self.xc_servers[self.selected_host].repair_storage,
                args=(listrepairstorage, self.selected_ref)).start()
        self.builder.get_object("acceptrepairstorage").set_sensitive(False)

    def on_m_remove_activate(self, widget, data=None):
        """
        Called from "remove" menuitem of server
        """
        # Remove server from configuration
        del self.config_hosts[self.selected_name]
        self.config['servers']['hosts'] = self.config_hosts
        self.config.write()
        # Remove from left treeview (treestore)
        self.treestore.remove(self.selected_iter)
    def on_m_forget_activate(self, widget, data=None):
        """
        Forget password: dont remember password for server
        """
        # Only put to "" the server password on oxc.conf
        if self.selected_name in self.config_hosts:
            self.config_hosts[self.selected_name][1]  = ""
        elif self.selected_ip in self.config_hosts:
            self.config_hosts[self.selected_ip][1]  = ""
        elif self.selected_host in self.config_hosts:
            self.config_hosts[self.selected_host][1]  = ""
    def on_m_addserver_activate(self, widget, data=None):
        """
        Add server: show the window for add a new server
        """
        self.builder.get_object("addserver").show()
    # VM
     # Make Into Template
    def on_m_make_into_template_activate(self, widget, data=None):
        """
        Called from "make into template" menuitem of VM
        Call to method "make_into_template" of oxcSERVER with selected ref param (vm ref)
        """
        self.xc_servers[self.selected_host].make_into_template(self.selected_ref)
     # Copy VM
    def on_m_snapshot_activate(self, widget, data=None):
        """
        Called from "snapshot" menuitem of VM
        Show snapshot dialog and set the name to empty
        """
        self.builder.get_object("snapshotname").set_text("")
        self.builder.get_object("dialogsnapshotname").show()

    def on_m_copy_activate(self, widget, data=None):
        """
        Called from "copy" menuitem of VM
        """
        listcopystg = self.builder.get_object("listcopystg")
        treecopystg = self.builder.get_object("treecopystg")
        # Set name and description on copy window
        self.builder.get_object("txtcopyvmname").set_text("Copy of " + self.selected_name)
        self.builder.get_object("txtcopyvmdesc").set_text(
                 self.xc_servers[self.selected_host].all_vms[self.selected_ref]['name_description']
                )
        """
        Fill the treeview called "treecopystg" with model "listcopystg" with possible storage
        This treeview is only used on "full copy"
        fill_listcopystg return the number position of default storage
        """
        defsr = self.xc_servers[self.selected_host].fill_listcopystg(listcopystg, self.selected_host)
        # Select the default storage
        treecopystg.set_cursor((defsr,), treecopystg.get_column(0))
        treecopystg.get_selection().select_path((defsr, 0))
        # Show the window copy window
        self.builder.get_object("windowcopyvm").show()
    def on_cancelforcejoinpool_clicked(self, widget, data=None):
        """
        Cancel "force join to pool" dialog
        """
        self.builder.get_object("forcejoinpool").hide()
    def on_acceptforcejoinpool_clicked(self, widget, data=None):
        """
        Accept "force join to pool" dialog
        """
        last_pool_data = self.xc_servers[self.last_host_pool].last_pool_data
        self.xc_servers[self.last_host_pool].add_server_to_pool_force(self.selected_ref, last_pool_data)
        self.builder.get_object("forcejoinpool").hide()

    def on_m_pool_add_server_activate(self, widget, data=None):
        """
        Called from "Add Server" right menu (pool)
        """
        for i in range(2,len(self.builder.get_object("menu_m_add_server").get_children())):
            self.builder.get_object("menu_m_add_server").remove(self.builder.get_object("menu_m_add_server").get_children()[2])
        for server in self.xc_servers:
            if self.xc_servers[server].is_connected == True:
                pool_ref = self.xc_servers[server].all_pools.keys()[0]
                if self.xc_servers[server].all_pools[pool_ref]["name_label"] == "":
                    image = gtk.Image()
                    image.set_from_file("images/tree_running_16.png")
                    item = gtk.ImageMenuItem(gtk.STOCK_HELP,None)
                    item.use_underline = False
                    item.set_image(image)
                    # Host ref
                    ref =  self.xc_servers[server].all_hosts.keys()[0]
                    self.builder.get_object("menu_m_add_server").append(item)
                    item.connect("activate", self.xc_servers[server].add_server_to_pool, ref, server, ref, self.selected_ip)
                    item.get_children()[0].set_label(self.xc_servers[server].all_hosts[ref]["name_label"])
                    item.show()

    def on_m_add_to_pool_activate(self, widget, data=None):
        """
        Called from "Add To pool" menuitem (server)
        """
        for i in range(2,len(self.builder.get_object("menu_add_to_pool").get_children())):
            self.builder.get_object("menu_add_to_pool").remove(self.builder.get_object("menu_add_to_pool").get_children()[2])
        for server in self.xc_servers:
            if self.xc_servers[server].is_connected == True:
                pool_ref = self.xc_servers[server].all_pools.keys()[0]
                if self.xc_servers[server].all_pools[pool_ref]["name_label"] != "":
                    image = gtk.Image()
                    image.set_from_file("images/poolconnected_16.png")
                    item = gtk.ImageMenuItem(gtk.STOCK_HELP,None)
                    item.use_underline = False
                    item.set_image(image)
                    # Host ref
                    pool = self.xc_servers[server].all_pools[pool_ref]["name_label"]
                    self.builder.get_object("menu_add_to_pool").append(item)
                    item.connect("activate", self.xc_servers[self.selected_ip].add_server_to_pool, pool_ref, self.selected_ip, self.selected_ref, server)
                    item.get_children()[0].set_label(pool)
                    item.show()
    def on_menuitem_pool_add_server_activate(self, widget, data=None):
        """
        Called from "Add Server" menuitem (pool)
        """
        for i in range(2,len(self.builder.get_object("menu_add_server").get_children())):
            self.builder.get_object("menu_add_server").remove(self.builder.get_object("menu_add_server").get_children()[2])
        for server in self.xc_servers:
            if self.xc_servers[server].is_connected == True:
                pool_ref = self.xc_servers[server].all_pools.keys()[0]
                if self.xc_servers[server].all_pools[pool_ref]["name_label"] == "":
                    image = gtk.Image()
                    image.set_from_file("images/tree_running_16.png")
                    item = gtk.ImageMenuItem(gtk.STOCK_HELP,None)
                    item.use_underline = False
                    item.set_image(image)
                    # Host ref
                    ref =  self.xc_servers[server].all_hosts.keys()[0]
                    self.builder.get_object("menu_add_server").append(item)
                    item.connect("activate", self.xc_servers[server].add_server_to_pool, ref, server, ref, self.selected_ip)
                    item.get_children()[0].set_label(self.xc_servers[server].all_hosts[ref]["name_label"])
                    item.show()
    def on_menuitem_server_add_to_pool_activate(self, widget, data=None):
        """
        Called from "Add to pool" menuitem (server)
        """
        for i in range(2,len(self.builder.get_object("menu_server_add_to_pool").get_children())):
            self.builder.get_object("menu_server_add_to_pool").remove(self.builder.get_object("menu_server_add_to_pool").get_children()[2])
        for server in self.xc_servers:
            if self.xc_servers[server].is_connected == True:
                pool_ref = self.xc_servers[server].all_pools.keys()[0]
                if self.xc_servers[server].all_pools[pool_ref]["name_label"] != "":
                    image = gtk.Image()
                    image.set_from_file("images/poolconnected_16.png")
                    item = gtk.ImageMenuItem(gtk.STOCK_HELP,None)
                    item.use_underline = False
                    item.set_image(image)
                    # Host ref
                    pool = self.xc_servers[server].all_pools[pool_ref]["name_label"]
                    self.builder.get_object("menu_server_add_to_pool").append(item)
                    item.connect("activate", self.xc_servers[self.selected_ip].add_server_to_pool, pool_ref, self.selected_ip, self.selected_ref, server)
                    item.get_children()[0].set_label(pool)
                    item.show()
    def on_m_resume_on_activate(self, widget, data=None):
        """
        Called from "Resumen on" menuitem of VM
        """
        # Remove the previous possible servers of submenu (right menu)
        for i in range(2,len(self.builder.get_object("menu_resume_on").get_children())):
            self.builder.get_object("menu_resume_on").remove(self.builder.get_object("menu_resume_on").get_children()[2])
        # Go all servers and add to submenu (right menu)
        for h in  self.xc_servers[self.selected_host].all_hosts:
            image = gtk.Image()
            image.set_from_file("images/xen.gif")
            item = gtk.ImageMenuItem(gtk.STOCK_HELP,None)
            item.use_underline = False
            item.set_image(image)
            """
            Set the signal, when is clicked call to function "start_resumen_on" with params:
            - Selected vm ref
            - Host ref
            """
            item.connect("activate", self.xc_servers[self.selected_host].resume_vm_on, self.selected_ref, h)
            self.builder.get_object("menu_resume_on").append(item)
            host_name = self.xc_servers[self.selected_host].all_hosts[h]['name_label']
            """
            Can start function could return:
            - Empty string means vm can start in that server
            - Not empty string means means vm cannot start in that server (not memory or other error)
            """
            can_start = self.xc_servers[self.selected_host].can_start(self.selected_ref, h)
            if can_start:
                item.get_children()[0].set_label(host_name + " : " + can_start)
            else:
                item.get_children()[0].set_label(host_name)
            item.show()
            # If server cannot be used to resume on it, disable server
            if can_start != "":
               item.set_sensitive(False)
    def on_m_start_on_activate(self, widget, data=None):
        """
        Called from "Start on" menuitem of VM
        """
        # Remove the previous possible servers of submenu (right menu)
        for i in range(2,len(self.builder.get_object("menu_start_on").get_children())):
            self.builder.get_object("menu_start_on").remove(self.builder.get_object("menu_start_on").get_children()[2])
        # Go all servers and add to submenu (right menu)
        for h in  self.xc_servers[self.selected_host].all_hosts:
            image = gtk.Image()
            image.set_from_file("images/xen.gif")
            item = gtk.ImageMenuItem(gtk.STOCK_HELP,None)
            item.use_underline = False
            item.set_image(image)
            """
            Set the signal, when is clicked call to function "start_resumen_on" with params:
            - Selected vm ref
            - Host ref
            """
            item.connect("activate", self.xc_servers[self.selected_host].start_vm_on, self.selected_ref, h)
            self.builder.get_object("menu_start_on").append(item)
            host_name = self.xc_servers[self.selected_host].all_hosts[h]['name_label']
            """
            Can start function could return:
            - Empty string means vm can start in that server
            - Not empty string means means vm cannot start in that server (not memory or other error)
            """
            can_start = self.xc_servers[self.selected_host].can_start(self.selected_ref, h)
            if can_start:
                item.get_children()[0].set_label(host_name + " : " + can_start)
            else:
                item.get_children()[0].set_label(host_name)
            item.show()
            # If server cannot be used to resume on it, disable server
            if can_start != "":
               item.set_sensitive(False)

    def on_m_pool_migrate_activate(self, widget, data=None):
        """
        Called from "Start on" menuitem of VM
        """
        # Remove the previous possible servers of submenu (right menu)
        for i in range(2,len(self.builder.get_object("menu_pool_migrate").get_children())):
            self.builder.get_object("menu_pool_migrate").remove(self.builder.get_object("menu_pool_migrate").get_children()[2])
        # Go all servers and add to submenu (right menu)
        for h in  self.xc_servers[self.selected_host].all_hosts:
            image = gtk.Image()
            image.set_from_file("images/xen.gif")
            item = gtk.ImageMenuItem(gtk.STOCK_HELP,None)
            item.use_underline = False
            item.set_image(image)
            """
            Set the signal, when is clicked call to function "start_resumen_on" with params:
            - Selected vm ref
            - Host ref
            """
            item.connect("activate", self.xc_servers[self.selected_host].migrate_vm, self.selected_ref, h)
            self.builder.get_object("menu_pool_migrate").append(item)
            host_name = self.xc_servers[self.selected_host].all_hosts[h]['name_label']
            resident_on = self.xc_servers[self.selected_host].all_vms[self.selected_ref]['resident_on']
            """
            Can start function could return:
            - Empty string means vm can start in that server
            - Not empty string means means vm cannot start in that server (not memory or other error)
            """
            can_start = self.xc_servers[self.selected_host].can_start(self.selected_ref, h)
            if can_start:
                item.get_children()[0].set_label(host_name + " : " + can_start)
            else:
                item.get_children()[0].set_label(host_name)
            item.show()
            # If server cannot be used to resume on it, disable server
            if can_start != "" or h == resident_on:
               item.set_sensitive(False)


    #TOOLBAR 
    def on_tb_start_clicked(self, widget, data=None):
        """
        "Start" button on toolbar is pressed
        Power on a VM
        """
        self.xc_servers[self.selected_host].start_vm(self.selected_ref)
    def on_tb_clean_shutdown_clicked(self, widget, data=None):
        """
        "Clean shutdown" on toolbar is pressed
        Clean shutdown a vm
        """
        self.xc_servers[self.selected_host].clean_shutdown_vm(self.selected_ref)

    def on_tb_hard_shutdown_clicked(self, widget, data=None):
        """
        "Hard shutdown" on toolbar is pressed
        Hard shutdown a vm
        """
        self.xc_servers[self.selected_host].hard_shutdown_vm(self.selected_ref)

    def on_tb_clean_reboot_clicked(self, widget, data=None):
        """
        "Clean reboot" on toolbar is pressed
        Clean reboot a vm
        """
        self.xc_servers[self.selected_host].clean_reboot_vm(self.selected_ref)

    def on_tb_hard_reboot_clicked(self, widget, data=None):
        """
        "Hard reboot" on toolbar is pressed
        hard reboot a vm
        """
        self.xc_servers[self.selected_host].hard_reboot_vm(self.selected_ref)


    def on_tb_suspend_clicked(self, widget, data=None):
        """
        "Suspend" on toolbar is pressed
        Suspend a vm
        """
        self.xc_servers[self.selected_host].suspend_vm(self.selected_ref)

    def on_tb_unpause_clicked(self, widget, data=None):
        """
        "Resumen" on toolbar is pressed
        Resume a suspended vm
        """
        self.xc_servers[self.selected_host].unpause_vm(self.selected_ref)

    def on_tbalerts_clicked(self, widget, data=None):
        """
        Open the alert window
        """
        self.builder.get_object("windowalerts").show()

    def update_toolbar(self):
        """
        This function is called when a VM, host, storage or template is selected
        Toolbar buttons are called:
        tb_action, e.g: tb_start
        check if "start" (removing tb_) exists on possible actions of this VM/host/...
        """
        toolbar = self.builder.get_object("toolbar")
        # for each children of toolbar
        for child in toolbar.get_children():
            if gtk.Buildable.get_name(child)[0:3] == "tb_":
                # self.selected_actions contains possible actions
                # if not exists: disable button
                # else: enable button
                if not self.selected_actions or \
                   self.selected_actions.count(gtk.Buildable.get_name(child)[3:]) \
                   == 0:
                    child.set_sensitive(False)
                else:
                    child.set_sensitive(True)
                    if gtk.Buildable.get_name(child)[3:] == "hard_shutdown":
                        if not self.selected_actions.count("clean_shutdown"):
                            self.builder.get_object("tb_clean_shutdown").hide()
                            self.builder.get_object("tb_hard_shutdown").show()
                    if gtk.Buildable.get_name(child)[3:] == "hard_reboot":
                        if not self.selected_actions.count("clean_reboot"):
                            self.builder.get_object("tb_clean_reboot").hide()
                            self.builder.get_object("tb_hard_reboot").show()
                    if gtk.Buildable.get_name(child)[3:] == "clean_shutdown":
                        self.builder.get_object("tb_clean_shutdown").show()
                        self.builder.get_object("tb_clean_reboot").show()
                        self.builder.get_object("tb_hard_reboot").hide()
                        self.builder.get_object("tb_hard_shutdown").hide()

    # MENUBAR Actions
    def on_m_start_activate(self, widget, data=None):
        """
        "Start" menuitem pressed on right click menu
        """
        self.xc_servers[self.selected_host].start_vm(self.selected_ref)
    def on_m_clean_shutdown_activate(self, widget, data=None):
        """
        "Clean shutdown" menuitem pressed on right click menu
        """
        if self.selected_type == "vm":
            self.xc_servers[self.selected_host].clean_shutdown_vm(self.selected_ref)
        elif self.selected_type == "server" or self.selected_type == "host":
            self.on_menuitem_server_shutdown_activate(widget, data)
    def on_m_clean_reboot_activate(self, widget, data=None):
        """
        "Clean reboot" menuitem pressed on right click menu
        """
        if self.selected_type == "vm":
            self.xc_servers[self.selected_host].clean_reboot_vm(self.selected_ref)
        elif self.selected_type == "server" or self.selected_type == "host":
            self.on_menuitem_server_reboot_activate(widget, data)

    def on_m_suspend_activate(self, widget, data=None):
        """
        "Suspend" menuitem pressed on right click menu
        """
        self.xc_servers[self.selected_host].suspend_vm(self.selected_ref)
    def on_m_unpause_activate(self, widget, data=None):
        """
        "Unpause" menuitem pressed on right click menu
        """
        self.xc_servers[self.selected_host].unpause_vm(self.selected_ref)
    def on_m_hard_reboot_activate(self, widget, data=None):
        """
        "Hard reboot" menuitem pressed on right click menu
        """
        self.xc_servers[self.selected_host].hard_reboot_vm(self.selected_ref)
    def on_m_hard_shutdown_activate(self, widget, data=None):
        """
        "Hard shutdown" menuitem pressed on right click menu
        """
        self.xc_servers[self.selected_host].hard_shutdown_vm(self.selected_ref)
    def on_m_pause_activate(self, widget, data=None):
        """
        "Pause" menuitem pressed on right click menu
        """
        self.xc_servers[self.selected_host].pause_vm(self.selected_ref)
    def on_m_unsuspend_activate(self, widget, data=None):
        """
        "Resume" (unsuspend) menuitem pressed on right click menu
        """
        self.xc_servers[self.selected_host].unsuspend_vm(self.selected_ref)
    def on_m_resume_activate(self, widget, data=None):
        """
        "Resume" menuitem pressed on right click menu
        """
        self.xc_servers[self.selected_host].resume_vm(self.selected_ref)

    def on_menuitem_tools_updatemanager_activate(self, widget, data=None):
        """
        "Update Manager" menuitem pressed on right click menu
        """
        listupdates = self.builder.get_object("listupdates")
        treeupdates = self.builder.get_object("treeupdates")
        self.xc_servers[self.selected_host].fill_list_updates(self.selected_ref, listupdates)
        if listupdates.__len__():
             treeupdates.set_cursor((0, ), treeupdates.get_column(0))
             treeupdates.get_selection().select_path((0, ))

        self.builder.get_object("updatemanager").show()

    def on_installxenservertools_activate(self, widget, data=None):
        """
        "Install XenServer Tools" menuitem pressed on right click menu
        """
        self.xc_servers[self.selected_host].install_xenserver_tools(self.selected_ref)
    def on_m_forget_activate(self, widget, data=None):
        """
        "Forget Storage" menuitem pressed on right click menu
        """
        target=self.xc_servers[self.selected_host].forget_storage(self.selected_ref)

    def on_m_unplug_activate(self, widget, data=None):
        """
        "Detach Storage" menuitem pressed on right click menu
        """
        # Show confirmation dialog
        self.builder.get_object("detachstorage").show()
    def on_acceptdetachstorage_clicked(self, wwidget, data=None):
        """
        Function called when you accept confirmation "detach storage" dialog
        """
        #target=self.xc_servers[self.selected_host].detach_storage(self.selected_ref)
        Thread(target=self.xc_servers[self.selected_host].detach_storage, args=(self.selected_ref,)).start()
        self.builder.get_object("detachstorage").hide()
    def on_canceldetachstorage_clicked(self, widget, data=None):
        """
        Function called when you cancel confirmation "detach storage" dialog
        """
        self.builder.get_object("detachstorage").hide()
    def on_m_reattach_activate(self, widget, data=None): 
        """
        "Reattach Storage" menuitem pressed on right click menu
        """
        stgtype = self.xc_servers[self.selected_host].all_storage[self.selected_ref]['type']
        # If selected type is iso, you only can select "NFS ISO" or "CIFS ISO"
        if stgtype == "iso":
            disable = ["radionewstgnfsvhd", "radionewstgiscsi", "radionewstghwhba",
                       "radionewstgnetapp", "radionewstgdell"]
            for widget in disable:
                self.builder.get_object(widget).set_sensitive(False)
            enable = ["radionewstgcifs", "radionewstgnfsiso"]
            for widget in enable:
                self.builder.get_object(widget).set_sensitive(True)
        elif stgtype == "lvmoiscsi":
            self.builder.get_object("radionewstgiscsi").set_active(True)
            self.builder.get_object("txtiscsiname").set_text(self.selected_name)
            self.on_nextnewstorage_clicked(self.builder.get_object("nextnewstorage"), data)
            self.builder.get_object("previousnewstorage").set_sensitive(False)
        elif stgtype == "nfs":
            self.builder.get_object("radionewstgnfsvhd").set_active(True)
            self.builder.get_object("txtnewstgnfsname").set_text(self.selected_name)
            self.on_nextnewstorage_clicked(widget, data)
            self.builder.get_object("previousnewstorage").set_sensitive(False)
        else:
            print stgtype
        self.builder.get_object("radionewstgcifs").set_active(True)
        # Flag variable to know if we will do a reattach
        self.reattach_storage = True
        self.builder.get_object("newstorage").show()

    def on_m_importvm_activate(self, widget, data=None):
        """
        "Import VM" menuitem pressed on right click menu
        """
        blue = gtk.gdk.color_parse("#d5e5f7")
        # Disable "next button", it will be enabled when file is selected
        self.builder.get_object("nextvmimport").set_sensitive(False)
        self.builder.get_object("eventimport0").modify_bg(gtk.STATE_NORMAL, blue)
        # Set a filter, you only can selected *.xva files
        self.builder.get_object("filefilterimportvm").add_pattern("*.xva")
        # Show the import window
        self.builder.get_object("vmimport").show()
        # listimportservers contains the connected servers
        listimportservers = self.builder.get_object("listimportservers")
        listimportservers.clear()
        # For each host in config..
        for host in self.config_hosts:
            # If we are connected to this server
            if host in self.xc_servers:
                # Then add to list
                listimportservers.append([gtk.gdk.pixbuf_new_from_file("images/tree_connected_16.png"),
                    self.xc_servers[host].hostname,True,host]);
            """
            else:
                listimportservers.append([gtk.gdk.pixbuf_new_from_file("images/tree_disconnected_16.png"),
                    host,False]);
            """
        # If we are connected to some server..
        if listimportservers.__len__():
            treeimportservers = self.builder.get_object("treeimportservers")
            # Then selected the first
            treeimportservers.set_cursor((0, ), treeimportservers.get_column(0))
            treeimportservers.get_selection().select_path((0, ))

    def on_m_export_activate(self, widget, data=None):
        """
        "Export VM" menuitem pressed on right click menu
        """
        # Set default name
        self.filesave.set_current_name(self.selected_name + ".xva")
        # Show the choose dialog
        self.filesave.show()

    def on_m_snap_newvm_activate(self, widget, data=None):
        """
        "New VM From snapshot" menuitem pressed on "snapshot" menu (Snapshots tab of VM)
        """
        # Show the "new vm" window
        # TODO -> select vm with name_label
        self.on_m_newvm_activate(widget, data)

    def on_m_snap_createtpl_activate(self, widget, data=None):
        """
        "Create template from snapshot" menuitem pressed on "snapshot" menu (Snapshots tab of VM)
        """
        # set a default name
        self.builder.get_object("snaptplname").set_text("Template from snapshot '" + \
            self.xc_servers[self.selected_host].all_vms[self.selected_snap_ref]['name_label'] + "'")
        # Shows a dialog to enter a name for new template
        self.builder.get_object("dialogsnaptplname").show()

    def on_m_snap_delete_activate(self, widget, data=None):
        """
        "Delete snapshot" menuitem pressed on "snapshot" menu (Snapshots tab of VM)
        """
        # Show a dialog asking confirmation
        self.builder.get_object("dialogsnapshotdelete").show()

    def on_m_destroy_activate(self, widget, data=None):
        """
        "Destroy" menuitem pressed on right click menu (VM)
        """
        # Show a dialog asking confirmation
        if self.selected_type == "vm":
            self.builder.get_object("dialogdeletevm").show()
            self.builder.get_object("dialogdeletevm").set_markup("Are you sure you want to delete VM '" + self.selected_name + "' ?")
        elif self.selected_type == "template" or self.selected_type == "custom_template":
            self.builder.get_object("dialogdeletevm").show()
            self.builder.get_object("dialogdeletevm").set_markup("Are you sure you want to delete template '" + self.selected_name + "' ?")
        elif self.selected_type == "storage":
            print "delete storage"
        #self.treestore.remove(self.selected_iter)
        #self.xc_servers[self.selected_host].destroy_vm(self.selected_ref)

    def on_m_connect_activate(self, widget, data=None):
        """
        "Connect" menuitem pressed on right click menu (Host)
        """
        # Checks if exists a "master password"
        # Master password if need to save reverse passwords with XTEA
        # XTEA is a block cipher to save server password on oxc.conf
        # If master password if used (saved on oxc.conf as md5) use it to xtea decrypt
        if not self.selected_name in self.config_hosts:
            return
        if len(self.config_hosts[self.selected_name]) > 2:
            self.builder.get_object("checksslconnection").set_active(str(self.config_hosts[self.selected_name][2]) == "True")

        if self.password and self.config_hosts[self.selected_name][1]:
            # Decrypt password to plain
            # Use typed master password (previously checked with md5)
            # Fill characters left with "X" to reach a 16 characters
            decrypt_pw = xtea.crypt("X" * (16-len(self.password)) + self.password, \
                     self.config_hosts[self.selected_name][1].decode("hex"), self.iv)
            # Call to add server with name, ip and decrypted password
            # Add server try to connect to the server
            self.add_server(self.selected_name, self.config_hosts[self.selected_name][0], \
                decrypt_pw)
        else:
            # If master password is not set or server hasn't a saved password
            # Empty entries
            self.builder.get_object("addserverhostname").get_child().set_text(self.selected_name)
            self.builder.get_object("addserverusername").set_text(self.config_hosts[self.selected_name][0])
            self.builder.get_object("addserverpassword").set_text("")
            # Show the add server window
            addserver = self.builder.get_object("addserver").show_all()
            self.builder.get_object("addserverpassword").grab_focus()
    def on_m_disconnect_activate(self, widget, data=None):
        """
        "Disconnect" menuitem pressed on right click menu (Host)
        """
        # Checks if exists a "master password"
        # get the ip/host (not virtual name)
        host = self.xc_servers[self.selected_host].host
        # Logout implies:
        # - Unregister events to current session
        # - Disconnect of server
        self.xc_servers[self.selected_host].logout()
        # Remove from list (and children)
        if len(self.treestore.get_path(self.selected_iter)) == 2:
            self.treestore.remove(self.selected_iter)
        else:
            path = (self.treestore.get_path(self.selected_iter)[0], self.treestore.get_path(self.selected_iter)[1])
            iter = self.treestore.get_iter(path)
            self.treestore.remove(iter)
        # Add again the ip/host name
        self.treestore.append(self.treeroot, ([gtk.gdk.pixbuf_new_from_file("images/tree_disconnected_16.png"), host, None, "server", "Disconnected", None, None, ["connect", "forgetpw", "remove"], None]))
        # If copy window is showed.. hide 
        self.builder.get_object("windowcopyvm").hide()
        self.treeview.set_cursor((0, ), self.treeview.get_column(0))
        self.treeview.get_selection().select_path((0, ))
        # Update tabs
        self.selected_type = "home"
        self.update_tabs()
        # Delete alerts
        self.builder.get_object("listalerts").clear()
        for host in self.xc_servers:
            if self.xc_servers[host].is_connected:
                self.xc_servers[host].fill_alerts(self.listalerts)
        self.update_n_alerts()
    def on_m_newvm_activate(self, widget, data=None):
        """
        "New VM" menuitem pressed on right click menu (Host)
        """
        # self.newvmdata is used to set "new vm" parameters
        self.newvmdata = {}
        listtemplates = self.builder.get_object("listtemplates")
        # Fill the "list of templates" to create a new VM
        self.xc_servers[self.selected_host].fill_list_templates(listtemplates)
        # Set to first page and setting "page_comple" next button is enabled
        self.builder.get_object("tabboxnewvm").set_current_page(0)
        # Select the first template by default
        treetemplates = self.builder.get_object("treetemplates")
        treetemplates.set_cursor((0, 1), treetemplates.get_column(1))
        treetemplates.get_selection().select_path((0, 1))
        # For some templates is needed use DVD Drive or ISO Images
        # Fill the possible iso images to use
        self.xc_servers[self.selected_host].fill_list_isoimages(self.listisoimage)
        self.builder.get_object("radiobutton3_data").set_active(1)
        # Fill the connected DVDS
        self.xc_servers[self.selected_host].fill_list_phydvd(self.listphydvd)

        # Default interfaces for the new vm, and set the first parameter: the number of the interfaces
        self.xc_servers[self.selected_host].fill_list_networks(
                                        self.listnetworks, self.listnetworkcolumn)

        listnewvmhosts = self.builder.get_object("listnewvmhosts")
        treenewvmhosts = self.builder.get_object("treenewvmhosts")
        # A new vm could be started on some host (e.g a pool with servers)
        # Fill the possible hosts where vm could be start
        path = self.xc_servers[self.selected_host].fill_listnewvmhosts(listnewvmhosts)
        # Set the default server
        treenewvmhosts.set_cursor((path,1), treenewvmhosts.get_column(0))
        treenewvmhosts.get_selection().select_path((path,1))

        # Setting a default options
        self.newvmdata['location'] = "radiobutton1"
        self.newvmdata['vdi'] = ""

        self.builder.get_object("lblnewvm0").set_markup('  <span background="blue" foreground="white"><b>%-35s</b></span>' % "Template")
        labels = ["Name", "Location", "Home Server", "CPU / Memory", "Virtual disks", "Virtual Interfaces", "Finish"]
        for i in range(1, 8):
            self.builder.get_object("lblnewvm" + str(i)).set_markup( "  <b>%-35s</b>" % labels[i-1])

        # Show the "new vm" assistent
        self.newvm.show()

     
    # MENUBAR checks
    def on_checksavepassword_toggled(self, widget, data=None):
        self.builder.get_object("label259").set_sensitive(widget.get_active())
        self.builder.get_object("txtmasterpassword").set_sensitive(widget.get_active())
    def on_checkshowxtpls_toggled(self, widget, data=None):
        """
        Enable or disable show templates on left tree
        """
        # Save enable or disable to configuration
        self.config["gui"]["show_xs_templates"] = widget.get_active()
        self.config.write()
        # Call to "refilter" to hide/show the templates
        self.modelfilter.refilter()

    def on_checkshowhiddenvms_toggled(self, widget, data=None):
        """
        Enable or disable show templates on left tree
        """
        # Save enable or disable to configuration
        self.config["gui"]["show_hidden_vms"] = widget.get_active()
        self.config.write()
        # Call to "refilter" to hide/show the templates
        self.modelfilter.refilter()

    def on_checkshowtoolbar_toggled(self, widget, data=None):
        """
        Enable or disable show top toolbar
        """
        self.config["gui"]["show_toolbar"] = widget.get_active()
        # If is active, show the toolbar, else hide the toolbar
        if widget.get_active():
            self.builder.get_object("toolbar").show()
        else:
            self.builder.get_object("toolbar").hide()
        # Save in configuration
        self.config.write()
    def on_checksetsyle_toggled(self, widget, data=None):
        """
        Enable or disable use oxc style or use GTK style
        """
        self.config["gui"]["set_style"] = widget.get_active()
        # This is a trick:
        # Only set the color when application is showed, not before
        if self.builder.get_object("lbltreesearch6").get_parent():
            self.set_style_colors()
        # Save in configuration
        self.config.write()
    def on_checkshowcustomtpls_toggled(self, widget, data=None, a=None):
        """
        Enable or disable show custom templates on left tree
        """
        self.config["gui"]["show_custom_templates"] = widget.get_active()
        # Save in configuration
        self.config.write()
        # Call to "refilter" to hide/show custom templates
        self.modelfilter.refilter()
    def on_checkshowlocalstorage_toggled(self, widget, data=None, a=None):
        """
        Enable or disable show local storage on left tree
        """
        self.config["gui"]["show_local_storage"] = widget.get_active()
        # Save in configuration
        self.config.write()
        # Call to "refilter" to hide/show custom templates
        self.modelfilter.refilter()
    # MENUBAR
    def on_menuitem_entermaintenancemode_activate(self, widget, data=None):
        """
        "Enter Maintenance Mode" on menuitem is pressed
        """
        listmaintenancemode = self.builder.get_object("listmaintenancemode")
        self.xc_servers[self.selected_host].fill_vms_which_prevent_evacuation(self.selected_ref, listmaintenancemode)
        self.builder.get_object("maintenancemode").show()
    def on_cancelmaintenancemode_clicked(self, widget, data=None):
        """
        Pressed "Cancel" button on maintenance window
        """
        self.builder.get_object("maintenancemode").hide()

    def on_acceptmaintenancemode_clicked(self, widget, data=None):
        """
        Pressed "Accept" button on maintenance window
        """
        self.xc_servers[self.selected_host].enter_maintancemode(self.selected_ref)
        self.builder.get_object("maintenancemode").hide()

    def on_menuitem_exitmaintenancemode_activate(self, widget, data=None):
        """
        "Exit Maintenance Mode" on menuitem is pressed
        """
        self.xc_servers[self.selected_host].exit_maintancemode(self.selected_ref)

    def on_menuitem_vm_startrecovery_activate(self, widget, data=None):
        """
        "Start" button on menuitem is pressed
        Power on a VM
        """
        self.xc_servers[self.selected_host].start_vm_recovery_mode(self.selected_ref)

    def on_menuitem_stg_new_activate(self, widget, data=None):
        """
        "New Storage Repository" menuitem pressed on menubar 
        """
        blue = gtk.gdk.color_parse("#d5e5f7")
        # Disable "next button", it will be enabled when file is selected
        enable= ["radionewstgnfsvhd", "radionewstgiscsi", "radionewstghwhba",
                   "radionewstgnetapp", "radionewstgdell", "radionewstgcifs", 
                   "radionewstgnfsiso"]
        for widget in enable:
            self.builder.get_object(widget).set_sensitive(True)
        self.reattach_storage = False
        self.builder.get_object("nextnewstorage").set_sensitive(True)
        self.builder.get_object("eventnewstg0").modify_bg(gtk.STATE_NORMAL, blue)
        self.builder.get_object("tabboxnewstorage").set_current_page(0)
        self.builder.get_object("newstorage").show() 
    def on_menuitem_dmesg_activate(self, widget, data=None):
        dmesg = self.xc_servers[self.selected_host].get_dmesg(self.selected_ref)
        self.builder.get_object("txthostdmesg").get_buffer().set_text(dmesg)
        self.builder.get_object("hostdmesg").show()
    def on_management_activate(self, widget, data=None):
        """
        "Management interfaces" on server menu is rpressed 
        """
        listmgmtinterfaces = self.builder.get_object("listmgmtinterfaces")
        treemgmtinterfaces = self.builder.get_object("treemgmtinterfaces")
        # Fill the list of interfaces with "Management" option enabled
        self.xc_servers[self.selected_host].fill_mamagement_ifs_list(listmgmtinterfaces)
        
        # Set the top label with server selected
        lblmgmtinterfaces = self.builder.get_object("lblmgmtinterfaces")
        lblmgmtinterfaces.set_text(lblmgmtinterfaces.get_text().replace("{0}", self.selected_name))

        # Show the window
        self.builder.get_object("mgmtinterface").show()

        # Select the first interface by default
        selection = treemgmtinterfaces.get_selection()
        treemgmtinterfaces.set_cursor((0, ), treemgmtinterfaces.get_column(0))
        treemgmtinterfaces.get_selection().select_path((0, ))

        # Get the reference of default interface
        pif_ref = listmgmtinterfaces.get_value(selection.get_selected()[1],0)
        combomgmtnetworks = self.builder.get_object("combomgmtnetworks")
        listmgmtnetworks = self.builder.get_object("listmgmtnetworks")

        # Get all information for this PIF
        pif = self.xc_servers[self.selected_host].all_pif[pif_ref]

        # Fill the network combo with possible networks
        # fill_management_networks return the position where network reference of pif is located
        current = self.xc_servers[self.selected_host].fill_management_networks(listmgmtnetworks, pif['network'])

        # Set in combo the network for default PIF
        combomgmtnetworks.set_active(current)
        # If interface configuration is dhcp disable ip/mask/gw entries
        if pif['ip_configuration_mode'] == "DHCP":
            self.builder.get_object("txtmgmtip").set_sensitive(False)
            self.builder.get_object("txtmgmtmask").set_sensitive(False)
            self.builder.get_object("txtmgmtgw").set_sensitive(False)
        # Although could be disabled, set the ip/netmask/gateway
        self.builder.get_object("txtmgmtip").set_text(pif['IP'])
        self.builder.get_object("txtmgmtmask").set_text(pif['netmask'])
        self.builder.get_object("txtmgmtgw").set_text(pif['gateway'])
        # If ip configuration is with dhcp set appropiate radio enabled
        self.builder.get_object("radiomgmtipdhcp").set_active(pif['ip_configuration_mode'] == "DHCP")
        self.builder.get_object("radiomgmtipmanual").set_active(pif['ip_configuration_mode'] != "DHCP")
        # If dns configuration is with dhcp set appropiate radio enabled
        self.builder.get_object("radiomgmtdnsdhcp").set_active(pif['DNS'] == "")
        self.builder.get_object("radiomgmtdnsmanual").set_active(pif['DNS'] != "")
        # If dns is manual..
        if pif['DNS']:
            # Fill the entries with dns ips
            dns = pif['DNS'].split(",")
            self.builder.get_object("txtmgmtdns1").set_text(dns[0])
            if len(dns) > 1:
                self.builder.get_object("txtmgmtdns2").set_text(dns[1])
            else:
                self.builder.get_object("txtmgmtdns2").set_text("")
        else:
            # If not, empty the entris and disable both entries
            self.builder.get_object("txtmgmtdns1").set_sensitive(False)
            self.builder.get_object("txtmgmtdns2").set_sensitive(False)
            self.builder.get_object("txtmgmtdns1").set_text("")
            self.builder.get_object("txtmgmtdns2").set_text("")

    def on_menuitem_stg_default_activate(self, widget, data=None):
        """
        "Set as Default Storage Repository" menu item is pressed (storage menu)
        """
        self.xc_servers[self.selected_host].set_default_storage(self.selected_ref)
    def on_menuitem_tools_statusreport_activate(self, widget, data=None):
        """
        "Status report" menu item is pressed (tools menu)
        """
        self.builder.get_object("statusreport").show()
        listreport = self.builder.get_object("listreport")
        self.xc_servers[self.selected_host].fill_list_report(self.selected_ref, listreport)
        self.update_report_total_size_time()

    def on_menuitem_tools_cad_activate(self, widget, data=None):
        """
        "Send Ctrl-Alt-Del" menu item is pressed (tools menu)
        """
        self.tunnel.send_data("\xfe\x01\x00\x00\x00\x00\x00\x1d")
        self.tunnel.send_data("\xfe\x01\x00\x00\x00\x00\x00\x38")
        self.tunnel.send_data("\xfe\x01\x00\x00\x00\x00\x00\xd3")
        self.tunnel.send_data("\xfe\x00\x00\x00\x00\x00\x00\x1d")
        self.tunnel.send_data("\xfe\x00\x00\x00\x00\x00\x00\x38")
        self.tunnel.send_data("\xfe\x00\x00\x00\x00\x00\x00\xd3")

    def on_menuitem_migratetool_activate(self, widget, data=None):
        """
        "Migrate tool" menu item is pressed (tools menu)
        """
        self.builder.get_object("spinmigratemem").set_value(256)
        self.builder.get_object("spinmigratevcpus").set_value(1)
        self.builder.get_object("checkmigrateoutputserver").set_sensitive(self.selected_type == "host")
        self.builder.get_object("migratetool").show()
    def on_menuitem_takescreenshot_activate(self, widget, data=None):
        """
        "Take screenshot" menu item is pressed (tools menu)
        """
        self.builder.get_object("savescreenshot").set_current_name("Screenshot_%s.jpg" \
                % self.selected_name.replace('/', '_'))
        self.builder.get_object("savescreenshot").show()

    def on_cancelsavescreenshot_clicked(self, widget, data=None):
        self.builder.get_object("savescreenshot").hide()

    def on_acceptsavescreenshot_clicked(self, widget, data=None):
        filename = self.builder.get_object("savescreenshot").get_filename()
        if self.selected_type == "vm":
            self.xc_servers[self.selected_host].save_screenshot(self.selected_ref, filename)
        else:
            #host
            ref = self.xc_servers[self.selected_host].host_vm[self.selected_ref][0]
            self.xc_servers[self.selected_host].save_screenshot(ref, filename)
        self.builder.get_object("savescreenshot").hide()

    def on_menuitem_options_activate(self, widget, data=None):
        """
        "Options" menu item is pressed (tools menu)
        """
        # Enable/disable the save password option
        self.builder.get_object("checksavepassword").set_active(eval(self.config["gui"]["save_password"]))
        # Show the options dialog
        self.builder.get_object("dialogoptions").show()
    def on_menuitem_delete_activate(self, widget, data=None):
        """
        "Delete" menu item is pressed (only for Pool)
        """
        # Delete the pool
        self.xc_servers[self.selected_host].delete_pool(self.selected_ref)
    def on_menuitem_connectall_activate(self, widget, data=None):
        """
        "Connect all" menu item is pressed (server menu)
        """
        # For each server: connect
        # TODO: fix
        self.treestore.foreach(self.foreach_connect, True)
    def on_menuitem_disconnectall_activate(self, widget, data=None):
        # For each server: disconnect
        """
        "Disconnect all" menu item is pressed (server menu)
        """
        # For each server: disconnect
        # TODO: fix
        self.treestore.foreach(self.foreach_connect, False)
    def on_collapsechildren_activate(self, widget, data=None):
        """
        "Collapse Children" menu item is pressed
        """
        for child in range(0,self.treestore.iter_n_children(self.selected_iter)):
             iter = self.treestore.iter_nth_child(self.selected_iter, child)
             if self.treestore.iter_n_children(iter):
                 path = self.treestore.get_path(iter)
                 self.treeview.collapse_row(path)
    def on_expandall_activate(self, widget, data=None):
        """
        "Expand all" menu item is pressed
        """
        for child in range(0,self.treestore.iter_n_children(self.selected_iter)):
             iter = self.treestore.iter_nth_child(self.selected_iter, child)
             if self.treestore.iter_n_children(iter):
                 path = self.treestore.get_path(iter)
                 self.treeview.expand_row(path, True)

    def on_menuitem_changepw_activate(self, widget, data=None):
        """
        "Change Server Password" menu item is pressed
        """
        self.builder.get_object("lblwrongpw").hide()
        self.builder.get_object("changepassword").show()
        self.builder.get_object("txtcurrentpw").set_text("")
        self.builder.get_object("txtnewpw").set_text("")
        self.builder.get_object("txtrenewpw").set_text("")
        self.builder.get_object("acceptchangepassword").set_sensitive(False)
        label = self.builder.get_object("lblchangepw").get_label()
        self.builder.get_object("lblchangepw").set_label(label.replace("{0}", self.selected_name))

    def on_menuitem_install_xslic_activate(self, widget, data=None):
        """
        "Install License Key" menu item is pressed
        """
        # Show file chooser
        if self.xc_servers[self.selected_host].all_hosts[self.selected_ref].get("license_server"):
            licenserver =  self.xc_servers[self.selected_host].all_hosts[self.selected_ref].get("license_server")
            self.builder.get_object("licensehost").set_text(licenserver["address"])
            self.builder.get_object("licenseport").set_text(licenserver["port"])
            self.builder.get_object("dialoglicensehost").show()


        else:
            self.builder.get_object("filterfilelicensekey").add_pattern("*.xslic")
            self.builder.get_object("filelicensekey").show()

    def on_cancellicensehost_clicked(self, widget, data=None):
        """
        Function called when you press cancel on license host dialog 
        """
        self.builder.get_object("dialoglicensehost").hide()

    def on_acceptlicensehost_clicked(self, widget, data=None):
        """
        Function called when you press cancel on license host dialog 
        """
        edition = "advanced"
        for licwidget in ["advanced", "enterprise", "platinum", "enterprise-xd"]:
            if self.builder.get_object(licwidget).get_active():
                edition = licwidget
                break

        licensehost = self.builder.get_object("licensehost").get_text()
        licenseport = self.builder.get_object("licenseport").get_text()
        self.xc_servers[self.selected_host].set_license_host(self.selected_ref, licensehost, licenseport, edition)
        self.builder.get_object("dialoglicensehost").hide()


    def on_cancelfilelicensekey_clicked(self, widget, data=None):
        """
        Function called when you press cancel on filchooser "install license key"
        """
        # Hide the file chooser
        self.builder.get_object("filelicensekey").hide()

    def on_openfilelicensekey_clicked(self, widget, data=None):
        """
        Function called when you press open on filchooser "install license key"
        """
        filename = self.builder.get_object("filelicensekey").get_filename()
        self.xc_servers[self.selected_host].install_license_key(self.selected_ref, filename)
        #print open( self.builder.get_object("filelicensekey").get_filename(), "rb").read().encode("base64").replace("\n","")
        # Hide the file chooser
        self.builder.get_object("filelicensekey").hide()

    def on_menuitem_restoreserver_activate(self, widget, data=None):
        """
        "Restoreserver" menu item is pressed
        """
        # Show select destination dialog

        self.builder.get_object("filefilterrestoreserver").add_pattern("*.xbk")
        self.builder.get_object("filerestoreserver").show()

    def on_menuitem_backupserver_activate(self, widget, data=None):
        """
        "Backup server" menu item is pressed
        """
        # Show select destination dialog
        filebackupserver = self.builder.get_object("filebackupserver")
        filebackupserver.set_current_name(self.selected_name + ".xbk")
        self.builder.get_object("filefilterbackupserver").add_pattern("*.xbk")
        self.builder.get_object("filebackupserver").show()

    def on_menuitem_downloadlogs_activate(self, widget, data=None):
        """
        "Download logs" (host) menu item is pressed
        """
        # Show select destination dialog
        filedownloadlogs = self.builder.get_object("filedownloadlogs")
        filedownloadlogs.set_current_name(self.selected_name + ".tar.gz")
        self.builder.get_object("filedownloadlogs").show()

    def on_cancelfilebackupserver_clicked(self, widget, data=None):
        """
        Function called when you cancel dialog for save backup server
        """
        self.builder.get_object("filebackupserver").hide()

    def on_savefilebackupserver_clicked(self, widget, data=None):
        """
        Function called when you accept dialog for save backup server
        """
        filebackupserver = self.builder.get_object("filebackupserver")
        filename = filebackupserver.get_filename()
        self.xc_servers[self.selected_host].thread_backup_server(self.selected_ref, filename, self.selected_name)
        self.builder.get_object("filebackupserver").hide()

    def on_cancelfiledownloadlogs_clicked(self, widget, data=None):
        """
        Function called when you cancel dialog for download logs
        """
        self.builder.get_object("filedownloadlogs").hide()

    def on_savefiledownloadlogs_clicked(self, widget, data=None):
        """
        Function called when you accept dialog for download logs
        """
        filedownloadlogs = self.builder.get_object("filedownloadlogs")
        filename = filedownloadlogs.get_filename()
        self.xc_servers[self.selected_host].thread_host_download_logs(self.selected_ref, filename, self.selected_name)
        self.builder.get_object("filedownloadlogs").hide()


    def on_cancelrestoreserver_clicked(self, widget, data=None):
        """
        Function called when you cancel dialog for open file to restore server
        """
        self.builder.get_object("filerestoreserver").hide()

    def on_openfilerestoreserver_clicked(self, widget, data=None):
        """
        Function called when you accept dialog for open file to restore server
        """
        filename = self.builder.get_object("filerestoreserver").get_filename()
        self.xc_servers[self.selected_host].thread_restore_server(self.selected_ref, filename, self.selected_name)
        self.builder.get_object("filerestoreserver").hide()

    def on_menuitem_server_reboot_activate(self, widget, data=None):
        """
        "Reboot server" menu item is pressed
        """
        self.builder.get_object("confirmreboot").show()
    def on_cancelconfirmreboot_clicked(self, widget, data=None):
        """
        Function called when you cancel dialog for reboot server
        """
        self.builder.get_object("confirmreboot").hide()

    def on_acceptconfirmreboot_clicked(self, widget, data=None):
        """
        Function called when you cancel dialog for reboot server
        """
        res = self.xc_servers[self.selected_host].reboot_server(self.selected_ref)
        #res = "OK"
        if res == "OK":
            self.on_m_disconnect_activate(widget, data)
        self.builder.get_object("confirmreboot").hide()

    def on_menuitem_server_shutdown_activate(self, widget, data=None):
        """
        "Reboot server" menu item is pressed
        """
        self.builder.get_object("confirmshutdown").show()

    def on_acceptconfirmshutdown_clicked(self, widget, data=None):
        """
        "Reboot server" menu item is pressed
        """
        res = self.xc_servers[self.selected_host].shutdown_server(self.selected_ref)
        if res == "OK":
            self.on_m_disconnect_activate(widget, data)
        self.builder.get_object("confirmshutdown").hide()

    def on_cancelconfirmshutdown_clicked(self, widget, data=None):
        """
        Function called when you cancel dialog for shutdown server
        """
        self.builder.get_object("confirmshutdown").hide()

    def on_menuitem_checkforupdates_activate(self, widget, data=None):
        """
        "Check for Updates" menu item is pressed (help)
        """
        pool = []
        hotfix = []
        # Get pool and patch info
        for server in  self.xc_servers.values():
            for host in server.all_hosts:
                pool.append("pool_" + server.all_hosts[host]["software_version"]["product_version"] + "=1")
                for patch in server.all_hosts[host]["patches"]:
                    host_patch = server.all_host_patch[patch]
                    if  host_patch["applied"]:
                        hotfix.append("hotfix_" + server.all_pool_patch[host_patch["pool_patch"]]["uuid"] + "=1")
                    else:
                        hotfix.append("hotfix_" + server.all_pool_patch[host_patch["pool_patch"]]["uuid"] + "=0")

        url = "http://updates.xensource.com/XenServer/5.5.2/XenCenter?%s;%s" % (";".join(pool), ";".join(hotfix))
        import webbrowser
        webbrowser.open(url)
    def on_menuitem_xenserver_on_the_web_activate(self, widget, data=None):
        """
        "Xenserver on the web" menu item is pressed (help)
        """
        url = "www.xenserver.com"
        import webbrowser
        webbrowser.open(url)

    def on_menuitem_help_activate(self, widget, data=None):
        """
        "About" menu item is pressed (Help)
        """
        # Show about dialog
        self.builder.get_object("aboutdialog").show()
    def on_menuitem_pool_remove_server_activate(self, widget, data=None):
        """
        "Remove server" (from pool) menu item is pressed (pool)
        """
        self.last_dialog_label = self.builder.get_object("removeserverfrompool").get_property("text")
        label = self.builder.get_object("removeserverfrompool").get_property("text")
        pool_ref = self.xc_servers[self.selected_host].all_pools.keys()[0]
        self.builder.get_object("removeserverfrompool").set_markup(
                label.replace("{0}", self.selected_name).replace("{1}",
                    self.xc_servers[self.selected_host].all_pools[pool_ref]["name_label"]) )
        self.builder.get_object("removeserverfrompool").show()
    def on_acceptremoveserverfrompool_clicked(self, widget, data=None):
        """
        Function called when you accept remove server from pool
        """
        Thread(target=self.xc_servers[self.selected_host].remove_server_from_pool,
                args=(self.selected_ref,)).start()
        self.builder.get_object("removeserverfrompool").hide()
        self.builder.get_object("removeserverfrompool").set_markup(self.last_dialog_label)
    def on_cancelremoveserverfrompool_clicked(self, widget, data=None):
        """
        Function called when you accept remove server from pool
        """
        self.builder.get_object("removeserverfrompool").hide()
        self.builder.get_object("removeserverfrompool").set_markup(self.last_dialog_label)

    def on_menuitem_pool_backupdb_activate(self, widget, data=None):
        """
        "Backup database" menu item is pressed(pool)
        """
        self.builder.get_object("filterfilepoolbackupdb").add_pattern("*.xml")
        filepoolbackupdb = self.builder.get_object("filepoolbackupdb")
        filepoolbackupdb.set_current_name(self.selected_name + "_backup_db.xml")
        filepoolbackupdb.show()
    def on_cancelfilepoolbackupdb_clicked(self, widget, data=None):
        """
        "Cancel" press on file chooser dialog for database pool backup
        """
        self.builder.get_object("filepoolbackupdb").hide()
    def on_acceptfilepoolbackupdb_clicked(self, widget, data=None):
        """
        "Cancel" press on file chooser dialog for database pool backup
        """
        filename = self.builder.get_object("filepoolbackupdb").get_filename()
        self.xc_servers[self.selected_host].pool_backup_database(self.selected_ref, filename, self.selected_name)
        self.builder.get_object("filepoolbackupdb").hide()

    def on_rebootconfirmpoolrestoredb_clicked(self, widget, data=None):
        """
        "Reboot" press on dialog restore database pool (reboot/dry run/cancel)
        """
        self.builder.get_object("confirmpoolrestoredb").hide()
        filename = self.builder.get_object("filepoolrestoredb").get_filename()
        Thread(target=self.xc_servers[self.selected_host].pool_restore_database, \
                args=(self.selected_ref, filename, self.selected_name, "false")).start()

        self.builder.get_object("filepoolrestoredb").hide()
    def on_dryrunconfirmpoolrestoredb_clicked(self, widget, data=None):
        """
        "Dry run" press on dialog restore database pool (reboot/dry run/cancel)
        """
        self.builder.get_object("confirmpoolrestoredb").hide()
        filename = self.builder.get_object("filepoolrestoredb").get_filename()
        Thread(target=self.xc_servers[self.selected_host].pool_restore_database, \
                args=(self.selected_ref, filename, self.selected_name, "true")).start()

        self.builder.get_object("filepoolrestoredb").hide()

    def on_cancelconfirmpoolrestoredb_clicked(self, widget, data=None):
        """
        "Dry run" press on dialog restore database pool (reboot/dry run/cancel)
        """
        self.builder.get_object("confirmpoolrestoredb").hide()
        self.builder.get_object("filepoolbackupdb").hide()


    def on_menuitem_pool_restoredb_activate(self, widget, data=None):
        """
        "Restore database" menu item is pressed(pool)
        """
        self.builder.get_object("filepoolrestoredb").show()

    def on_cancelfilepoolrestoredb_clicked(self, widget, data=None):
        """
        "Cancel" press on file chooser dialog for database pool restore 
        """
        self.builder.get_object("filepoolrestoredb").hide()

    def on_acceptfilepoolrestoredb_clicked(self, widget, data=None):
        """
        "Open" press on file chooser dialog for database pool restore 
        """
        self.builder.get_object("confirmpoolrestoredb").show()

        self.builder.get_object("filepoolrestoredb").hide()


    def on_menuitem_pool_disconnect_activate(self, widget, data=None):
        """
        "Disconnect" (from pool) menu item is pressed
        """
        self.on_m_disconnect_activate(widget, data)
    def on_menuitem_pool_new_activate(self, widget, data=None):
        """
        "New Pool..." menu item is pressed
        """
        listpoolmaster = self.builder.get_object("listpoolmaster")
        listpoolmaster.clear()
        combopoolmaster = self.builder.get_object("combopoolmaster")

        # For each server add to combobox master servers list
        for host in self.config_hosts.keys():
           # If server is connected..
           if host in self.xc_servers:
               # Add to combo
               pool = False
               for pool_ref in  self.xc_servers[host].all_pools:
                   if self.xc_servers[host].all_pools[pool_ref]['name_label'] != "":
                        pool = True
               if not pool:
                   listpoolmaster.append([host, self.xc_servers[host].hostname])
        # Set the first as default
        combopoolmaster.set_active(0)
        ref = None
        # If there are servers added to combobox, get the ref
        if combopoolmaster.get_active_iter():
            ref = listpoolmaster.get_value(combopoolmaster.get_active_iter(), 0)

        listpoolvms = self.builder.get_object("listpoolvms")
        listpoolvms.clear()
        # For each server add to possible servers for pool
        for host in self.config_hosts.keys():
           if host not in self.xc_servers:
               listpoolvms.append([None, host, 0, "Disconnected", False])
           else:
               if self.xc_servers[host].is_connected:
                   pool = False
                   for pool_ref in  self.xc_servers[host].all_pools:
                       if self.xc_servers[host].all_pools[pool_ref]['name_label'] != "":
                            pool = True
                   if not pool:
                       if ref != host:
                           listpoolvms.append([host, self.xc_servers[host].hostname, False, "", True])
                       else:
                           listpoolvms.append([host, self.xc_servers[host].hostname, True, "Master", False])
                   else:
                       listpoolvms.append([host, self.xc_servers[host].hostname, False, "This server is already in a pool", False])
               else:
                   listpoolvms.append([None, host, 0, "Disconnected", False])
         
        # Show the "newpool" window
        self.builder.get_object("newpool").show()
    def update_menubar(self):
        """
        This function is called when a VM, host, storage or template is selected
        Depends if you selected a server, host (server connected), vm then 
        A menuitems are enabled and others are disabled

        """
        show = {}
        if self.selected_type == "pool":
            show["menu5"] =  ["menuitem_pool_new", "menuitem_pool_delete", "menuitem_pool_disconnect","menuitem_pool_prop", "menuitem_pool_backupdb", "menuitem_pool_restoredb", "menuitem_pool_add_server"]
            # TODO: disable menuite_connectall
            show["menu6"] =  ["menuitem_addserver", "menuitem_disconnectall", "menuitem_connectall", "menuitem_forget", "menuitem_remove"]
            show["menu7"] =  ["menuitem_importvm2"]
            show["menu8"] =  [""]
            show["menu9"] =  [""]
            show["menu10"] =  ["menuitem_options", "menuitem_migratetool", "menuitem_tools_updatemanager"]
        if self.selected_type == "home":
            show["menu5"] =  [""]
            # TODO: disable menuite_connectall
            show["menu6"] =  ["menuitem_addserver", "menuitem_connectall", "menuitem_disconnectall"]
            show["menu7"] =  ["menuitem_importvm2"]
            show["menu8"] =  [""]
            show["menu9"] =  [""]
            show["menu10"] =  ["menuitem_options","menuitem_tools_alerts", "menuitem_migratetool"]
        if self.selected_type == "server":
            if self.selected_state == "Disconnected":
                show["menu5"] =  ["menuitem_pool_new"]
                # TODO: disable menuite_connectall
                show["menu6"] =  ["menuitem_addserver", "menuitem_disconnectall", "menuitem_connectall", "menuitem_connect", "menuitem_forget", "menuitem_remove"]
                show["menu7"] =  ["menuitem_importvm2"]
                show["menu8"] =  [""]
                show["menu9"] =  [""]
                show["menu10"] =  ["menuitem_options", "menuitem_migratetool"]
        if self.selected_type == "host":
                show["menu5"] =  ["menuitem_pool_new"]
                # TODO: use allowed_operations reboot/shutdown
                show["menu6"] =  ["menuitem_addserver", "menuitem_disconnectall", "menuitem_disconnect", "menuitem_forget",\
                        "menuitem_remove",  "menuitem_newvm", "menuitem_server_prop", "menuitem_mgmt_ifs", "menuitem_dmesg",\
                        "menuitem_server_reboot", "menuitem_server_shutdown",  "menuitem_changepw","menuitem_backupserver", \
                        "menuitem_restoreserver","menuitem_install_xslic","menuitem_server_add_to_pool", \
                        "menuitem_downloadlogs"
                        ]
                show["menu7"] =  ["menuitem_importvm2", "menuitem_newvm2"]
                show["menu8"] =  ["menuitem_stg_new"]
                show["menu9"] =  ["menuitem_tpl_import"]
                show["menu10"] =  ["menuitem_options","menuitem_tools_alerts", "menuitem_takescreenshot", "menuitem_migratetool", "menuitem_tools_statusreport", "menuitem_tools_updatemanager"]
                pool_ref = self.xc_servers[self.selected_host].all_pools.keys()[0]
                
                if self.xc_servers[self.selected_host].all_hosts[self.selected_ref]["enabled"]:
                    show["menu6"].append("menuitem_entermaintenancemode")
                else:
                    show["menu6"].append("menuitem_exitmaintenancemode")
                
                if self.xc_servers[self.selected_host].all_pools[pool_ref]["name_label"] != '' and \
                        self.xc_servers[self.selected_host].all_pools[pool_ref]["master"] != self.selected_ref:
                    show["menu5"].append("menuitem_pool_remove_server") 
        if self.selected_type == "vm":
                show["menu6"] =  ["menuitem_newvm", "menuitem_server_prop", "menuitem_mgmt_ifs", "menuitem_addserver", "menuitem_disconnectall"]
                show["menu7"] =  ["menuitem_importvm2", "menuitem_newvm2", "menuitem_vm_prop"]
                show["menu8"] =  ["menuitem_stg_new", "menuitem_stg_newvdi", "menuitem_stg_attachvdi"]
                show["menu9"] =  ["menuitem_tpl_import"]
                show["menu10"] =  ["menuitem_options","menuitem_tools_alerts", "menuitem_takescreenshot", "menuitem_migratetool"]
                # Special case
                # If in allowed operations of selected VM exists "start", then add the menu item "start in recovery mode"
                for op in self.xc_servers[self.selected_host].all_vms[self.selected_ref]['allowed_operations']:
                    show["menu7"].append("menuitem_vm_" + op)
                    if op == "start":
                        show["menu7"].append("menuitem_vm_startrecovery")
                if self.selected_state == "Running":
                    show["menu7"].append("menuitem_vm_install_xs_tools")
        if self.selected_type == "storage":
            show["menu5"] =  ["menuitem_pool_new"]
            show["menu6"] =  ["menuitem_addserver", "menuitem_connectall", "menuitem_disconnectall","menuitem_newvm"]
            show["menu7"] =  ["menuitem_importvm2","menuitem_newvm2"]
            show["menu8"] =  ["menuitem_stg_new","menuitem_stg_newvdi", "menuitem_stg_attachvdi"]
            show["menu9"] =  [""]
            show["menu10"] =  ["menuitem_options","menuitem_tools_alerts", "menuitem_migratetool"]
            if self.xc_servers[self.selected_host].all_storage[self.selected_ref]['allowed_operations'].count("vdi_create")>0:
                show["menu8"].append("menuitem_stg_default")
        if self.selected_type == "template":
            show["menu5"] =  ["menuitem_pool_new"]
            show["menu6"] =  ["menuitem_addserver", "menuitem_connectall", "menuitem_disconnectall","menuitem_newvm"]
            show["menu7"] =  ["menuitem_importvm2","menuitem_newvm2"]
            show["menu8"] =  ["menuitem_stg_new","", ""]
            show["menu9"] =  ["menuitem_tpl_newvm", "menuitem_tpl_import", "menuitem_tpl_export", "menuitem_tpl_copy", "menuitem_tpl_delete"]
            show["menu10"] =  ["menuitem_options","menuitem_tools_alerts", "menuitem_migratetool"]

        # For each menu...
        for menu in show:
            # For each child of this menu..
            for child in self.builder.get_object(menu).get_children():
                # Check if is on "show" variable
                if show[menu].count(gtk.Buildable.get_name(child)):
                    # If is on: enable menuitem
                    child.set_sensitive(True)
                else:
                    # Else: disable menuitem
                    child.set_sensitive(False)
    def on_tm_logwindow_activate(self, widget, data=None):
        # TODO: fix it URGENT
        for i in range(1, 1):
            self.builder.get_object("logwindow").show()
            vboxframe = gtk.Frame()
            if i % 2 == 0:
                vboxframe.set_size_request(500,100)
            else:
                vboxframe.set_size_request(500,80)
            vboxchild = gtk.Fixed()
            vboxchildlabel1 = gtk.Label()
            vboxchildlabel2 = gtk.Label()
            vboxchildlabel3 = gtk.Label()
            vboxchildlabel4 = gtk.Label()
            vboxchildlabel5 = gtk.Label()
            #FIXME
            #vboxchildprogressbar.set_style(1)
            vboxchildlabel1.set_label("Starting ... ")
            vboxchildlabel2.set_label("23:28 04/08/2009")
            vboxchildlabel3.set_label("Details: problem starting..")
            vboxchildlabel4.set_label("Time: 00:00:00")

            vboxchild.put(vboxchildlabel1, 25, 12)
            vboxchild.put(vboxchildlabel2, 800, 12)
            vboxchild.put(vboxchildlabel3, 25, 32)
            vboxchild.put(vboxchildlabel4, 25, 52)

            # Active task
            if i % 2 == 0:
                vboxchildcancel = gtk.Button()
                vboxchildprogressbar = gtk.ProgressBar()
                vboxchildprogressbar.set_size_request(800,20)
                vboxchildprogressbar.set_fraction(float(1/float(i)))
                vboxchild.put(vboxchildcancel, 800, 32)
                vboxchildcancel.set_label("Cancel")
                vboxchildlabel5.set_label("Progress: ")
                vboxchild.put(vboxchildprogressbar, 100, 72)
                vboxchild.put(vboxchildlabel5, 25, 72)

            vboxframe.add(vboxchild)
            if i % 2 == 0:
                vboxframe.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
            else:
                vboxframe.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))

            self.builder.get_object("vboxlog").add(vboxframe)
            self.builder.get_object("vboxlog").show_all()

