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

class oxcSERVERhostnics:
    def delete_nic(self, ref_nic, ref_vm, delete_network=True):
        ref_bond = self.all_pif[ref_nic]['bond_master_of'][0]
        ref_network = self.all_pif[ref_nic]['network']
        res = self.connection.Bond.destroy(self.session_uuid, ref_bond)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref_vm
        else:
            print res   
        if delete_network:
            res = self.connection.network.destroy(self.session_uuid, ref_network)
            if "Value" in res:
                self.track_tasks[res['Value']] = ref_vm
            else:
                print res        

    def fill_available_nics(self, list, list2):
        list.clear()
        list2.clear()
        for pif_key in self.all_pif.keys():
            if self.all_pif[pif_key]['metrics'] != "OpaqueRef:NULL":
                pif_metric = {}
                if self.all_pif[pif_key]['metrics'] in self.all_pif_metrics:
                    pif_metric = self.all_pif_metrics[self.all_pif[pif_key]['metrics']]
                else:
                    pif_metric["pci_bus_path"] = "N/A"
            pif = self.all_pif[pif_key]
            if self.all_pif[pif_key]['metrics'] != "OpaqueRef:NULL" and pif_metric['pci_bus_path'] != "N/A":
                nic = "NIC %s" % pif['device'][-1:]
                error = ""
                if len(self.all_network[pif['network']]['VIFs']):
                    error = "in use by VMs"
                if pif['bond_slave_of'] != "OpaqueRef:NULL" and pif['bond_slave_of'] in self.all_bond:
                    devices = []
                    for slave in self.all_bond[pif['bond_slave_of']]['slaves']:
                            devices.append(self.all_pif[slave]['device'][-1:])
                    devices.sort() 
                    error = "already in Bond %s" % ('+'.join(devices))
                list.append([pif_key,nic,error,error == ""])

    def create_bond(self, ref, ref2, name, name2,auto=False):
        network_cfg = {
                'uuid' : '',
                'name_label': "Bond %s+%s" % (name[-1:], name2[-1:]),
                'name_description': '',
                'VIFs': [],
                'PIFs': [],
                'other_config': {
                        'XenCenterCreateInProgress': "true"
                        },
                'bridge': '',
                'blobs': {}
             }
        if auto:
            network_cfg['other_config']['automatic'] = "true"
        else:
            network_cfg['other_config']['automatic'] = "false"
        res = self.connection.network.create(self.session_uuid, network_cfg) 
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
            network = res['Value']
        else:
            print res

        res = self.connection.Async.Bond.create(self.session_uuid, network, [ref, ref2],"")
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def fill_nic_info(self, ref):
        pif = self.all_pif[ref]
        pif_metric = self.all_pif_metrics[self.all_pif[ref]['metrics']]
        if pif_metric['duplex']:
            duplex = "full"
        else:
            duplex = "half"
        if "mac" in pif:
                mac = pif['mac']
        else:
                mac = ""
        connected = "Disconnected"
        if pif_metric['carrier']:
                connected = "Connected"
        labels = {}
        labels['lblnicname'] = "NIC %s" % pif['device'][-1:]
        labels['lblnicvendor'] =  pif_metric['vendor_name']
        labels['lblnicdevice'] = pif_metric['device_name'] 
        labels['lblnicmac'] =  mac
        labels['lblnicpcibus'] = pif_metric['pci_bus_path']
        labels['lblniclinkstatus'] = connected 
        if connected == "Connected":
            labels['lblnicspeed'] = pif_metric['speed'] + " mbit/s"
        else:
            labels['lblnicspeed'] = ""
        labels['lblnicduplex'] =  duplex
        for label in labels.keys():
            self.wine.builder.get_object(label).set_label(labels[label])

