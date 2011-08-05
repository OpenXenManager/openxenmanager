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
import xtea
from oxcSERVER import *
class oxcWindowAddServer:
    """
    Class with functions to manage "add server" window
    """
    def on_addserver_clicked(self, widget, data=None):
        """
        Function called when you press "add server" button 
        """
        # Show the add server window
        self.builder.get_object("addserver").show_all()
        self.builder.get_object("addserverhostname").grab_focus()
    def on_imageaddserver_button_press_event(self, widget, data=None):
        """
        Function called when you press main image to add "add server"
        """
        # Show the add server window
        self.builder.get_object("addserver").show()
        self.builder.get_object("addserverpassword").grab_focus()
    def on_addserverhostname_changed(self, widget, data=None):
        """
        Function called when hostname/ip text field is changed
        """
        # Get "connect" button object
        connectAddServer = self.builder.get_object("connectAddServer")
        # widget.get_active_text() contains the ip/hostname
        if len(widget.get_active_text()) > 0:
            # If is not empty, enable the button
            connectAddServer.set_sensitive(True)
        else:
            # If is empty, disable the button
            connectAddServer.set_sensitive(False)
    def on_connectAddServer_clicked(self, widget, data=None):
        """
        Function called when you press the "connect" button 
        """
        # Get host, username and password
        host = self.builder.get_object("addserverhostname").get_active_text()
        user = self.builder.get_object("addserverusername").get_text()
        password = self.builder.get_object("addserverpassword").get_text()
        # Call to "add_server" function with params
        # This function try connect to server and authenticate
        self.add_server(host, user, password)
    def on_cancelAddServer_clicked(self, widget, data=None):
        """
        Function called when you press the "cancel" button on "add server" dialog
        """
        self.builder.get_object("addserver").hide()
    def update_progressconnect(self):
        """
        Function to update "progress connect" while is loading
        """
        #gtk.gdk.threads_enter()
        self.builder.get_object("progressconnect").pulse()
        #gtk.gdk.threads_leave()
    def finish_progressconnect(self, success=True):
        """
        Function called when connection loading is finished
        """
        if success:
            # Create a new thread it receives updates
            # Fill alerts list on "alerts" window
            self.xc_servers[self.selected_host].fill_alerts(self.listalerts)
            self.update_n_alerts()
        # Hide window progress
        gobject.idle_add(lambda: self.hide_wprogressconnect() and False)
        
        # Setting again the modelfiter it will be refresh internal path/references
        self.treeview.set_model(self.modelfilter)
        self.treeview.expand_all()
        self.xc_servers[self.selected_host].thread_event_next()

    def hide_wprogressconnect(self):
        self.builder.get_object("wprogressconnect").hide()
        
    def add_server(self, host, user, password, iter=None, ssl = None):
        """
        Function used to connect to server
        """
        self.builder.get_object("addserver").hide()
        #Show a dialog with a progress bar.. it should be do better
        self.builder.get_object("wprogressconnect").show()
        # Check if SSL connection is selected
        if ssl == None:
            ssl = self.builder.get_object("checksslconnection").get_active()
        else:
            self.builder.get_object("checksslconnection").set_active(ssl)
        # Create a new oxcSERVER object, creating object connects to server too
        self.builder.get_object("lblprogessconnect").set_label("Connecting to %s..." % (host))
        self.xc_servers[host] = oxcSERVER(host,user,password, self, ssl)
        Thread(target=self.xc_servers[host].update_connect_status).start()
    
    def finish_add_server(self, host, user, password, iter=None, ssl = None):
        if self.xc_servers[host].is_connected == True:
            # If we are connected to server (authentication is ok too)
            if (self.selected_iter or iter) and self.selected_type == "server":
                # Remove from left tree, it will be created again with "fill_tree_with_vms"
                if iter:
                    self.treestore.remove(iter)
                else:
                    self.treestore.remove(self.selected_iter)
            # Hide "add server" window
            self.builder.get_object("addserver").hide()
            # Append to historical host list on "add server" window
            self.builder.get_object("listaddserverhosts").append([host])
            # Fill left tree and get all data (pool, vm, storage, template..)
            #self.xc_servers[host].fill_tree_with_vms(self.treestore, self.treeroot, self.treeview)
            self.builder.get_object("lblprogessconnect").set_label("Synchronizing...")
            t = Thread(target=self.xc_servers[host].fill_tree_with_vms, args=(self.treestore, self.treeroot, self.treeview))
            t.start()
            # Remember, we are connected, if we use a master password then save the password
            # Password is saved encrypted with XTEA
            if self.password:
                z = xtea.crypt("X" * (16-len(self.password)) + self.password, password, self.iv)
                self.config_hosts[host] = [user, z.encode("hex"), ssl]
            else:
                self.config_hosts[host] = [user, "", ssl]
            self.config['servers']['hosts'] = self.config_hosts
            # Save relation host/user/passwords to configuration
            self.config.write()
        else:
            # If connection failed.. show add server dialog again
            self.builder.get_object("addserver").show()
            # Append to historical host list on "add server" window
            # And hide progress bar
            self.builder.get_object("wprogressconnect").hide()
            # Show a alert dialog showing error
            self.show_error_dlg("%s" % self.xc_servers[host].error_connecting, "Error connecting")
        
        if self.selected_host == None:
            self.selected_host = host

