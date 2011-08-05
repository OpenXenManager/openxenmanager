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
import xml.sax.saxutils as saxutils

class oxcSERVERstorage:
    stg_ref = None
    stg_uuid = None
    def fill_hw_hba(self, ref, list):
       #<?xml version="1.0"?><methodCall><methodName>SR.probe</methodName><params><param><value><string>OpaqueRef:c9ea013c-cbce-0e85-6863-66d8e7b66ea7</string></value></param><param><value><string>OpaqueRef:5c0a69d1-7719-946b-7f3c-683a7058338d</string></value></param><param><value><struct /></value></param><param><value><string>lvmohba</string></value></param><param><value><struct /></value></param></params></methodCall>
       list.clear()
       res = self.connection.SR.probe(self.session_uuid, ref, {}, "lvmohba", {})
       if len(res['ErrorDescription']) > 2:
           result = res['ErrorDescription'][3]
           dom = xml.dom.minidom.parseString(result)
           nodes = dom.getElementsByTagName("BlockDevice")
           disks = {}
           for node in nodes:
               size = self.convert_bytes(node.getElementsByTagName("size")[0].childNodes[0].data.strip())
               serial = node.getElementsByTagName("serial")[0].childNodes[0].data.strip()
               scsiid = node.getElementsByTagName("SCSIid")[0].childNodes[0].data.strip()
               adapter = node.getElementsByTagName("adapter")[0].childNodes[0].data.strip()
               channel = node.getElementsByTagName("channel")[0].childNodes[0].data.strip()
               id = node.getElementsByTagName("id")[0].childNodes[0].data.strip()
               lun = node.getElementsByTagName("lun")[0].childNodes[0].data.strip()
               vendor = node.getElementsByTagName("vendor")[0].childNodes[0].data.strip()
               path = node.getElementsByTagName("path")[0].childNodes[0].data.strip()
               if vendor not in disks:
                   disks[vendor] = []
               disks[vendor].append(["  %s %s %s %s:%s:%s:%s" % (size, serial, scsiid, adapter, channel, id, lun),scsiid,path])
           for ref in disks.keys():
               list.append(["<b>" + ref + "</b>", False, "", ""])
               for lun in disks[ref]:
                   list.append([lun[0], True, lun[1], lun[2]])
           return 0
       else:
           self.wine.show_error_dlg("No LUNs were found. Please verify your hardware configuration")
           return 1

    def rescan_isos(self, ref):
        res = self.connection.Async.SR.scan(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def detach_storage(self, ref):
        for pbd in self.all_storage[ref]['PBDs']:
            res = self.connection.Async.PBD.unplug(self.session_uuid, pbd)
            if "Value" in res:
                self.track_tasks[res['Value']] = ref
            else:
                print res
            if "Value" in res:
                value = res["Value"]
                task = self.connection.task.get_record(self.session_uuid, value)['Value']
                while task["status"] == "pending":
                    task = self.connection.task.get_record(self.session_uuid, value)['Value']
                res = self.connection.PBD.destroy(self.session_uuid, pbd)
                if "Value" in res:
                    self.track_tasks[res['Value']] = ref
                else:
                    print res
    def forget_storage(self, ref):
        if self.all_storage[ref]['allowed_operations'].count("unplug"):
            for pbd in self.all_storage[ref]['PBDs']:
                res = self.connection.Async.PBD.unplug(self.session_uuid, pbd)
                if "Value" in res:
                    self.track_tasks[res['Value']] = ref
                    value = res["Value"]
                    task = self.connection.task.get_record(self.session_uuid, value)['Value']
                    while task["status"] == "pending":
                        task = self.connection.task.get_record(self.session_uuid, value)['Value']
                    res = self.connection.Async.PBD.destroy(self.session_uuid, pbd)
                    if "Value" in res:
                        self.track_tasks[res['Value']] = ref
                        value = res["Value"]
                        task = self.connection.task.get_record(self.session_uuid, value)['Value']
                        while task["status"] == "pending":
                            task = self.connection.task.get_record(self.session_uuid, value)['Value']
                    else:
                        print res
                else:
                    print res
        res = self.connection.Async.SR.forget(self.session_uuid, ref)         
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def delete_vdi(self, ref_vdi, ref_vm):
        for ref_vbd in self.all_vdi[ref_vdi]['VBDs']:
            res = self.connection.VBD.destroy(self.session_uuid, ref_vbd)
            if "Value" in res:
                self.track_tasks[res['Value']] = ref_vm
            else:
                print res
        res = self.connection.VDI.destroy(self.session_uuid, ref_vdi)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref_vm
        else:
            print res
    def reattach_nfs_iso(self, sr, name, share, options):
        # FIXME
        ref = self.all_hosts.keys()[0]
        pbd = {
                "uuid" : "",
                "host" : ref,
                "SR" : sr,
                "device_config" : {
                        "location" : share,
                        "options": options
                },
                "currentyle_attached" : False,
                "other_config" : {}
            }
        self.connection.SR.set_name_label(self.session_uuid, sr, name)
        self.connection.SR.set_name_description(self.session_uuid, sr,  "NFS ISO Library [%s]" % (share))
        res = self.connection.Async.PBD.create(self.session_uuid, pbd)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
            value = res['Value']
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
            while task["status"] == "pending":
                task = self.connection.task.get_record(self.session_uuid, value)['Value']
            result =  saxutils.unescape(task['result']).replace("<value>","").replace("</value>","").replace("&quot;", '"')
            res = self.connection.Async.PBD.plug(self.session_uuid, result)
            value = res['Value']
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
            while task["status"] == "pending":
                task = self.connection.task.get_record(self.session_uuid, value)['Value']
            if task["status"] == "success": 
                return 0
            else:
                self.wine.show_error_dlg(str(task["error_info"]))
                return 1
        else:
            print res

    def create_nfs_iso(self, ref, name, share, options):
        sr = {
                "location" : share,
                "options" : options
        }
        value = self.connection.SR.create(self.session_uuid, ref, sr, "0", name, "NFS ISO Library [%s]" % (share), "iso", "iso", True, {})
        if "ErrorDescription" in value:
            self.wine.show_error_dlg(value["ErrorDescription"][2])
            return 1
        else:
            return 0
    def reattach_cifs_iso(self, sr, name, share, options, user="", password=""):
        ref = self.all_hosts.keys()[0]
        pbd = {
                "uuid" : "",
                "host" : ref,
                "SR" : sr,
                "device_config" : {
                        "location" : share,
                        "type": "cifs",
                        "options": options
                },
                "currentyle_attached" : False,
                "other_config" : {}
            }
        self.connection.SR.set_name_label(self.session_uuid, sr, name)
        self.connection.SR.set_name_description(self.session_uuid, sr,  "CIFS ISO Library [%s]" % (share))
        res = self.connection.Async.PBD.create(self.session_uuid, pbd)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
            value = res['Value']
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
            while task["status"] == "pending":
                task = self.connection.task.get_record(self.session_uuid, value)['Value']
            result =  saxutils.unescape(task['result']).replace("<value>","").replace("</value>","").replace("&quot;", '"')
            res = self.connection.Async.PBD.plug(self.session_uuid, result)
            value = res['Value']
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
            while task["status"] == "pending":
                task = self.connection.task.get_record(self.session_uuid, value)['Value']
            if task["status"] == "success": 
                return 0
            else:
                self.wine.show_error_dlg(str(task["error_info"]))
                return 1
        else:
            print res

    def create_cifs_iso(self, ref, name, share, options, user="", password=""):
        sr = {
            "location" : share,
            "type" : "cifs",
            "options" : options,
            "username" : user,
            "cifspassword" : password,
        }
        value = self.connection.SR.create(self.session_uuid, ref, sr, "0", name, "CIFS ISO Library [%s]" % (share), "iso", "iso", True, {})
        if "ErrorDescription" in value:
            self.wine.show_error_dlg(value["ErrorDescription"][2])
            return 1
        else:
            return 0

    def create_nfs_vhd(self, ref, name, host, path, options, create=None):
        sr = {
            "serverpath" : path,
            "server" : host,
            "options" : options
        }
        res = self.connection.SR.create(self.session_uuid, ref, sr, str(0), name, "NF SR [%s:%s]" % (host, path), "nfs", "", True, {})
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def create_aoe(self, ref, name, path, create=None):
        sr = {
            "device" : path,
        }
        res = self.connection.SR.create(self.session_uuid, ref, sr, str(0), name, "AoE SR [%s]" % (path), "lvm", "", True, {})
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def reattach_aoe(self, ref, name, path, create, uuid):
        sr = self.connection.SR.get_by_uuid(self.session_uuid, uuid)
        sr = self.connection.SR.introduce(self.session_uuid, uuid, name, "AOE SR [%s]" % (path), "lvm", "", True, {})['Value']
        pbd = {
                "uuid" : "",
                "host" : ref,
                "SR" : sr,
                "device_config" : {
                        "device" : path,
                },
                "currently_attached" : False,
                "other_config" : {}
            }
        ref = self.connection.PBD.create(self.session_uuid, pbd)['Value']
        self.connection.PBD.plug(self.session_uuid, ref)

    def reattach_nfs_vhd(self, ref, name, host, path, options, create, uuid):
        sr = self.connection.SR.get_by_uuid(self.session_uuid, uuid)
        sr = self.connection.SR.introduce(self.session_uuid, uuid, name, "NFS SR [%s:%s]" % (host, path), "nfs", "", True, {})['Value']
        pbd = {
                "uuid" : "",
                "host" : ref,
                "SR" : sr,
                "device_config" : {
                        "serverpath" : path,
                        "server" : host,
                        "options": options
                },
                "currently_attached" : False,
                "other_config" : {}
            }
        ref = self.connection.PBD.create(self.session_uuid, pbd)['Value']
        self.connection.PBD.plug(self.session_uuid, ref)

    def format_hardware_hba(self, ref, uuid, name, path): 
       sr = {
        "SCSIid" : uuid,

       }
       res = self.connection.SR.create(self.session_uuid, ref, sr, "0", name, "Hardware HBA SR [%s]" % (path), "lvmohba", "", False, {})
       if "Value" in res:
           self.track_tasks[res['Value']] =  self.host_vm[ref][0]
           print self.connection.SR.set_other_config(self.session_uuid, res['Value'], {"auto-scan": "false"})
       else:
           print res

    def reattach_and_introduce_hardware_hba(self, ref, uuid, name, path): 
       res = self.connection.SR.introduce(self.session_uuid, self.stg_uuid, name, "Hardware HBA SR [%s]" % (path), "lvmohba", "", False, {})
       pbd = {
               "uuid" : "",
               "host" : ref,
               "SR" : res['Value'],
               "device_config" : {
                       "SCSIid" : uuid,
               },
               "currentyle_attached" : False,
               "other_config" : {}
           }
 
       res = self.connection.Async.PBD.create(self.session_uuid, pbd)
       if "Value" in res:
           self.track_tasks[res['Value']] =  self.host_vm[ref][0]
           value = res['Value']
           task = self.connection.task.get_record(self.session_uuid, value)['Value']
           while task["status"] == "pending":
               task = self.connection.task.get_record(self.session_uuid, value)['Value']
           result =  saxutils.unescape(task['result']).replace("<value>","").replace("</value>","").replace("&quot;", '"')
           res = self.connection.Async.PBD.plug(self.session_uuid, result)
           value = res['Value']
           task = self.connection.task.get_record(self.session_uuid, value)['Value']
           while task["status"] == "pending":
               task = self.connection.task.get_record(self.session_uuid, value)['Value']
           if task["status"] == "success": 
               return 0
           else:
               self.wine.show_error_dlg(str(task["error_info"]))
               return 1
       else:
           print res
      
    def reattach_hardware_hba(self, ref, uuid, name, path): 
       ref = self.all_hosts.keys()[0]
       pbd = {
               "uuid" : "",
               "host" : ref,
               "SR" : self.stg_ref,
               "device_config" : {
                       "SCSIid" : uuid,
               },
               "currentyle_attached" : False,
               "other_config" : {}
           }
       self.connection.SR.set_name_label(self.session_uuid, self.stg_ref, name)
       self.connection.SR.set_name_description(self.session_uuid, self.stg_ref,  "Hardware HBA SR [%s]" % (path))
       res = self.connection.Async.PBD.create(self.session_uuid, pbd)
       if "Value" in res:
           self.track_tasks[res['Value']] =  self.host_vm[ref][0]
           value = res['Value']
           task = self.connection.task.get_record(self.session_uuid, value)['Value']
           while task["status"] == "pending":
               task = self.connection.task.get_record(self.session_uuid, value)['Value']
           result =  saxutils.unescape(task['result']).replace("<value>","").replace("</value>","").replace("&quot;", '"')
           res = self.connection.Async.PBD.plug(self.session_uuid, result)
           value = res['Value']
           task = self.connection.task.get_record(self.session_uuid, value)['Value']
           while task["status"] == "pending":
               task = self.connection.task.get_record(self.session_uuid, value)['Value']
           if task["status"] == "success": 
               return 0
           else:
               self.wine.show_error_dlg(str(task["error_info"]))
               return 1
       else:
           print res

       pass
       """
       sr = {
        "SCSIid" : uuid,

       }
       res = self.connection.SR.create(self.session_uuid, ref, sr, "0", name, "Hardware HBA SR [IBM - %s]" % (path), "lvmohba", "", False, {})
       if "Value" in res:
           self.track_tasks[res['Value']] =  self.host_vm[ref][0]
           print self.connection.SR.set_other_config(self.session_uuid, res['Value'], {"auto-scan": "false"})
       else:
           print res
       """
    def check_hardware_hba(self, ref, uuid, text): 
       result = self.connection.SR.probe(self.session_uuid, ref, {"SCSIid" : uuid }, "lvmohba", {})['Value']
       dom = xml.dom.minidom.parseString(result)
       nodes = dom.getElementsByTagName("UUID")
       if len(nodes):
           reattach = True
           self.stg_uuid = nodes[0].childNodes[0].data.strip()
           for storage_ref in self.all_storage.keys():
               storage = self.all_storage[storage_ref]
               if storage["uuid"] == self.stg_uuid:
                   self.stg_ref = storage_ref
                   if len(storage['PBDs']):
                       reattach = False
           if reattach:
               if self.stg_ref:
                   return [2, self.all_storage[self.stg_ref]['name_label'], self.all_hosts[ref]['name_label']]
               else:
                   return [3, text, self.all_hosts[ref]['name_label']]
           else:
               return [1, self.all_storage[self.stg_ref]['name_label'], self.all_hosts[ref]['name_label']]
       else:
           return [0, None, None]

    def check_iscsi(self, ref, name, host, port, scsiid, targetiqn, user, password):
        sr = {
            "port" : port,
            "target" : host,
            "SCSIid" : scsiid,
            "targetIQN" : targetiqn
        }
        if user:
            sr["chapuser"] = user
        if password:
            sr["chappassword"] = password
        value = self.connection.Async.SR.probe(self.session_uuid, ref, sr, "lvmoiscsi", {})['Value']
        task = self.connection.task.get_record(self.session_uuid, value)['Value']
        while task["status"] == "pending":
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
        result =  saxutils.unescape(task['result']).replace("<value>","").replace("</value>","").replace("&quot;", '"')
        print result
        dom = xml.dom.minidom.parseString(result)
        nodes = dom.getElementsByTagName("UUID")
        if len(nodes):
            return nodes[0].childNodes[0].data.strip()
        else:
            return None
        #ref = self.connection.SR.create(self.session_uuid, ref, sr, "0", name, "iSCSI SR [%s (%s)]" % (host, targetiqn), "lvmoiscsi", "", True, {})
        #print ref
    def create_iscsi(self, ref, name, host, port, scsiid, targetiqn, user, password):
        sr = {
            "port" : port,
            "target" : host,
            "SCSIid" : scsiid,
            "targetIQN" : targetiqn
        }
        if user:
            sr["chapuser"] = user
        if password:
            sr["chappassword"] = password
        res = self.connection.Async.SR.create(self.session_uuid, ref, sr, "0", name, "iSCSI SR [%s (%s)]" % (host, targetiqn), "lvmoiscsi", "", True, {})
     
    def reattach_iscsi(self, ref, name, host, port, scsiid, targetiqn, user, password, lun):
        res = self.connection.SR.introduce(self.session_uuid, lun, name,  "iSCSI SR [%s (%s)]" % (host, targetiqn), "lvmoiscsi", "", True, {})
        print res
        pbd = {
                "uuid" : "",
                "host" : ref,
                "SR" : res['Value'],
                "device_config" : {
                        "port" : port,
                        "target" : host,
                        "SCSIid" : scsiid,
                        "targetIQN" : targetiqn
                    },
                "currently_attached" : False,
                "other_config" : {}
            }
        if user:
            pbd["device_config"]["chapuser"] = user
        if password:
            pbd["device_config"]["chappassword"] = password

        res = self.connection.PBD.create(self.session_uuid, pbd)
        print res
        print self.connection.Async.PBD.plug(self.session_uuid, res['Value'])
        """
        sr = {
            "port" : port,
            "target" : host,
            "SCSIid" : scsiid,
            "targetIQN" : targetiqn
        }
        if user:
            sr["chapuser"] = user
        if password:
            sr["chappassword"] = password
        res = self.connection.Async.SR.create(self.session_uuid, ref, sr, "0", name, "iSCSI SR [%s (%s)]" % (host, targetiqn), "lvmoiscsi", "", True, {})
        """

    def scan_aoe(self, ref, lista, path):
        sr = {
            "device" : path,
        }
        value = self.connection.Async.SR.probe(self.session_uuid, ref, sr, "lvm", {})['Value']
        task = self.connection.task.get_record(self.session_uuid, value)['Value']
        while task["status"] == "pending":
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
        print task
        if task['result'].count("<value>"):
            result =  saxutils.unescape(task['result']).replace("<value>","").replace("</value>","").replace("&quot;", '"')
            dom = xml.dom.minidom.parseString(result)
            nodes = dom.getElementsByTagName("SRlist")
            if len(nodes[0].childNodes):
                for i in range(1,len(nodes[0].childNodes),2):
                     ref = nodes[0].childNodes[i].childNodes[1].childNodes[0].data.strip()
                     print ref
                     print self.search_storage_uuid(ref)
                     if self.search_storage_uuid(ref) == False: 
                         lista.append([ref, ref])
            if lista.__len__() > 0:
                return 2
            else:
                return 1
        else:
            if len(task["error_info"]) > 2:
                self.wine.show_error_dlg(task["error_info"][2])
            else:
                self.wine.show_error_dlg(task["error_info"][1])
            self.connection.task.destroy(self.session_uuid, value)
            return 0

    def scan_nfs_vhd(self, ref, list, host, path, options):
        sr = {
            "serverpath" : path,
            "server" : host,
            "options" : options,
        }
        value = self.connection.Async.SR.probe(self.session_uuid, ref, sr, "nfs", {})['Value']
        task = self.connection.task.get_record(self.session_uuid, value)['Value']
        while task["status"] == "pending":
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
        if task['result'].count("<value>"):
            result =  saxutils.unescape(task['result']).replace("<value>","").replace("</value>","").replace("&quot;", '"')
            dom = xml.dom.minidom.parseString(result)
            nodes = dom.getElementsByTagName("SRlist")
            if len(nodes[0].childNodes):
                for i in range(1,len(nodes[0].childNodes),2):
                     ref = nodes[0].childNodes[i].childNodes[1].childNodes[0].data.strip()
                     if self.search_storage_uuid(ref) == False: 
                         list.append([ref, ref])
            if list.__len__() > 0:
                return 2
            else:
                return 1
        else:
            self.wine.show_error_dlg(task["error_info"][2])
            self.connection.task.destroy(self.session_uuid, value)
            return 0
    def search_storage_uuid(self, uuid):
        """
        Function to search a storage with specify uuid, returns True if found
        """
        for stg in self.all_storage.keys():
            if self.all_storage[stg]["uuid"] == uuid:
                return True
        return False
    def fill_iscsi_target_iqn(self, ref, list, target, port, user=None, password=None):
        list.clear()
        sr = {
            "port" : port,
            "target": target,
            }
        if user:
            sr["chapuser"] = user
        if password:
            sr["chappassword"] = password
        value = self.connection.Async.SR.create(self.session_uuid, ref, sr, "0", "__gui__", "SHOULD NEVER BE CREATED","lvmoiscsi","user", True, {})['Value']
        task = self.connection.task.get_record(self.session_uuid, value)['Value']
        while task["status"] == "pending":
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
        if task["error_info"][3]:
            dom = xml.dom.minidom.parseString(task["error_info"][3])
            nodes = dom.getElementsByTagName("TGT")
            ix = 1
            for i in range(0, len(nodes)):
                index = nodes[i].childNodes[1].childNodes[0].data.strip()
                ip = nodes[i].childNodes[3].childNodes[0].data.strip()
                target = nodes[i].childNodes[5].childNodes[0].data.strip()
                list.append([target, "%s (%s)" % (target, ip)])
            self.connection.task.destroy(self.session_uuid, value) 
            return True
        else:
            self.wine.show_error_dlg(task["error_info"][2])
            self.connection.task.destroy(self.session_uuid, value) 
            return False
    def fill_iscsi_target_lun(self, ref, list, target, targetiqn, port, user=None, password=None):
        list.clear()
        sr = {
            "port" : port,
            "target": target,
            }
        # chapuser
        # chappassword
        if user:
            sr["chapuser"] = user
        if password:
            sr["chappassword"] = password

        sr["targetIQN"] = targetiqn
        value = self.connection.Async.SR.create(self.session_uuid, ref, sr, "0", "__gui__", "SHOULD NEVER BE CREATED","lvmoiscsi","user", True, {})['Value']
        task = self.connection.task.get_record(self.session_uuid, value)['Value']
        while task["status"] == "pending":
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
        if task["error_info"][3]:
            dom = xml.dom.minidom.parseString(task["error_info"][3])
            nodes = dom.getElementsByTagName("LUN")
            for i in range(0, len(nodes)):
                vendor = nodes[i].getElementsByTagName("vendor")[0].childNodes[0].data.strip()
                #serial =  nodes[i].getElementsByTagName("serial")[0].childNodes[0].data.strip()
                lunid =  nodes[i].getElementsByTagName("LUNid")[0].childNodes[0].data.strip()
                size = nodes[i].getElementsByTagName("size")[0].childNodes[0].data.strip()
                scsiid =  nodes[i].getElementsByTagName("SCSIid")[0].childNodes[0].data.strip()
                list.append([scsiid, "LUN %s: %s (%s)" % (lunid, self.convert_bytes(size), vendor)])
            self.connection.task.destroy(self.session_uuid, value) 
            return True
        else:
            self.wine.show_error_dlg(task["error_info"][2])
            self.connection.task.destroy(self.session_uuid, value) 
            return False
