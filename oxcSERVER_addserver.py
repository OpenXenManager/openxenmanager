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
import xmlrpclib, urllib
import asyncore, socket
import select
import gtk
from os import chdir
import platform
import sys, shutil
import datetime
from threading import Thread
from configobj import ConfigObj
import xml.dom.minidom 
from operator import itemgetter
import pdb
import rrdinfo
import time
import gobject
from messages import messages, messages_header

class oxcSERVERaddserver(gobject.GObject):
    __gsignals__ = {
        "connect-success": (gobject.SIGNAL_RUN_FIRST, None, ()),
        "connect-failure": (gobject.SIGNAL_RUN_FIRST, None, (str,)),
        "sync-progress": (gobject.SIGNAL_RUN_FIRST, None, (str,)),
        "sync-success": (gobject.SIGNAL_RUN_FIRST, None, ()),
        "sync-failure": (gobject.SIGNAL_RUN_FIRST, None, (str,))
    }

    connectThread = None
    
    def __init__(self):
         self.__gobject_init__()

    def connect_server_async(self):
        # begin connecting
        self.connectThread = Thread(target=self.connect_server)
        self.connectThread.start()
            
    def connect_server(self):
        protocol = ["http", "https"][self.ssl]
        self.url = "%s://%s" % (protocol, self.host)
        self.connection = xmlrpclib.Server(self.url)
        self.connection_events = xmlrpclib.Server(self.url)
        try:
            self.session = self.connection.session.login_with_password(self.user, self.password) 
            if self.session['Status']  == "Success":
                self.is_connected = True
                self.session_uuid = self.session['Value']
                self.session_events = self.connection_events.session.login_with_password(self.user, self.password) 
                self.session_events_uuid = self.session_events['Value']
                self.connection_events.event.register(self.session_events_uuid, ["*"])
                # tell the controller that we've finished
                self.emit("connect-success")
            else:
                self.emit("connect-failure", self.session['ErrorDescription'][2])
        except:
            self.emit("connect-failure", sys.exc_info()[1])
        
    def thread_event_next(self):
        Thread(target=self.event_next, args=()).start()
        return True

    def fill_alerts(self, list):
        #FIXME priority: 1 info 5 alert
        self.all_messages = self.connection.message.get_all_records(
                  self.session_uuid)['Value']
        relacion = {}
        for ref in self.all_messages.keys():
            relacion[self.get_seconds(str(self.all_messages[ref]['timestamp']))] = ref
        rkeys = relacion.keys()
        rkeys.sort()
        for ref in rkeys:
            message = self.all_messages[relacion[ref]]
            self.add_alert(message, relacion[ref], list)
    
    def sync(self):
        try:
            # Get all vm records
            self.emit("sync-progress", "Retrieving VMs")
            result = self.connection.VM.get_all_records(self.session_uuid)
            if "Value" not in result:
                if "HOST_IS_SLAVE" in result["ErrorDescription"]:
                    # TODO: csun: automatically connect instead
                    error = "The host server \"%s\" is a slave in a pool; please connect to the master server at \"%s\"." % (self.host, result["ErrorDescription"][1])
                else:
                    error = "Unknown error:\n%s" % str(result["ErrorDescription"])
                self.emit("sync-failure", self, error)
                return
            
            self.all_vms = result.get('Value')

            self.emit("sync-progress", "Retrieving hosts")
            self.all_hosts = self.connection.host.get_all_records(self.session_uuid).get('Value')
            
            # DEBUG
            for ref in self.all_hosts:
                print "Server version is %s" % (["%s" % (self.all_hosts[ref]['software_version'][x]) for x in ('product_brand', 'product_version', 'xapi')] + [self.all_hosts[ref]['license_params']['sku_marketing_name']])
            
            self.emit("sync-progress", "Retrieving pools")
            self.all_pools = self.connection.pool.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving SRs")
            self.all_storage = self.connection.SR.get_all_records(self.session_uuid).get('Value')

            self.emit("sync-progress", "Retrieving tasks")
            self.all_tasks = self.connection.task.get_all_records(self.session_uuid).get('Value')
            for task in self.all_tasks.keys():
                self.tasks[task] = self.all_tasks[task]
            
            self.emit("sync-progress", "Retrieving VBDs")
            self.all_vbd = self.connection.VBD.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving VBD metrics")
            self.all_vbd_metrics = self.connection.VBD_metrics.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving VDIs")
            self.all_vdi = self.connection.VDI.get_all_records(self.session_uuid).get('Value')
            
            self.emit("sync-progress", "Retrieving networks")
            self.all_network = self.connection.network.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving PIFs")
            self.all_pif = self.connection.PIF.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving PIF metrics")
            self.all_pif_metrics= self.connection.PIF_metrics.get_all_records(self.session_uuid).get('Value')

            self.emit("sync-progress", "Retrieving PBDs")
            self.all_pbd = self.connection.PBD.get_all_records(self.session_uuid).get('Value')
            
            self.emit("sync-progress", "Retrieving VIFs")
            self.all_vif = self.connection.VIF.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving VIF metrics")
            # FIXME: csun: all_vif_metrics == all_vlan?
            self.all_vif_metrics = self.connection.VIF_metrics.get_all_records(self.session_uuid).get('Value')
            self.all_vlan        = self.connection.VIF_metrics.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving NIC bonds")
            self.all_bond = self.connection.Bond.get_all_records(self.session_uuid).get('Value')

            self.emit("sync-progress", "Retrieving VM guest metrics")
            self.all_vm_guest_metrics = self.connection.VM_guest_metrics.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving VM metrics")
            self.all_vm_metrics = self.connection.VM_metrics.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving host metrics")
            self.all_host_metrics = self.connection.host_metrics.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving host CPUs")
            self.all_host_cpu = self.connection.host_cpu.get_all_records(self.session_uuid).get('Value')

            self.emit("sync-progress", "Retrieving pool patches")
            self.all_pool_patch = self.connection.pool_patch.get_all_records(self.session_uuid).get('Value')
            self.emit("sync-progress", "Retrieving host patches")
            self.all_host_patch = self.connection.host_patch.get_all_records(self.session_uuid).get('Value')
            
            self.emit("sync-progress", "Retrieving consoles")
            self.all_console = self.connection.console.get_all_records(self.session_uuid).get('Value')

            try:
                # TODO: csun: why can these throw errors?
                self.emit("sync-progress", "Retrieving subjects")
                self.all_subject = self.connection.subject.get_all_records(self.session_uuid).get('Value')
                self.emit("sync-progress", "Retrieving roles")
                self.all_role = self.connection.role.get_all_records(self.session_uuid).get('Value')
            except:
                import traceback
                print "Synchronisation warning:\nRetrieval of subjects/roles threw error:"
                traceback.print_exc()
        except:
            self.emit("sync-failure", "An unknown error occurred. See log output in terminal for details.")
            print "Synchronisation error:\n"
            import traceback
            traceback.print_exc()
        else:
            print "sync-success"
            self.emit("sync-success")


