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

class oxcSERVERvmstorage:
    def vm_storagedetach(self, ref):
        print self.connection.VBD.destroy(self.session_uuid, ref) 

    def vm_storageplug(self, ref):
        print self.connection.VBD.plug(self.session_uuid, ref) 

    def vm_storageunplug(self, ref):
        print self.connection.VBD.unplug(self.session_uuid, ref) 

    def set_vm_dvd(self, vm, vdi):
        if vdi:
            cd = None 
            if self.get_vm_dvd_ref(vm) and self.all_vbd[self.get_vm_dvd_ref(vm)]['allowed_operations'].count("eject"):
                res =  self.connection.Async.VBD.eject(self.session_uuid, self.get_vm_dvd_ref(vm))
                self.track_tasks[res['Value']] = vm
            if vdi != "empty":
                res = self.connection.Async.VBD.insert(self.session_uuid, self.get_vm_dvd_ref(vm), vdi)
                self.track_tasks[res['Value']] = vm

    def add_disk_to_vm(self, name, description, sr, virtual_size, vmuuid, vm_ref):
       vdi_cfg = {
            'name_label': name,
            'name_description': description, 
            'SR': sr,
            'virtual_size': str(virtual_size),
            'type': "user",
            'sharable': False,
            'read_only': False,
            'other_config': {},
            'xenstore_data': {},
            'smconfig': {"vmhint" : vmuuid }
       }
       vdi = self.connection.VDI.create(self.session_uuid, vdi_cfg)
       if vm_ref:
           userdevice = self.connection.VM.get_allowed_VBD_devices(self.session_uuid, vm_ref)['Value'][0]
           vbd_cfg = {
                'VM': vm_ref, 
                'VDI': vdi['Value'],
                'userdevice': userdevice,
                'bootable': False,
                'mode': "RW",
                'type': "Disk",
                'unplugabble': "0",
                'storage_lock': "0",
                'empty': False,
                'currently_attached': "0",
                'status_code': "0",
                'other_config': {},
                'qos_algorithm_type': "",
                'qos_algorithm_params': {}
           }
           res = self.connection.VBD.create(self.session_uuid, vbd_cfg)
           if "Value" in res:
                self.track_tasks[res['Value']] = vm_ref 
           else:
                print res
           res = self.connection.Async.VBD.plug(self.session_uuid, res['Value'])
           if "Value" in res:
                self.track_tasks[res['Value']] = vm_ref 
           else:
                print res  
    def fill_vm_storageattach(self, list):
        list.clear() 
        refattachdisk = {}                                
        all_sr = self.connection.SR.get_all_records\
                  (self.session_uuid)['Value']
       
        for sr in all_sr:
            if all_sr[sr]['type'] != "iso" and all_sr[sr]['content_type'] != "iso":
                refattachdisk[sr] = list.append(None, [gtk.gdk.pixbuf_new_from_file("images/storage_default_16.png"), sr, all_sr[sr]["name_label"],"", False])   

        all_vdi= self.connection.VDI.get_all_records\
                  (self.session_uuid)['Value']
        for vdi in all_vdi:
            if not all_vdi[vdi]['VBDs'] and all_vdi[vdi]['read_only'] == False:
                 list.append(refattachdisk[all_vdi[vdi]['SR']], [gtk.gdk.pixbuf_new_from_file("images/user_template_16.png"), vdi, all_vdi[vdi]['name_label'], all_vdi[vdi]['name_description'] + " - " +  self.convert_bytes(all_vdi[vdi]['physical_utilisation']) + " used out of " + self.convert_bytes(all_vdi[vdi]['virtual_size']),True])

    def attach_disk_to_vm(self, ref, vdi, ro):
        userdevice = self.connection.VM.get_allowed_VBD_devices(self.session_uuid, ref)['Value'][0]
        vbd_cfg = {
            'VM': ref,
            'VDI': vdi,
            'userdevice': userdevice,
            'bootable': False,
            'mode': "RW",
            'type': "Disk",
            'unplugabble': "0",
            'storage_lock': "0",
            'empty': False,
            'currently_attached': "0",
            'status_code': "0",
            'other_config': {},
            'qos_algorithm_type': "",
            'qos_algorithm_params': {}
        }
        if ro == True:
            vbd_cfg["mode"] = "RO"

        res = self.connection.VBD.create(self.session_uuid, vbd_cfg)
        if "Value" in res:
            res = self.connection.Async.VBD.plug(self.session_uuid, res["Value"])
            if "Value" in res:
                self.track_tasks[res['Value']] = ref 

    def install_xenserver_tools(self, vm):
        vdi = self.get_xs_tools_ref() 
        if self.get_vm_dvd_ref(vm) and self.all_vbd[self.get_vm_dvd_ref(vm)]['allowed_operations'].count("eject"):
            res =  self.connection.Async.VBD.eject(self.session_uuid, self.get_vm_dvd_ref(vm))
            self.track_tasks[res['Value']] = vm
        if vdi != "empty":
            res = self.connection.Async.VBD.insert(self.session_uuid, self.get_vm_dvd_ref(vm), vdi)
            self.track_tasks[res['Value']] = vm

    def get_xs_tools_ref(self):
       for vdi in self.all_vdi:
           if "sm_config" in self.all_vdi[vdi] and "xs-tools" in self.all_vdi[vdi]["sm_config"] \
            and self.all_vdi[vdi]["sm_config"]["xs-tools"] == "true":
                return vdi

    def get_vm_dvd_ref(self, vm):
        for vbd in self.all_vbd.keys():
            if self.all_vbd[vbd]["VM"] == vm: 
                if (self.all_vbd[vbd]['type'] == "CD" or self.all_vbd[vbd]['type'] == "udev"):
                    print self.all_vbd[vbd]['type']
                    return vbd

        #FIXME: auto add VBD to CD, do 'click here to add CD'
        userdevice = self.connection.VM.get_allowed_VBD_devices(self.session_uuid, vm)['Value'][0]

        vbd_cfg = {
            'uuid': "",
            'allowed_operations': [],
            'current_operations': {},
            'VM': vm,
            'VDI': "",
            'device': "",
            'userdevice': userdevice,
            'bootable': False,
            'mode': "RO",
            'type': "CD",
            'unplugabble': "0",
            'storage_lock': "0",
            'empty': True,
            'other_config': {},
            'currently_attached': "0",
            'status_code': "0",
            'status_detail': "",
            'runtime_properties': "",
            'qos_algorithm_type': "",
            'qos_algorithm_params': {},
            'metrics': ""
        }
        res = self.connection.VBD.create(self.session_uuid, vbd_cfg) 
        if "Value" in res:
            self.track_tasks[res['Value']] = vm
            self.all_vbd[res['Value']] = self.connection.VBD.get_record(self.session_uuid, res['Value'])['Value']
        else:
            print res
        return res['Value']
