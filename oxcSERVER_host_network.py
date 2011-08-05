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

class oxcSERVERhostnetwork:
    def fill_listnetworknic(self, list):
        list.clear()
        vlan = [0]
        for pif_key in self.all_pif:
            pif = self.all_pif[pif_key]
            if pif['currently_attached']:
                if len(pif['bond_master_of']):
                    devices = []
                    for slave in self.all_bond[pif['bond_master_of'][0]]['slaves']:
                        devices.append(self.all_pif[slave]['device'][-1:])
                    devices.sort()
                    list.append([pif_key,"Bond %s" % '+'.join(devices)])

                else:
                    if pif['VLAN'] == "-1":
                        list.append([pif_key,"NIC %s" % pif['device'][-1:]])
                    else:
                        vlan.append(pif['VLAN'])
        return int(max(vlan))+1
    def delete_network(self, ref_network, ref_vm):
        print self.all_network[ref_network]
        for ref_pif in self.all_network[ref_network]['PIFs']:
            if len(self.all_pif[ref_pif]['bond_master_of']):
                self.delete_nic(ref_pif, ref_vm, False)
            else:
                res = self.connection.PIF.destroy(self.session_uuid, ref_pif)
                if "Value" in res:
                    self.track_tasks[res['Value']] = ref_vm
                else:
                    print res        
        res = self.connection.network.destroy(self.session_uuid, ref_network)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref_vm
        else:
            print res
    def create_external_network(self, name, desc, auto, pif, vlan):
        network_cfg = {
               'uuid': '',
               'name_label': name,
               'name_description': desc, 
               'VIFs': [],
               'PIFs': [],
               'other_config': {},
               'bridge': '',
               'blobs': {}
           }
        if auto:
            network_cfg['other_config']['automatic'] = "true"
        else:
            network_cfg['other_config']['automatic'] = "false"

        network = None
        res = self.connection.network.create(self.session_uuid, network_cfg) 
        if "Value" in res:
            network = res['Value']
        else:
            print res
        if network:
            res = self.connection.pool.create_VLAN_from_PIF(self.session_uuid, pif, network, str(vlan)) 
            if "Value" not in res:
                print res
    def create_internal_network(self, name, desc, auto):
        network_cfg = {
               'uuid': '',
               'name_label': name,
               'name_description': desc, 
               'VIFs': [],
               'PIFs': [],
               'other_config': {},
               'bridge': '',
               'blobs': {}
           }
        if auto:
            network_cfg['other_config']['automatic'] = "true"
        else:
            network_cfg['other_config']['automatic'] = "false"

        res = self.connection.network.create(self.session_uuid, network_cfg) 
        if "Value" in res:
            print res
    def is_vlan_available(self, data):
        for pif_key in self.all_pif:
            if int(self.all_pif[pif_key]['VLAN']) == int(data):
                return False
        return True

