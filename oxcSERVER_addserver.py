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

class oxcSERVERaddserver:
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
    
   def fill_tree_with_vms(self, treestore, treeroot, treeview, get_data=True):
        # Get all vm records
        if get_data:
            self.wine.update_progressconnect()
            result = self.connection.VM.get_all_records\
                      (self.session_uuid)
            if "Value" in result:
                self.all_vms = result['Value']
            else:
                self.wine.finish_progressconnect(False)
                if "HOST_IS_SLAVE" in result["ErrorDescription"]:
                    gobject.idle_add(lambda: self.wine.show_error_dlg("HOST IS SLAVE, please connect to: %s" % (result["ErrorDescription"][1])) and False)
                else:
                    print result
                #self.wine.show_error_dlg(str(result["ErrorDescription"]))
                return

            # Get all
            self.wine.update_progressconnect()
            self.all_tasks = self.connection.task.get_all_records(
                      self.session_uuid)['Value']
            
            for task in self.all_tasks.keys():
                self.tasks[task] = self.all_tasks[task]
            self.wine.update_progressconnect()
            self.all_vbd = self.connection.VBD.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_vbd_metrics = self.connection.VBD_metrics.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_vdi = self.connection.VDI.get_all_records(self.session_uuid)['Value']
            
            self.wine.update_progressconnect()
            self.all_network = self.connection.network.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_pif = self.connection.PIF.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_pif_metrics= self.connection.PIF_metrics.get_all_records(self.session_uuid)['Value']

            self.wine.update_progressconnect()
            self.all_pbd = self.connection.PBD.get_all_records(self.session_uuid)['Value']
            
            self.wine.update_progressconnect()
            self.all_vif = self.connection.VIF.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_vif_metrics = self.connection.VIF_metrics.get_all_records(self.session_uuid)['Value']
            self.all_vlan = self.connection.VIF_metrics.get_all_records(self.session_uuid)['Value']


            self.wine.update_progressconnect()
            self.all_vm_guest_metrics = self.connection.VM_guest_metrics.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_vm_metrics = self.connection.VM_metrics.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_host_metrics = self.connection.host_metrics.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_host_cpu = self.connection.host_cpu.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_bond = self.connection.Bond.get_all_records(self.session_uuid)['Value']

            self.wine.update_progressconnect()
            self.all_pool_patch = self.connection.pool_patch.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_host_patch = self.connection.host_patch.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_console = self.connection.console.get_all_records(self.session_uuid)['Value']

            # Get all host records
            self.wine.update_progressconnect()
            self.all_hosts = self.connection.host.get_all_records(self.session_uuid)['Value']
            # Get all pool records
            self.wine.update_progressconnect()
            self.all_pools = self.connection.pool.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_storage = self.connection.SR.get_all_records(self.session_uuid)['Value']
            self.wine.update_progressconnect()
            self.all_console = self.connection.console.get_all_records(self.session_uuid)['Value']

            try:
                self.all_subject= self.connection.subject.get_all_records(self.session_uuid)['Value']
                self.all_role = self.connection.role.get_all_records(self.session_uuid)['Value']
            except:
                pass

 

        poolroot = None 
        hostroot = {}
        root = ""
        self.treestore = treestore
        self.default_sr = ""
        gtk.gdk.threads_enter()
        for pool in self.all_pools.keys():
            self.default_sr = self.all_pools[pool]['default_SR']
            if self.all_pools[pool]['name_label']:
                poolroot =  treestore.append(treeroot, [gtk.gdk.pixbuf_new_from_file\
                    ("images/poolconnected_16.png"),\
                    self.all_pools[pool]['name_label'], pool, "pool", "Running", self.host, pool, ['newvm', 'newstorage', 'importvm', 'disconnect'], self.host])
        if poolroot:
            relacion = {}
            for ref in self.all_hosts.keys():
                relacion[str(self.all_hosts[ref]['name_label'] + "_" + ref)] = ref
            self.all_hosts_keys = []
            rkeys = relacion.keys()
            rkeys.sort(key=str.lower)
            for ref in rkeys:
                self.all_hosts_keys.append(relacion[ref])
            for h in self.all_hosts_keys:
                host_uuid = self.all_hosts[h]['uuid']
                host = self.all_hosts[h]['name_label']
                host_enabled = self.all_hosts[h]['enabled']
                host_address = self.all_hosts[h]['address']
                if host_enabled:
                    hostroot[h] = treestore.append(poolroot, [gtk.gdk.pixbuf_new_from_file\
                                ("images/tree_connected_16.png"),\
                                host, host_uuid, "host", "Running", self.host, h,\
                                ['newvm', 'importvm', 'newstorage', 'clean_reboot', 'clean_shutdown', 'shutdown'], host_address])
                else:
                    hostroot[h] = treestore.append(poolroot, [gtk.gdk.pixbuf_new_from_file\
                                ("images/tree_disabled_16.png"),\
                                host, host_uuid, "host", "Disconnected", self.host, h, \
                                [], host_address])
            root = poolroot
        else:
           host_uuid = self.all_hosts[self.all_hosts.keys()[0]]['uuid']
           host = self.all_hosts[self.all_hosts.keys()[0]]['name_label']
           host_address = self.all_hosts[self.all_hosts.keys()[0]]['address']
           host_enabled = self.all_hosts[self.all_hosts.keys()[0]]['enabled']
           if host_enabled:
               hostroot[self.all_hosts.keys()[0]] = treestore.append(treeroot, [gtk.gdk.pixbuf_new_from_file\
                            ("images/tree_connected_16.png"),\
                            host, host_uuid, "host", "Running", self.host, self.all_hosts.keys()[0], 
                            ['newvm', 'importvm', 'newstorage', 'clean_reboot', 'clean_shutdown', 'shutdown', 'disconnect'], host_address])
           else:
               hostroot[self.all_hosts.keys()[0]] = treestore.append(treeroot, [gtk.gdk.pixbuf_new_from_file\
                            ("images/tree_disabled_16.png"),\
                            host, host_uuid, "host", "Running", self.host, self.all_hosts.keys()[0], 
                            ['newvm', 'importvm', 'newstorage', 'clean_reboot', 'clean_shutdown', 'shutdown', 'disconnect'], host_address])
           root = hostroot[self.all_hosts.keys()[0]]
        self.hostname = host
        self.hostroot = hostroot
        self.poolroot = poolroot
        relacion = {}
        for ref in self.all_vms.keys():
            relacion[str(self.all_vms[ref]['name_label'] + "_" + ref)] = ref
        self.all_vms_keys = []
        rkeys = relacion.keys()
        rkeys.sort(key=str.lower)
        for ref in rkeys:
            self.all_vms_keys.insert(0,relacion[ref])


        for vm in self.all_vms_keys:
            if not self.all_vms[vm]['is_a_template']:
                if not self.all_vms[vm]['is_control_domain']:
                  self.add_vm_to_tree(vm)
                  for operation in self.all_vms[vm]["current_operations"]:
                    self.track_tasks[operation] = vm
                else:
                  self.host_vm[self.all_vms[vm]['resident_on']] = [vm,  self.all_vms[vm]['uuid']]
  
        # Get all storage record 
        for sr in self.all_storage.keys():
            if self.all_storage[sr]['name_label'] != "XenServer Tools":
                if len(self.all_storage[sr]['PBDs']) == 0:
                    self.last_storage_iter = treestore.append(root, [\
                           gtk.gdk.pixbuf_new_from_file("images/storage_detached_16.png"),\
                             self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                             "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None])
                    continue
                broken = False
                for pbd_ref in self.all_storage[sr]['PBDs']:
                    if not self.all_pbd[pbd_ref]['currently_attached']:
                        broken = True
                        self.last_storage_iter = treestore.append(root, [\
                               gtk.gdk.pixbuf_new_from_file("images/storage_broken_16.png"),\
                                 self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                                 "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None])
                if not broken:
                    if self.all_storage[sr]['shared']:
                        if sr == self.default_sr:
                            self.last_storage_iter = treestore.append(root, [\
                               gtk.gdk.pixbuf_new_from_file("images/storage_default_16.png"),\
                                 self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                                 "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None])
                        else:
                            self.last_storage_iter = treestore.append(root, [\
                               gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png"),\
                                 self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                                 "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None])

                    else:
                        for pbd in self.all_storage[sr]['PBDs']:
                            if sr == self.default_sr:
                                if self.all_pbd[pbd]['host'] in hostroot:
                                    self.last_storage_iter = treestore.append(hostroot[self.all_pbd[pbd]['host']], [\
                                        gtk.gdk.pixbuf_new_from_file("images/storage_default_16.png"),\
                                         self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                                         "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None])
                                else:
                                    self.last_storage_iter = treestore.append(root, [\
                                       gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png"),\
                                         self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                                         "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None])

                            else:
                                if self.all_pbd[pbd]['host'] in hostroot:
                                    self.last_storage_iter = treestore.append(hostroot[self.all_pbd[pbd]['host']], [\
                                        gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png"),\
                                         self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                                         "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None])
                                else:
                                    self.last_storage_iter = treestore.append(root, [\
                                       gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png"),\
                                         self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                                         "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None])


                    
        for tpl in self.all_vms_keys:
            if self.all_vms[tpl]['is_a_template'] and not self.all_vms[tpl]['is_a_snapshot']: 
                if self.all_vms[tpl]['last_booted_record'] == "":
                     treestore.append(root, [\
                        gtk.gdk.pixbuf_new_from_file("images/template_16.png"),\
                        self.all_vms[tpl]['name_label'], self.all_vms[tpl]['uuid'],\
                        "template", None, self.host, tpl, self.all_vms[tpl]['allowed_operations'], None])
                else:
                     tpl_affinity = self.all_vms[tpl]['affinity']
                    
                     if tpl_affinity in hostroot: 
                         treestore.append(hostroot[tpl_affinity], [\
                            gtk.gdk.pixbuf_new_from_file("images/user_template_16.png"),\
                            self.all_vms[tpl]['name_label'], self.all_vms[tpl]['uuid'],\
                            "custom_template", None, self.host, tpl, self.all_vms[tpl]['allowed_operations'], None])
                     else:
                         treestore.append(root, [\
                            gtk.gdk.pixbuf_new_from_file("images/user_template_16.png"),\
                            self.all_vms[tpl]['name_label'], self.all_vms[tpl]['uuid'],\
                            "custom_template", None, self.host, tpl, self.all_vms[tpl]['allowed_operations'], None])

        treeview.expand_all()
        self.wine.finish_progressconnect()
        gtk.gdk.threads_leave()

