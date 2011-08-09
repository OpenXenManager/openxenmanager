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
import os
import platform
import sys, shutil
import datetime
import xml.dom.minidom 
import pdb
import rrdinfo
import time
import put
import gobject
from rrd import RRD, XPORT
import xml.sax.saxutils as saxutils
import traceback

from threading import Thread
from configobj import ConfigObj
from operator import itemgetter
from pygtk_chart import line_chart
from messages import messages, messages_header

from oxcSERVER_vm import *
from oxcSERVER_host import *
from oxcSERVER_properties import *
from oxcSERVER_storage import *
from oxcSERVER_alerts import *
from oxcSERVER_addserver import *
from oxcSERVER_newvm import *
from oxcSERVER_menuitem import *
from capabilities import capabilities_text

class oxcSERVER(oxcSERVERvm,oxcSERVERhost,oxcSERVERproperties,oxcSERVERstorage,oxcSERVERalerts,oxcSERVERaddserver,oxcSERVERnewvm,oxcSERVERmenuitem):
    session_uuid = None
    is_connected = False 
    host_vm = {}
    set_descriptions = {}
    halt = False
    halt_search = False
    halt_import = False
    track_tasks = {}
    tasks = {}
    vboxchildcancel = {}
    vboxchildprogressbar = {}
    vboxchildprogress = {}
    autostart = {}
    vif_plug = []
    flag_vif_plug = False
    found_iter = ""
    import_ref = None
    import_start = False
    import_make_into_template = False
    poolroot = None
    hostroot = {}
    last_storage_iter = None
    pbdcreate = []
    
    def __init__(self, host, user, password, wine, ssl = False):
        super(oxcSERVER, self).__init__()
        self.host = host
        self.hostname = host
        self.wine = wine
        self.user = user
        self.password = password
        self.ssl = ssl 
        
    def logout(self):
        self.halt_search = True
        self.halt = True
        if self.is_connected:
            self.connection.event.unregister(self.session_uuid, ["*"])
            self.connection.session.logout(self.session_uuid) 
            self.is_connected = False

    def get_network_relation(self, ref, show_halted_vms):
        # Get network -> VM relation
        relation = {}
        for network in self.all_network:
            network_name = self.all_network[network]['name_label'].replace('Pool-wide network associated with eth','Network ')
            vms = []
            for vif in self.all_network[network]['VIFs']:
                vm = self.all_vif[vif]['VM']
                if not vms.count(vm + "_" +  self.all_vms[vm]['name_label']):
                    if show_halted_vms or  self.all_vms[vm]['power_state'] == "Running":
                        vms.append(vm + "_" +  self.all_vms[vm]['name_label'])
            relation[network + "_" + network_name] = vms

        return relation

    def get_storage_relation(self, ref, show_halted_vms):
        # Get network -> VM relation
        relation = {}
        for storage in self.all_storage:
            storage_name = self.all_storage[storage]['name_label']
            vms = []
            for vdi in self.all_storage[storage]['VDIs']:
                vbds = self.all_vdi[vdi]['VBDs']
                for vbd in vbds:
                    vm = self.all_vbd[vbd]['VM']
                    if not vms.count(vm + "_" +  self.all_vms[vm]['name_label']):
                        if show_halted_vms or  self.all_vms[vm]['power_state'] == "Running":
                            vms.append(vm + "_" +  self.all_vms[vm]['name_label'])
            relation[storage+ "_" + storage_name] = vms

        return relation

    def prueba(self):
        print self.session_uuid
        task_uuid = self.connection.task.create(self.session_uuid, "Restore2", "Restoring2 ")
        print task_uuid
        time.sleep(300)
        print task_uuid
        return
        networks = self.connection.network.get_all_records(self.session_uuid)['Value']
        for network in networks:
            print networks[network]['name_label']
            vms = []
            for vif in networks[network]['VIFs']:
                vms.append(self.connection.VIF.get_record(self.session_uuid, vif)['Value']['VM'])
            # Remove duplicates
            set = {}
            map(set.__setitem__, vms, [])
            for vm in set.keys():
                print "\t" + self.connection.VM.get_record(self.session_uuid, vm)['Value']['name_label']

        storages = self.connection.SR.get_all_records(self.session_uuid)['Value']
        for storage in storages:
            vms = []
            print storages[storage]['name_label']
            for vdi in storages[storage]['VDIs']:
                vbds = self.connection.VDI.get_record(self.session_uuid, vdi)['Value']['VBDs']
                for vbd in vbds:
                    vms.append(self.connection.VBD.get_record(self.session_uuid, vbd)['Value']['VM'])
            set = {}
            map(set.__setitem__, vms, [])
            for vm in set.keys():
                print "\t" + self.connection.VM.get_record(self.session_uuid, vm)['Value']['name_label']

        """
        print self.connection.Async.pool_patch.apply(self.session_uuid, "OpaqueRef:772a39ac-e9be-1b14-2b20-ded03b95b20b", "OpaqueRef:be650e6f-8e2f-d937-c525-15fd57568bac")
        result = self.connection.host.get_system_status_capabilities(self.session_uuid, "OpaqueRef:480dede4-930b-1b5c-54a8-73d38fa56d3a")['Value']
        privacy = {"yes": "1", "maybe": "2", "if_customized": "3", "no": "4"}
        dom = xml.dom.minidom.parseString(result)
        nodes = dom.getElementsByTagName("capability")
        capabilities = {}
        for node in nodes:
           attr = node.attributes
           key, checked, pii, minsize, maxsize, mintime, maxtime = [attr.getNamedItem(k).value for k \
                   in ["key", "default-checked", "pii", "min-size", "max-size", "min-time", "max-time"]]
           capabilities[privacy[pii] + "_" + key] = [checked, minsize, maxsize, mintime, maxtime]
        totalsize = 0
        totaltime = 0
        for key in sorted(capabilities.keys()):
           if key.split("_",2)[1] in capabilities_text:
               print capabilities_text[key.split("_",2)[1]]
               checked, minsize, maxsize, mintime, maxtime = [value for value in capabilities[key]]
               if minsize == maxsize:
                  if maxsize != "-1": 
                      totalsize += int(maxsize)
                  size = self.convert_bytes(maxsize)
               elif minsize == "-1":
                  totalsize += int(maxsize)
                  size = "< %s" % self.convert_bytes(maxsize)
               else:
                  totalsize += int(maxsize)
                  size = "%s-%s" % (self.convert_bytes(minsize), self.convert_bytes(maxsize))

               if mintime == maxtime:
                  if maxtime == "-1":
                      time = "Negligible"
                  else:
                      totaltime += int(maxtime)
                      time = maxtime
               elif mintime == "-1":
                  totaltime += int(maxtime)
                  time= "< %s" % maxtime
               else:
                  totaltime += int(maxtime)
                  time= "%s-%s" % (mintime, maxtime)

               print "\tChecked: %s\n\tSize: %s\n\tTime: %s seconds\n" % (checked, size, time)
        print "Total Size: < %s Total Time: < %d minutes\n" % (self.convert_bytes(totalsize), totaltime/60)
        print self.connection.VM.get_record(self.session_uuid, "OpaqueRef:dfd4eb56-d44b-8895-328e-83a36a0807ee")
        print self.connection.VM.set_PV_kernel(self.session_uuid, "OpaqueRef:dfd4eb56-d44b-8895-328e-83a36a0807ee", "asdfasdf")
        print "https://%s/vncsnapshot?session_id=%s&ref=%s" % (self.host, self.session_uuid, "OpaqueRef:be4332e6-a8c2-eb35-6b4d-58384e1f8463")
        time.sleep(30)
        task_uuid = self.connection.task.create(self.session_uuid, "Backup database pool", "Backup database pool")
        url = "http://" + self.host + '/pool/xmldbdump?session_id=%s&task_id=%s' % (self.session_uuid, task_uuid['Value'])
        urllib.urlretrieve(url, "/tmp/backup.xml")
        import httplib, os
        filename = "/root/openxencenter/prueba.xml"
        task_uuid = self.connection.task.create(self.session_uuid, "Restore Pool database", "Restoring database pool " + filename)
        self.track_tasks[task_uuid['Value']] = "Restore.Pool"
        size=os.path.getsize(filename)
        conn = httplib.HTTPConnection("192.168.100.2", 80)
        conn.putrequest('PUT', '/pool/xmldbdump?session_id=%s&task_id=%s&dry_run=true' % (self.session_uuid, task_uuid['Value']), True, True)
        conn.putheader("Content-length:", str(size));
        conn.endheaders()
        fp=open(filename, 'r')
        total = 0
        while True:
           leido = fp.read(16384)
           total += len(leido)
           if leido:
               time.sleep(0.1)
               conn.send(leido) 
           else:
               break
        conn.close()
        fp.close()
        value = task_uuid["Value"]
        task = self.connection.task.get_record(self.session_uuid, value)['Value']
        while task["status"] == "pending":
           task = self.connection.task.get_record(self.session_uuid, value)['Value']
        print self.connection.host.get_all_records(self.session_uuid)
        print self.connection.host.dmesg(self.session_uuid, "OpaqueRef:480dede4-930b-1b5c-54a8-73d38fa56d3a")
        res = self.connection.SR.create(self.session_uuid,"OpaqueRef:5c0a69d1-7719-946b-7f3c-683a7058338d", {"SCSIid" : "3600a0b8000294d50000043454990e472" }, "0", ">Hardware HBA virtual disk storage", "Hardware HBA SR [IBM - /dev/sde]","lvmohba", "", False,{})
        if len(res['ErrorDescription']) > 2:
            print res['ErrorDescription'][2]
        #<?xml version="1.0"?><methodCall><methodName>Async.SR.probe</methodName><params><param><value><string>OpaqueRef:021466a4-68d1-8e4b-c8ee-4d40e7be1d19</string></value></param><param><value><string>OpaqueRef:5c0a69d1-7719-946b-7f3c-683a7058338d</string></value></param><param><value><struct><member><name>SCSIid</name><value><string>3600a0b8000294d50000045784b85e36f</string></value></member></struct></value></param><param><value><string>lvmohba</string></value></param><param><value><struct /></value></param></params></methodCall>
        all_storage = self.connection.SR.get_all_records(self.session_uuid)['Value']
        all_pbd = self.connection.PBD.get_all_records(self.session_uuid)['Value']
        result = self.connection.SR.probe(self.session_uuid, "OpaqueRef:5c0a69d1-7719-946b-7f3c-683a7058338d", {"SCSIid" : "3600a0b8000294d50000045784b85e36f" }, "lvmohba", {})['Value']
        dom = xml.dom.minidom.parseString(result)
        nodes = dom.getElementsByTagName("UUID")
        if len(nodes):
           reattach = True
           uuid = nodes[0].childNodes[0].data.strip()
           for storage in all_storage.values():
               if storage["uuid"] == uuid:
                   print storage
                   if len(storage['PBDs']):
                       print all_pbd[storage['PBDs'][0]]
                       reattach = False
           if reattach: 
               return 0
               print "Do you want reattach...."
           else:
               print "Please first detach...."
        else:
           print "Do you want format.."
           pass
        res = self.connection.SR.probe(self.session_uuid, "OpaqueRef:5c0a69d1-7719-946b-7f3c-683a7058338d", {}, "lvmohba", {})
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
               if vendor not in disks:
                   disks[vendor] = []
               disks[vendor].append("%s %s %s %s:%s:%s:%s" % (size, serial, scsiid, adapter, channel, id, lun))
           print disks
        else:
           print "No LUNS found"
        """
        #<?xml version="1.0"?><methodCall><methodName>Async.SR.probe</methodName>
        #<params>
        #<param><value><string>OpaqueRef:047a0487-db6d-d273-09a3-d2ac68cb0a7c</string></value></param>
        #<param><value><string>OpaqueRef:480dede4-930b-1b5c-54a8-73d38fa56d3a</string></value></param>
        #<param><value><struct>
        #    <member><name>serverpath</name><value><string>/home</string></value></member>
        #    <member><name>server</name><value><string>192.168.100.4</string></value></member>
        #    <member><name>options</name><value><string /></value></member>
        #</struct></value></param>
        #<param><value><string>nfs</string></value></param>
        #<param><value><struct /></value></param></params></methodCall>
        """
        all_vms = self.connection.VM.get_all_records(self.session_uuid)['Value']
        all_vdi = self.connection.VDI.get_all_records(self.session_uuid)['Value']
        all_vbd = self.connection.VBD.get_all_records(self.session_uuid)['Value']
        vm = "OpaqueRef:0bbb21d5-4810-2cdc-9b75-c02415de78bb"
        vm_vbd = ""
        vm_vdi = ""
        for vbd in all_vbd.keys():
            if all_vbd[vbd]["VM"] == vm and \
                    all_vbd[vbd]['type'] == "CD":
                   vm_vbd = vbd

        for vdi in all_vdi:
           if all_vdi[vdi]['location'] == "XenCenter.iso":
            vm_vdi = vdi
        print self.connection.Async.VBD.eject(self.session_uuid, vm_vbd) 
        print self.connection.VBD.insert(self.session_uuid, vm_vbd, vm_vdi)
        sr = {
        "serverpath" : "/home",
        "server" : "192.168.100.4",
        "options" : ""
        }
        value = self.connection.Async.SR.probe(self.session_uuid, "OpaqueRef:480dede4-930b-1b5c-54a8-73d38fa56d3a", sr, "nfs", {})['Value']
        task = self.connection.task.get_record(self.session_uuid, value)['Value']
        while task["status"] == "pending":
           task = self.connection.task.get_record(self.session_uuid, value)['Value']
        result =  saxutils.unescape(task['result']).replace("<value>","").replace("</value>","").replace("&quot;", '"')
        print result
        dom = xml.dom.minidom.parseString(result)
        nodes = dom.getElementsByTagName("SRlist")
        if len(nodes[0].childNodes):
            for i in range(1,len(nodes[0].childNodes),2):
                print nodes[0].childNodes[i].childNodes[1].childNodes[0].data.strip()
        self.connection.task.destroy(self.session_uuid, value)
        sr = {
           "port" : "3260",
           "target" : "192.168.100.4",
           "SCSIid" : "14945540000000000000000000100000002a00a002100a00c",
           "targetIQN" : "iqn.2001-04.com.example:storage.disk2.sys1.xyz",
        }
        value = self.connection.Async.SR.probe(self.session_uuid, "OpaqueRef:480dede4-930b-1b5c-54a8-73d38fa56d3a", sr, "lvmoiscsi",{})['Value']
        task = self.connection.task.get_record(self.session_uuid, value)['Value']
        while task["status"] == "pending":
           task = self.connection.task.get_record(self.session_uuid, value)['Value']
        print task
        self.connection.task.destroy(self.session_uuid, value)
        sr = {
            "port" : "3260",
            "target": "192.168.100.4",
            }
        # chapuser
        # chappassword
        value = self.connection.Async.SR.create(self.session_uuid, "OpaqueRef:480dede4-930b-1b5c-54a8-73d38fa56d3a", sr, "0", "__gui__", "SHOULD NEVER BE CREATED","lvmoiscsi","user", True, {})['Value']
        task = self.connection.task.get_record(self.session_uuid, value)['Value']
        while task["status"] == "pending":
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
        if task["error_info"][3]:
            dom = xml.dom.minidom.parseString(task["error_info"][3])
            nodes = dom.getElementsByTagName("TGT")
            index = nodes[0].childNodes[1].childNodes[0].data.strip()
            ip = nodes[0].childNodes[3].childNodes[0].data.strip()
            target = nodes[0].childNodes[5].childNodes[0].data.strip()
            print "%s (%s)" % (target, ip)
        else:
            print task["error_info"][2]
            self.connection.task.destroy(self.session_uuid, value)
        sr["targetIQN"] = target
        value = self.connection.Async.SR.create(self.session_uuid, "OpaqueRef:480dede4-930b-1b5c-54a8-73d38fa56d3a", sr, "0", "__gui__", "SHOULD NEVER BE CREATED","lvmoiscsi","user", True, {})['Value']
        task = self.connection.task.get_record(self.session_uuid, value)['Value']
        while task["status"] == "pending":
            task = self.connection.task.get_record(self.session_uuid, value)['Value']
        print task["error_info"][3]
        if task["error_info"][3]:
            dom = xml.dom.minidom.parseString(task["error_info"][3])
            nodes = dom.getElementsByTagName("LUN")
            vendor = nodes[0].childNodes[1].childNodes[0].data.strip()
            lunid = nodes[0].childNodes[3].childNodes[0].data.strip()
            size = nodes[0].childNodes[5].childNodes[0].data.strip()
            scsiid = nodes[0].childNodes[7].childNodes[0].data.strip()
            print "LUN %s: %s (%s)" % (lunid, self.convert_bytes(size), vendor)
        else:
            print task["error_info"][2]
            self.connection.task.destroy(self.session_uuid, value)
        """
    def export_vm(self, uuid):
        vm_uuid = self.connection.VM.get_by_uuid(self.session_uuid, uuid)['Value']
        print "GET /export?ref=%s&session_id=%s HTTP/1.1\r\n\r\n" % (vm_uuid,self.session_uuid)
    def get_seconds(self, toconvert):
        converted = datetime.datetime.strptime(str(toconvert), "%Y%m%dT%H:%M:%SZ")
        totime = time.mktime(converted.timetuple())
        #FIXME
        return totime
    def format_date(self, toconvert):
        converted = datetime.datetime.strptime(str(toconvert), "%Y%m%dT%H:%M:%SZ")
        #totime = time.mktime(converted.timetuple())
        return str(converted)
    #FIXME
    def get_seconds_difference_reverse(self, toconvert):
        converted = datetime.datetime.strptime(str(toconvert), "%Y%m%dT%H:%M:%SZ")
        totime = time.mktime(converted.timetuple())
        #FIXME
        return totime-time.time()-3600
    def get_seconds_difference(self, toconvert):
        converted = datetime.datetime.strptime(str(toconvert), "%Y%m%dT%H:%M:%SZ")
        totime = time.mktime(converted.timetuple())
        #FIXME
        return time.time()-totime-3600
    def get_dmesg(self, ref):
        return self.connection.host.dmesg(self.session_uuid, ref)["Value"]

    def restore_server(self, ref, file, name):
        import httplib
        #<?xml version="1.0"?><methodCall><methodName>task.create</methodName><params><param><value><string>OpaqueRef:149c1416-9934-3955-515a-d644aaddc38f</string></value></param><param><value><string>uploadTask</string></value></param><param><value><string>http://83.165.161.223/host_restore?session_id=OpaqueRef:149c1416-9934-3955-515a-d644aaddc38f</string></value></param></params></methodCall>
        task_uuid = self.connection.task.create(self.session_uuid, "Restoring Server", "Restoring Server %s from %s " % (name,file))
        self.track_tasks[task_uuid['Value']] = "Restore.Server"
        #size=os.stat(file)[6] 


        fp=open(file, 'rb')
        url = self.wine.selected_ip
        put.putfile(fp, 'http://' + url + '/host_restore?session_id=%s&task_id=%s&dry_run=true' % (self.session_uuid, task_uuid['Value']))
        return 
        conn = httplib.HTTP(url)
        conn.putrequest('PUT', '/host_restore?session_id=%s&task_id=%s&dry_run=true' % (self.session_uuid, task_uuid['Value']))
        conn.putheader('Content-Type', 'text/plain')
        conn.endheaders()

        blocknum=0
        uploaded=0
        blocksize=4096
        while not self.halt_import:
            bodypart=fp.read(blocksize)
            blocknum+=1
            if blocknum % 10 == 0:
                uploaded+=len(bodypart)

            if not bodypart: break
            conn.send(bodypart)

        fp.close()
    def save_screenshot(self, ref, filename):
        url = "http://" + self.wine.selected_ip + '/vncsnapshot?session_id=%s&ref=%s' % (self.session_uuid, ref)
        urllib.urlretrieve(url, filename)


    def pool_backup_database(self, ref, filename, name):
        task_uuid = self.connection.task.create(self.session_uuid, "Backup Pool database", "Backing up database pool " + name)
        self.track_tasks[task_uuid['Value']] = "Backup.Pool"
        url = "http://" + self.wine.selected_ip+ '/pool/xmldbdump?session_id=%s&task_id=%s' % (self.session_uuid, task_uuid['Value'])
        urllib.urlretrieve(url, filename)

    def pool_restore_database(self, ref, filename, name, dry_run="true"):
        import httplib
        task_uuid = self.connection.task.create(self.session_uuid, "Restore Pool database", "Restoring database pool " + filename)
        self.track_tasks[task_uuid['Value']] = "Restore.Pool"

        size=os.path.getsize(filename)
        url = self.wine.selected_ip
        fp=open(filename, 'r')
        put.putfile(fp, 'http://' + url + '/pool/xmldbdump?session_id=%s&task_id=%s&dry_run=%s' % (self.session_uuid, task_uuid['Value'], dry_run))
        return
        conn = httplib.HTTP(url)
        conn.putrequest('PUT', '/pool/xmldbdump?session_id=%s&task_id=%s&dry_run=%s' % (self.session_uuid, task_uuid['Value'], dry_run))
        conn.putheader('Content-Length', str(size))
        conn.endheaders()
        total = 0
        while True:
            leido = fp.read(16384)
            if leido:
                total += len(leido)
                time.sleep(0.1) 
                conn.send(leido) 
            else:
                break
        fp.close()
    def host_download_logs(self, ref, filename, name):
        task_uuid = self.connection.task.create(self.session_uuid, "Downloading host logs", "Downloading logs from host " + name)
        self.track_tasks[task_uuid['Value']] = "Download.Logs"
        url = "http://" + self.wine.selected_ip + '/host_logs_download?session_id=%s&sr_id=%s&task_id=%s' % (self.session_uuid, ref, task_uuid['Value'])
        urllib.urlretrieve(url, filename)

    def host_download_status_report(self, ref, refs, filename, name):
        task_uuid = self.connection.task.create(self.session_uuid, "Downloading status report", "Downloading status report from host " + name)
        self.track_tasks[task_uuid['Value']] =  self.host_vm[ref][0]
        url = "https://" + self.wine.selected_ip + '/system-status?session_id=%s&entries=%s&task_id=%s&output=tar' % (self.session_uuid, refs, task_uuid['Value'])
        urllib.urlretrieve(url, filename)

    def backup_server(self, ref, filename, name):
        task_uuid = self.connection.task.create(self.session_uuid, "Backup Server", "Backing up server " + name)
        self.track_tasks[task_uuid['Value']] = "Backup.Server"
        url = "http://" + self.wine.selected_ip + '/host_backup?session_id=%s&sr_id=%s&task_id=%s' % (self.session_uuid, ref, task_uuid['Value'])
        urllib.urlretrieve(url, filename)

    def import_vm(self, ref, filename):
        #file = "pruebadebian.xva"
        import httplib
        task_uuid = self.connection.task.create(self.session_uuid, "Importing VM", "Importing VM " + filename)
        self.track_tasks[task_uuid['Value']] = "Import.VM"

        size=os.stat(filename)[6] 
        url = self.wine.selected_ip
        fp=open(filename, 'r')
        put.putfile(fp, 'http://' + url + '/import?session_id=%s&sr_id=%s&task_id=%s' % (self.session_uuid, ref, task_uuid['Value']))
        return

        conn = httplib.HTTP(url)
        conn.putrequest('PUT', '/import?session_id=%s&sr_id=%s&task_id=%s' % (self.session_uuid, ref, task_uuid['Value']))
        conn.putheader('Content-Type', 'text/plain')
        conn.putheader('Content-Length', str(size))
        conn.endheaders()
        fp=open(file, 'rb')
        blocknum=0
        uploaded=0
        blocksize=4096
        while not self.halt_import:
            bodypart=fp.read(blocksize)
            blocknum+=1
            if blocknum % 10 == 0:
                uploaded+=len(bodypart)
            if blocknum % 1000 == 0:
                time.sleep(0.1) 

            if not bodypart: break
            conn.send(bodypart)

        fp.close()

    def add_alert(self, message, ref, list):
        if message['cls'] == "Host":
            if message['name'] in messages:
                parent = list.prepend(None, [gtk.gdk.pixbuf_new_from_file("images/info.gif"), 
                    self.hostname, messages_header[message['name']], self.format_date(str(message['timestamp'])),
                    ref, self.host])
                list.prepend(parent, [None, "", messages[message['name']] % (self.hostname), "",
                    ref, self.host])
            else:
                parent = list.prepend(None, [gtk.gdk.pixbuf_new_from_file("images/info.gif"), 
                    self.hostname, message['name'], self.format_date(str(message['timestamp'])),
                    ref, self.host])
                list.prepend(parent, [None, "", message['name'], "",
                    ref, self.host])
        elif message['name'] == "ALARM":
            self.filter_uuid = message['obj_uuid']
            if self.vm_filter_uuid() not in self.all_vms:
                return None
            if not self.all_vms[self.vm_filter_uuid()]['is_control_domain']:
                value = message['body'].split("\n")[0].split(" ")[1]
                dom = xml.dom.minidom.parseString(message['body'].split("config:")[1][1:])
                nodes = dom.getElementsByTagName("name")
                #alert = message['body'].split('value="')[1].split('"')[0]
                alert = nodes[0].attributes.getNamedItem("value").value
                nodes = dom.getElementsByTagName("alarm_trigger_level")
                level = nodes[0].attributes.getNamedItem("value").value
                nodes = dom.getElementsByTagName("alarm_trigger_period")
                period = nodes[0].attributes.getNamedItem("value").value

                if "alert_" + alert in messages:
                    parent = list.prepend(None, [gtk.gdk.pixbuf_new_from_file("images/warn.gif"),
                        self.hostname, messages_header["alert_" + alert],
                        self.format_date(str(message['timestamp'])), ref, self.host])
                    list.prepend(parent, [None, "", messages["alert_" + alert] % \
                            (self.all_vms[self.vm_filter_uuid()]['name_label'], float(value)*100, int(period), float(level)*100), "",
                            ref, self.host])
                else:
                    print message['name']
                    print message['body']
            else:
                value = message['body'].split("\n")[0].split(" ")[1]
                alert = message['body'].split('value="')[1].split('"')[0]
                if "host_alert_" + alert in messages:
                    parent = list.prepend(None, [gtk.gdk.pixbuf_new_from_file("images/warn.gif"),
                        self.hostname, messages_header["host_alert_" + alert] % ("Control Domain"),
                        self.format_date(str(message['timestamp'])), ref, self.host])
                    list.prepend(parent, [None, "", messages["host_alert_" + alert] % \
                            ("Control Domain", self.hostname, float(value)), "",
                            ref, self.host])
                else:
                    print message['name']
                    print message['body']
    def add_vm_to_tree(self, vm):
        if  self.all_vms[vm]['resident_on'] != "OpaqueRef:NULL" and self.all_vms[vm]['resident_on'] in self.hostroot:
            resident = self.all_vms[vm]['resident_on']
            self.treestore.prepend(self.hostroot[self.all_vms[vm]['resident_on']], [\
                gtk.gdk.pixbuf_new_from_file("images/tree_%s_16.png"\
                % self.all_vms[vm]['power_state'].lower()),\
                self.all_vms[vm]['name_label'], self.all_vms[vm]['uuid'],\
                "vm", self.all_vms[vm]['power_state'], self.host,
                vm, self.all_vms[vm]['allowed_operations'],  self.all_hosts[resident]['address']])

        elif self.all_vms[vm]['affinity'] != "OpaqueRef:NULL" and self.all_vms[vm]['affinity'] in self.hostroot:
              affinity = self.all_vms[vm]['affinity']
              self.treestore.prepend(self.hostroot[self.all_vms[vm]['affinity']], [\
                  gtk.gdk.pixbuf_new_from_file("images/tree_%s_16.png"\
                  % self.all_vms[vm]['power_state'].lower()),\
                  self.all_vms[vm]['name_label'], self.all_vms[vm]['uuid'],\
                  "vm", self.all_vms[vm]['power_state'], self.host,   
                  vm, self.all_vms[vm]['allowed_operations'], self.all_hosts[affinity]['address']])
        else:
            if self.poolroot:
                self.treestore.prepend(self.poolroot, [\
                    gtk.gdk.pixbuf_new_from_file("images/tree_%s_16.png"\
                    % self.all_vms[vm]['power_state'].lower()),\
                    self.all_vms[vm]['name_label'], self.all_vms[vm]['uuid'],\
                    "vm", self.all_vms[vm]['power_state'], self.host,
                    vm, self.all_vms[vm]['allowed_operations'],  self.host])
            else:
                self.treestore.prepend(self.hostroot[self.all_hosts.keys()[0]], [\
                    gtk.gdk.pixbuf_new_from_file("images/tree_%s_16.png"\
                    % self.all_vms[vm]['power_state'].lower()),\
                    self.all_vms[vm]['name_label'], self.all_vms[vm]['uuid'],\
                    "vm", self.all_vms[vm]['power_state'], self.host,
                    vm, self.all_vms[vm]['allowed_operations'], self.host])

    def fill_allowed_operations(self, ref):
        actions = self.connection.VM.get_allowed_operations(self.session_uuid, ref)['Value']
        self.all_vms[ref]['allowed_operations'] = actions
        return actions

    def fill_vm_network(self, ref, tree, list):
        #self.filter_ref = ref
        #vm_vifs = filter(self.filter_vif_ref, self.all_vif.values())
        list.clear()
        if ref in self.all_vms:
            guest_metrics = self.all_vms[ref]['guest_metrics']

            for vif_ref in self.all_vms[ref]['VIFs']:
                vif = self.all_vif[vif_ref]
                if "kbps" in vif['qos_algorithm_params']:
                    limit =  vif['qos_algorithm_params']['kbps']
                else:
                    limit = ""
                ip = ""
                if guest_metrics in self.all_vm_guest_metrics and vif['device'] + "/ip" in self.all_vm_guest_metrics[guest_metrics]['networks']:
                    ip = self.all_vm_guest_metrics[guest_metrics]['networks'][vif['device'] + "/ip"]

                else:
                    ip = ""
                #FIXME
                if vif['network'] in self.all_network:
                    network =  self.all_network[vif['network']]['name_label'].replace('Pool-wide network associated with eth','Network ')
                else:
                    network = ""
                list.append((vif['device'], \
                        vif['MAC'], \
                        limit, \
                        network, \
                        ip, \
                        str(vif['currently_attached']), vif_ref))
        else:
            print "VM not found %s" % ref 

    def set_vif_limit(self, ref, limit, vm_ref):
      qos_algorithm_params = {
        'kbps': str(limit)
      }
      res = self.connection.VIF.set_qos_algorithm_params(self.session_uuid, ref, qos_algorithm_params)
      if "Value" in res:
          self.track_tasks[res['Value']] = vm_ref
      else:
          print res
    def set_vif_to_manual(self, ref, vm_ref):
      res = self.connection.VIF.set_MAC_autogenerated(self.session_uuid, ref, False)
      if "Value" in res:
          self.track_tasks[res['Value']] = vm_ref
      else:
          print res


    def fill_vm_snapshots(self, uuid, tree=None, list=None):
        list.clear()
        if uuid in self.all_vms:
            all_snapshots = self.all_vms[uuid]['snapshots']
            for snapshot_uuid in all_snapshots:
                snapshot_name = self.all_vms[snapshot_uuid]['name_label']
                snapshot_time = self.all_vms[snapshot_uuid]['snapshot_time']
                snapshot_of = self.all_vms[snapshot_uuid]['snapshot_of']
                snapshot_size = 0 
                for vbd in self.all_vms[snapshot_uuid]['VBDs']:
                    vbd_data = self.all_vbd[vbd]
                    if vbd_data['type'] == 'Disk':
                        snapshot_size += int(self.connection.VDI.get_record(self.session_uuid,vbd_data['VDI'])['Value']['physical_utilisation'])
                list.append([snapshot_uuid, "<b>" + snapshot_name + "</b>\n\nTaken on: " + str(snapshot_time) + "\n\nSize: " + \
                        self.convert_bytes(snapshot_size) + "\n\n" + "Used by: " + self.wine.selected_name + "\n"])

    def update_performance(self, uuid, ref, ip, host=False, period=5):
        # Default three hours of period
        self.halt_performance = False
        for widget in ["scrolledwindow47", "scrolledwindow48", "scrolledwindow49", "scrolledwindow50"]:
            if self.wine.builder.get_object(widget).get_children()[0].get_children():
                #gobject.idle_add(lambda:  self.wine.builder.get_object(widget).get_children()[0].remove(self.wine.builder.get_object(widget).get_children()[0].get_children()[0]) and False)
                gtk.gdk.threads_enter()
                self.wine.builder.get_object(widget).get_children()[0].remove(self.wine.builder.get_object(widget).get_children()[0].get_children()[0])
                gtk.gdk.threads_leave()

        if host:
            data_sources = self.connection.host.get_data_sources(self.session_uuid, ref)
        else:
            data_sources = self.connection.VM.get_data_sources(self.session_uuid, ref)
        if not "Value" in data_sources:
            return
        data_sources = data_sources['Value']
        ds = {}
        for data_source in data_sources:
            if data_source['enabled']:
                name = data_source['name_label']
                desc = data_source['name_description']
                if not name[:3] in ds.keys():
                    ds[name[:3]] = []
            if ds[name[:3]].count([name, desc]) == 0:
                if name not in ("memory_internal_free", "xapi_free_memory_kib", "xapi_memory_usage_kib",  "xapi_live_memory_kib") \
                        and name[:6] != "pif___":
                            ds[name[:3]].append([name, desc])
        if host:
            if os.path.exists(os.path.join(self.wine.pathconfig, "host_rrds.rrd")):
                os.unlink(os.path.join(self.wine.pathconfig, "host_rrds.rrd"))
            urllib.urlretrieve("http://%s/host_rrds?session_id=%s" % (ip, self.session_uuid), os.path.join(self.wine.pathconfig, "host_rrds.rrd"))
            rrd = RRD(os.path.join(self.wine.pathconfig, "host_rrds.rrd"))
        else:
            if os.path.exists(os.path.join(self.wine.pathconfig, "vm_rrds.rrd")):
                os.unlink(os.path.join(self.wine.pathconfig, "vm_rrds.rrd"))
            urllib.urlretrieve("http://%s/vm_rrds?session_id=%s&uuid=%s" % (ip, self.session_uuid, uuid), os.path.join(self.wine.pathconfig, "vm_rrds.rrd"))
            rrd = RRD(os.path.join(self.wine.pathconfig, "vm_rrds.rrd"))
        rrdinfo = rrd.get_data(period)

        def show_tic(value):
            if time.strftime("%S", time.localtime(value)) == "00":
                return time.strftime("%H:%M", time.localtime(value))
            else:
                return ""

        def hovered(chart, graph, (x, y)):
            #print chart.get_title()
            self.wine.builder.get_object("lblperf" + graph.get_title()[:3].lower()).set_label(
                    "%s - %s = %0.2f" % (time.strftime("%d/%m %H:%M:%S", time.localtime(x)),  graph.get_title(), y))

            # Chart
        chart = {}
        graph = {}
        for name in ["cpu", "vbd", "vif", "mem"]:
            chart[name] = line_chart.LineChart()
            chart[name].xaxis.set_show_tics(True)
            chart[name].xaxis.set_tic_format_function(show_tic)
            chart[name].yaxis.set_position(7)
            chart[name].connect("datapoint-hovered", hovered)
            chart[name].legend.set_visible(True)
            chart[name].legend.set_position(line_chart.POSITION_BOTTOM_RIGHT)
            chart[name].set_padding(100)
            chart[name].yaxis.set_label("kBps")
        chart["cpu"].yaxis.set_label("%")
        chart["mem"].yaxis.set_label("MB")

        # CPU Graph
        chart["cpu"].set_yrange((0, 100))
        for key in rrdinfo.keys():
            if key[:3] == "cpu":
                data = rrdinfo[key]["values"]
                for i in range(len(data)):
                    data[i][1] = data[i][1]*100
                graph[key] = line_chart.Graph(key, key, data)
                graph[key].set_show_title(False)
                chart["cpu"].add_graph(graph[key])
                
        chart["cpu"].set_size_request(len(data)*20, 250)
        gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow47").add_with_viewport(chart["cpu"]) and False)
        gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow47").show_all() and False)
        
        # Memory
        if "memory_internal_free" in rrdinfo and "memory" in rrdinfo:
            chart["mem"].set_yrange((0, int(rrdinfo["memory"]["max_value"])/1024/1024))
            data = rrdinfo["memory"]["values"]
            data2 = rrdinfo["memory_internal_free"]["values"]
            for i in range(len(data2)):
                data[i][1] = (data[i][1] - data2[i][1]*1024)/1024/1024
            graph["mem"] = line_chart.Graph("Memory used", "Memory used", data)
            graph["mem"].set_show_title(False)
            chart["mem"].add_graph(graph["mem"])
            chart["mem"].set_size_request(len(data)*20, 250)
        
            gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow48").add_with_viewport(chart["mem"]) and False)
            gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow48").show_all() and False)
        elif "memory_total_kib" in rrdinfo and "xapi_free_memory_kib" in rrdinfo:
            chart["mem"].set_yrange((0, int(rrdinfo["memory_total_kib"]["max_value"])/1024/1024))
            data = rrdinfo["memory_total_kib"]["values"]
            data2 = rrdinfo["xapi_free_memory_kib"]["values"]
            for i in range(len(data2)):
                data[i][1] = (data[i][1] - data2[i][1]*1024)/1024/1024
            graph["mem"] = line_chart.Graph("Memory used", "Memory used", data)
            graph["mem"].set_show_title(False)
            chart["mem"].add_graph(graph["mem"])
            chart["mem"].set_size_request(len(data)*20, 250)
        
            gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow48").add_with_viewport(chart["mem"]) and False)
            gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow48").show_all() and False)

        else:
            label = gtk.Label()
            label.set_markup("<b>No data availaible</b>")
            gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow48").add_with_viewport(label) and False)
            gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow48").show_all() and False)
        
        # Network
        max_value = 0
        data = None
        for key in rrdinfo.keys():
            if key[:3] == "vif" or  key[:3] == "pif":
                data = rrdinfo[key]["values"]
                for i in range(len(data)):
                    data[i][1] = data[i][1]/1024
                    if data[i][1] > max_value:
                        max_value = data[i][1]
                graph[key] = line_chart.Graph(key, key, data)
                graph[key].set_show_title(False)
                chart["vif"].add_graph(graph[key])
        if data:
            chart["vif"].set_yrange((0, max_value))
            chart["vif"].set_size_request(len(data)*20, 250)
            
            gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow49").add_with_viewport(chart["vif"]) and False)
            gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow49").show_all() and False)
        else:
            label = gtk.Label()
            label.set_markup("<b>No data availaible</b>")
            gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow49").add_with_viewport(label) and False)
            gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow49").show_all() and False)
 
        # Disk
        if not host:
            max_value = 0
            data = None
            for key in rrdinfo.keys():
                if key[:3] == "vbd":
                    data = rrdinfo[key]["values"]
                    for i in range(len(data)):
                        data[i][1] = data[i][1]/1024
                    graph[key] = line_chart.Graph(key, key, data)
                    graph[key].set_show_title(False)
                    chart["vbd"].add_graph(graph[key])
                    if rrdinfo[key]['max_value']/1024 > max_value:
                        max_value = rrdinfo[key]['max_value']/1024

            chart["vbd"].set_yrange((0, max_value))
            chart["vbd"].set_size_request(len(data)*20, 250)
            if data: 
                gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow50").add_with_viewport(chart["vbd"]) and False)
                gobject.idle_add(lambda: self.wine.builder.get_object("scrolledwindow50").show_all() and False)
            
        if max_value == 0: max_value = 1
        gobject.idle_add(lambda: self.wine.adjust_scrollbar_performance() and False)
        
        time.sleep(5)
        while not self.halt_performance:
            if os.path.exists(os.path.join(self.wine.pathconfig, "update.rrd")):
                os.unlink(os.path.join(self.wine.pathconfig, "update.rrd"))
            urllib.urlretrieve("http://%s/rrd_updates?session_id=%s&start=%s&cf=AVERAGE&interval=5&vm_uuid=%s" % (ip, self.session_uuid, int(time.time())-10, uuid), os.path.join(self.wine.pathconfig, "update.rrd"))
            rrd = XPORT(os.path.join(self.wine.pathconfig, "update.rrd"))
            rrdinfo = rrd.get_data()
            
            for key in rrdinfo:
                if key in graph:
                    if rrdinfo[key]['values']:
                        if key[:3] == "cpu":
                           data = rrdinfo[key]["values"]
                           for i in range(len(data)):
                               data[i][1] = data[i][1]*100

                           graph[key].add_data(data)
                           chart[key[:3]].queue_draw()
                        elif key[:3] == "vif":
                           data = rrdinfo[key]["values"]
                           for i in range(len(data)):
                                data[i][1] = data[i][1]/1024
                           graph[key].add_data(data)
                           chart[key[:3]].queue_draw()
                        elif key[:3] == "vbd":
                           data = rrdinfo[key]["values"]
                           for i in range(len(data)):
                                data[i][1] = data[i][1]/1024
                           graph[key].add_data(data)
                           chart[key[:3]].queue_draw()
            if "memory_internal_free" in rrdinfo:
                data = rrdinfo["memory"]["values"]
                data2 = rrdinfo["memory_internal_free"]["values"]
                for i in range(len(data2)):
                    data[i][1] = (data[i][1] - data2[i][1]*1024)/1024/1024
                graph["mem"].add_data(data)
                chart["mem"].queue_draw()
            
            for i in range(5):
                if not self.halt_performance:
                    time.sleep(1)
    def fill_vm_log(self, uuid, tree=None, list=None, thread=False):
        self.filter_uuid = uuid
        self.filter_ref = self.wine.selected_ref
        i = 0
        for ch in self.wine.builder.get_object("vmtablelog").get_children():
            gobject.idle_add(lambda: self.wine.builder.get_object("vmtablelog").remove(ch) and False)


        for task_ref in filter(self.task_filter_uuid, self.tasks):
            task = self.all_tasks[task_ref]
            if "snapshot" in task:
               self.add_box_log(task['snapshot']['name_label'], str(task['snapshot']['created']), "%s %s" % (task["snapshot"]["name_label"], self.all_vms[self.track_tasks[task["ref"]]]["name_label"]), str(task['snapshot']['created']), task['ref'], task, float(task['snapshot']['progress']),i%2)
            else:
               if "ref" in task:
                   self.add_box_log(task['name_label'], str(task['created']), "%s %s" % (task["name_label"], self.all_vms[self.track_tasks[task["ref"]]]["name_label"]), str(task['created']), self.get_task_ref_by_uuid(task['uuid']), task, float(task['progress']),i%2)
               else:
                   self.add_box_log(task['name_label'], str(task['created']), "%s %s" % (task["name_label"], task["name_description"]), str(task['created']), task_ref, task, float(task['progress']),i%2)
               i = i + 1
        for log in sorted(filter(self.log_filter_uuid, self.all_messages.values()),  key=itemgetter("timestamp"), reverse=True):
            timestamp = str(log['timestamp'])
            if thread: 
                gobject.idle_add(lambda: self.add_box_log(log['name'], timestamp, log['body'], str(log['timestamp']),alt=i%2) and False)
            else:
                self.add_box_log(log['name'], timestamp, log['body'], str(log['timestamp']),alt=i%2)
            i = i + 1
    def add_box_log(self, title, date, description, time, id=None, task=None, progress=0, alt=0):
        date = self.format_date(date)
        vboxframe = gtk.Frame()
        vboxframe.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#d5e5f7"))
        if task:
            vboxframe.set_size_request(700,100)
        else:
            vboxframe.set_size_request(700,80)
        vboxchild = gtk.Fixed()
        vboxevent = gtk.EventBox()
        vboxevent.add(vboxchild)
        vboxframe.add(vboxevent)
        vboxchildlabel1 = gtk.Label()
        vboxchildlabel1.set_selectable(True)
        vboxchildlabel2 = gtk.Label()
        vboxchildlabel2.set_selectable(True)
        vboxchildlabel3 = gtk.Label()
        vboxchildlabel3.set_selectable(True)
        vboxchildlabel3.set_size_request(600,-1)
        vboxchildlabel3.set_line_wrap(True)
        vboxchildlabel4 = gtk.Label()
        vboxchildlabel4.set_selectable(True)
        #FIXME
        #vboxchildprogressbar.set_style(1)
        vboxchildlabel2.set_label(date)
        if title in messages_header:
            vboxchildlabel1.set_label(messages_header[title])
        else:
            vboxchildlabel1.set_label(title)
        if title in messages:
            vboxchildlabel3.set_label(messages[title] % (self.wine.selected_name))
        else:
            vboxchildlabel3.set_label(description)
        vboxchildlabel1.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))
        #vboxchildlabel4.set_label(time)
        vboxchild.put(vboxchildlabel1, 25, 12)
        vboxchild.put(vboxchildlabel2, 500, 12)
        vboxchild.put(vboxchildlabel3, 25, 32)
        vboxchild.put(vboxchildlabel4, 25, 52)

        # Active task 
        if task:
            self.vboxchildcancel[id] = gtk.Button()
            self.vboxchildcancel[id].connect("clicked", self.cancel_task)
            self.vboxchildcancel[id].set_name(id)
            self.vboxchildprogressbar[id] = gtk.ProgressBar()
            self.vboxchildprogress[id] = gtk.Label()
            self.vboxchildprogress[id].set_selectable(True)
            self.vboxchildprogressbar[id].set_size_request(500,20)
            self.vboxchildprogressbar[id].set_fraction(progress)
            if ("snapshot" in task and (task["snapshot"]["status"] != "failure" and task["snapshot"]["status"] != "success")) or \
                    (task["status"] != "failure" and task["status"] != "success"):
                vboxchild.put(self.vboxchildcancel[id], 500, 32)
                self.vboxchildcancel[id].set_label("Cancel")
                self.vboxchildprogress[id].set_label("Progress: ")
                vboxchild.put(self.vboxchildprogressbar[id], 100, 72)
            elif ("snapshot" in task and task["snapshot"]["status"] == "failure") or task["status"] == "failure":
                self.vboxchildcancel[id].hide()
                self.vboxchildprogressbar[id].hide()
                self.vboxchildprogress[id].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FF0000'))
                if "snapshot" in task:
                    self.vboxchildprogress[id].set_label("Error: %s" % task["snapshot"]["error_info"])
                else:
                    self.vboxchildprogress[id].set_label("Error: %s" % task["error_info"])
            else:
                if ("snapshot" in task and task["snapshot"]["finished"]) or task["finished"]:
                    vboxchildlabel4.set_label("Finished: %s"  % self.format_date(str(task["finished"])))


            vboxchild.put(self.vboxchildprogress[id], 25, 72)
            if ("snapshot" in task and task["snapshot"]["status"] == "success"):
                self.vboxchildcancel[id].hide()
                self.vboxchildprogressbar[id].hide()
            if task["status"] == "success":
                self.vboxchildcancel[id].hide()
                self.vboxchildprogressbar[id].hide()

        if alt: 
            vboxevent.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#d5e5f7"))
        else:
            vboxevent.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#BAE5D3"))
        self.wine.builder.get_object("vmtablelog").add(vboxframe)
        self.wine.builder.get_object("vmtablelog").show_all()        

    def cancel_task(self, widget, data=None):
        self.connection.task.cancel(self.session_uuid, gtk.Buildable.get_name(widget))
        widget.hide()
        self.vboxchildprogress[gtk.Buildable.get_name(widget)].set_label("Cancelled")
        self.vboxchildprogressbar[gtk.Buildable.get_name(widget)].hide()
        self.wine.push_alert("Task cancelled")

    def fill_host_storage(self, ref, list):
        list.clear()
        for storage in self.all_storage.values():
            on_host = False
            for pbd in storage['PBDs']:
                if self.all_pbd[pbd]['host'] == ref:
                    on_host = True
            #if storage['type'] != "iso":
            if on_host:
                if "physical_size" in storage:
                    if int(storage['physical_size']) > 0:
                        usage = "%d%% (%s used)" % \
                                (((float(storage['physical_utilisation'])/1073741824)  / \
                                (float(storage['physical_size'])/1073741824) * 100), \
                                self.convert_bytes(storage['physical_utilisation']))
                    else:
                        usage = "0% (0B Used)"      
                    if storage['name_label'] != "XenServer Tools":
                        list.append((storage['name_label'],
                            storage['name_description'],
                            storage['type'],
                            str(storage['shared']),
                            usage,
                            self.convert_bytes(storage['physical_size']),
                            self.convert_bytes(storage['virtual_allocation'])))

    def fill_host_search(self, ref, list):
        while not self.halt_search:
            gobject.idle_add(lambda: list.clear() and False)
            position = 0
            hosts = {}
            #FIXME: what happen when a pool exists?
            for host in self.all_hosts.keys():
                metrics = self.all_hosts[host]['metrics']
                memory_free = int(self.all_host_metrics[metrics]['memory_free'])
                memory_total = int(self.all_host_metrics[metrics]['memory_total'])
                if memory_total == 0:
                    memory = ""
                    memory_img = 0
                else:
                    memory = str(((memory_total-memory_free)*100)/memory_total) + "% used of " + self.convert_bytes(memory_total)
                    memory_img = int((((memory_total-memory_free)*100)/memory_total)/10)
                start_time = self.all_hosts[host]['other_config']['boot_time'][:-1]
                uptime = self.humanize_time(time.time() - int(start_time))
                hosts[host] = position
                gobject.idle_add(lambda item: list.append(None, item) and False, ([gtk.gdk.pixbuf_new_from_file("images/tree_connected_16.png"),  "<b>" + self.all_hosts[host]['name_label'] + "</b>\n<i>" +  self.all_hosts[host]['name_description']  + "</i>", gtk.gdk.pixbuf_new_from_file("images/usagebar_5.png"), "",gtk.gdk.pixbuf_new_from_file("images/usagebar_%s.png" % str(memory_img)),memory,"-","",self.all_hosts[host]['address'],uptime, None]))

                position = position + 1

            for host in self.all_hosts.keys():
                Thread(target=self.fill_vm_search, args=(host,list,hosts)).start()
            for i in range(0,60):
                if not self.halt_search:
                    time.sleep(1)
    def fill_vm_search(self, host,list, hosts):
        rrd_updates = rrdinfo.RRDUpdates("http://%s/rrd_updates?session_id=%s&start=%d&cf=AVERAGE&interval=5&host=true" % (self.all_hosts[host]["address"], self.session_uuid, time.time()-600))
        rrd_updates.refresh()
        for uuid in rrd_updates.get_vm_list():
            for vm in self.all_vms:
                if self.all_vms[vm]["uuid"] == uuid:
                    break
            guest_metrics = self.all_vms[vm]['guest_metrics']
            ips = []
            with_tools = True
            if guest_metrics != "OpaqueRef:NULL":
                for vif in self.all_vms[vm]['VIFs']:
                    if "networks" in self.all_vm_guest_metrics[guest_metrics]:
                        if self.all_vif[vif]['device'] + "/ip" in self.all_vm_guest_metrics[guest_metrics]['networks']:
                            if self.all_vm_guest_metrics[guest_metrics]['networks'][self.all_vif[vif]['device'] + "/ip"]:
                                ips.append(self.all_vm_guest_metrics[guest_metrics]['networks'][self.all_vif[vif]['device'] + "/ip"])
            else:
                with_tools = False
            cpu = 0
            cpu_pct = 0
            vbd_write_avg = 0
            vbd_write_max = 0
            vbd_read_avg = 0
            vbd_read_max = 0
            vif_write_avg = 0
            vif_write_max = 0
            vif_read_avg = 0
            vif_read_max = 0
            memory = 0
            memory_total = 0
            for param in rrd_updates.get_vm_param_list(uuid):
                    data=[0]
                    media=0.0
                    i = 0
                    row = None
                    for row in range(rrd_updates.get_nrows()):
                           value1 = rrd_updates.get_vm_data(uuid,param,row)
                           if value1 != "NaN":
                                data.append(value1)
                                media += value1
                                i += 1
                    if i == 0: i=1
                    if row:
                        if param.count("cpu") > 0:
                            cpu = cpu + 1
                            cpu_pct = cpu_pct + int(rrd_updates.get_vm_data(uuid,param,row)*100)
                        elif param.count("vbd") > 0 and param.count("write"):
                            try:
                                vbd_write_avg += int((media/i)/1024)
                                vbd_write_max += int(max(data)/1024)
                            except:
                                vbd_write_avg += 0
                                vbd_write_max += 0
                        elif param.count("vbd") > 0 and param.count("read"):
                            try:
                                vbd_read_avg += int((media/i)/1024)
                                vbd_read_max += int(max(data)/1024)
                            except:
                                vbd_read_avg += 0
                                vbd_read_max += 0
                        elif param.count("vif") > 0 and param.count("tx"):
                            try:
                                vif_write_avg += int((media/i)/1024)
                                vif_write_max += int(max(data)/1024)
                            except:
                                vif_write_avg += 0
                                vif_write_max += 0
                        elif param.count("vif") > 0 and param.count("rx"):
                            try:
                                vif_read_avg += int((media/i)/1024)
                                vif_read_max += int(max(data)/1024)
                            except:
                                vif_read_avg += 0
                                vif_read_max += 0
                        elif param.count("memory_internal_free") > 0:
                            memory =  int(rrd_updates.get_vm_data(uuid,param,row))*1024
                            memory_total = int(self.all_vms[vm]['memory_dynamic_max'])
                        else:
                            #print str(media/i) + "/" + str(max(data))
                            #print "last: " + str(rrd_updates.get_vm_data(uuid,param,row))
                            
                            pass

                        if cpu:
                            load = str(cpu_pct/cpu)
                            load_img = str(int((cpu_pct/cpu)/10))
                        else:
                            load = "0"
                            load_img = "0"
                        if memory:
                            memory_used = str(((memory_total-memory)*100)/memory_total)
                            memory_img = str(int(((memory_total-memory)*100)/memory_total)/10)
                        else:
                            memory_used = "0"
                            memory_img = "0"
            if row:
                parent = self.all_vms[vm]['resident_on']
                if parent == "OpaqueRef:NULL": 
                    parent = self.all_vms[vm]['affinity']
                if not self.all_vms[vm]['is_control_domain']:
                    if self.all_vms[vm]['metrics'] not in  self.all_vm_metrics:
                        self.all_vm_metrics[self.all_vms[vm]['metrics']] = self.connection.VM_metrics.get_record(self.session_uuid, self.all_vms[vm]['metrics'])['Value']
                    start_time = self.all_vm_metrics[self.all_vms[vm]['metrics']]['start_time']
                    uptime = self.humanize_time(self.get_seconds_difference(start_time))
                    if parent != "OpaqueRef:NULL":
                        if int(load_img) > 10:
                          load_img = "10"
                        elif int(load_img) < 0:
                          load_img = "0"
                        if int(memory_img) > 10:
                          memory_img = "10"
                        elif int(memory_img) < 0:
                          memory_img = "0"

                        if with_tools:
                             gobject.idle_add(lambda parent_path, item: list.append(list.get_iter(parent_path), item) and False,
                                hosts[parent],
                                ([gtk.gdk.pixbuf_new_from_file("images/tree_running_16.png"), 
                                  self.all_vms[vm]['name_label'] + "\n<i>" + self.all_vms[vm]['name_description'] + "</i>", 
                                  gtk.gdk.pixbuf_new_from_file("images/usagebar_%s.png" % load_img), 
                                  load + "% of " + str(cpu) + " cpus",
                                  gtk.gdk.pixbuf_new_from_file("images/usagebar_%s.png" % abs(int(memory_img))),
                                  memory_used + "% of " + self.convert_bytes(memory_total),
                                  str(vbd_write_avg) + "/" + str(vbd_write_max) + " | " +  str(vbd_read_avg) + "/" + str(vbd_read_max),
                                  str(vif_write_avg) + "/" + str(vif_write_max) + " | " +  str(vif_read_avg) + "/" + str(vif_read_max),
                                  "\n".join(ips),
                                  uptime,
                                  None
                              ]))
                        else:
                            gobject.idle_add(lambda parent_path, item: list.append(list.get_iter(parent_path), item) and False,
                                hosts[parent],
                                ([gtk.gdk.pixbuf_new_from_file("images/tree_running_16.png"), 
                                  self.all_vms[vm]['name_label'] + "\n<i>" + self.all_vms[vm]['name_description'] + "</i>", 
                                  gtk.gdk.pixbuf_new_from_file("images/usagebar_%s.png" % load_img), 
                                  load + "% of " + str(cpu) + " cpus",
                                  gtk.gdk.pixbuf_new_from_file("images/usagebar_0.png"),
                                  "",
                                  "<span foreground='red'><b>XenServer tools</b></span>",
                                  "<span foreground='red'><b>not installed</b></span>",
                                  "-",
                                  uptime,
                                  None
                               ]))
                    else:
                        pass
                        """
                        list.append(None,  
                          ([gtk.gdk.pixbuf_new_from_file("images/tree_running_16.png"), 
                            self.all_vms[vm]['name_label'] + "\n<i>" + self.all_vms[vm]['name_description'] + "</i>", 
                            gtk.gdk.pixbuf_new_from_file("images/usagebar_%s.png" % load_img), 
                            load + "% of " + str(cpu) + " cpus",
                            gtk.gdk.pixbuf_new_from_file("images/usagebar_0.png"),
                            "",
                            "<span foreground='red'><b>XenServer tools</b></span>",
                            "<span foreground='red'><b>not installed</b></span>",
                            "-",
                            uptime,
                            None
                         ]))
                        """
                        #print  self.all_vms[vm]
                else:
                    gobject.idle_add(lambda: list.set(list.get_iter(hosts[parent]), 2,  gtk.gdk.pixbuf_new_from_file("images/usagebar_%s.png" % load_img),
                                            3,  load + "% of " + str(cpu) + " cpus",
                                            7, str(vif_write_avg) + "/" + str(vif_write_max) + " | " +  str(vif_read_avg) + "/" + str(vif_read_max)) and False)
            gobject.idle_add(lambda: self.wine.treesearch.expand_all() and False)



    def fill_local_storage(self, ref, list):
        list.clear()
        """
        for pbd in self.all_storage[ref]['PBDs']:
            print self.all_pbd[pbd]
        print "*************"
        """
        if ref in self.all_storage:
            for vdi in self.all_storage[ref]['VDIs']:
                pct = (int(self.all_vdi[vdi]['physical_utilisation'])/int(self.all_vdi[vdi]['virtual_size']))*100
                if self.all_vdi[vdi]['VBDs']:
                    vbd = self.all_vbd[self.all_vdi[vdi]['VBDs'][0]]
                    vm = self.all_vms[vbd['VM']]['name_label']
                else:
                    vm = ""
                if self.all_vdi[vdi]['is_a_snapshot']:
                    vm += " (snapshot)"
                #FIXME
                if self.all_vdi[vdi]['name_label'] != "base copy":
                    list.append([vdi, self.all_vdi[vdi]['name_label'], self.all_vdi[vdi]['name_description'], \
                            self.convert_bytes(self.all_vdi[vdi]['virtual_size']) + " (" + str(pct) + "% on disk)", vm])
    def fill_vm_storage(self, ref, list):
        self.filter_ref = ref
        all_vbds = filter(self.filter_vbd_ref, self.all_vbd.values())
        list.clear()
        if ref not in self.all_vms:
            return
        for vbd_ref in self.all_vms[ref]['VBDs']:
            vbd = self.all_vbd[vbd_ref]
            if vbd['VDI'] != "OpaqueRef:NULL" and vbd['type'] != "CD":
                if vbd['mode'] == "RW":
                    ro = "False" 
                else:
                    ro = "True" 
                if vbd['VDI']:
                    self.filter_vdi = vbd['VDI']
                    vdi = self.all_vdi[self.filter_vdi_ref()]
                    vdi_name_label = vdi['name_label'] 
                    vdi_name_description =  vdi['name_description']
                    vdi_virtual_size =  vdi['virtual_size']
                    vdi_sr = vdi['SR'] 
                    sr_name = self.all_storage[vdi_sr]['name_label']
                    list.append((vdi_name_label, \
                         vdi_name_description, \
                         sr_name, \
                         vbd['userdevice'], \
                         self.convert_bytes(vdi_virtual_size), \
                         ro, \
                         "0 (Highest) ", \
                         str(vbd['currently_attached']), \
                         "/dev/" + vbd['device'], vbd['VDI'], vbd_ref, vbd['bootable']))
    def fill_vm_storage_dvd(self, ref, list):
        i = 0
        active = 0
        self.filter_ref = ref
        all_vbds = filter(self.filter_vbd_ref, self.all_vbd.values())
        vmvdi = ""
        for vbd in all_vbds:
            if vbd['type'] == "CD":
               vmvdi = vbd['VDI']
        list.clear()
        list.append(["<empty>", "empty", True, True])
        list.append(["DVD drives", "", False, True])
        for sr in self.all_storage:
            if self.all_storage[sr]['type'] == "udev" and self.all_storage[sr]['sm_config']["type"] == "cd":
                if len(self.all_storage[sr]['VDIs']):
                    i = i + 1
                    if self.all_storage[sr]['VDIs'][0] == vmvdi:
                            active = i  
                    if self.all_storage[sr]['VDIs'][0] in self.all_vdi:
                        info = self.all_vdi[self.all_storage[sr]['VDIs'][0]]
                        list.append(["\tDVD Drive " + info['location'][-1:],  self.all_storage[sr]['VDIs'][0], True, False])
                    else:
                        list.append(["\tDVD Drive",  self.all_storage[sr]['VDIs'][0], True, False])
        for sr in self.all_storage:
            if self.all_storage[sr]['type'] == "iso":

                list.append([self.all_storage[sr]['name_label'], sr, False, True])
                i = i + 1
                isos = {}
                for vdi in self.all_storage[sr]['VDIs']:
                    isos[str(self.all_vdi[vdi]['name_label'])] = vdi
                for vdi_ref in sorted(isos):
                    vdi = isos[vdi_ref]
                    list.append(["\t" + self.all_vdi[vdi]['name_label'], vdi, True, False])
                    i = i + 1
                    if vdi == vmvdi:
                        active = i  
        if active == 0:
            return active
        else:
            return active+1
    def update_tab_storage(self, ref, builder):
        labels = {}
        labels['lblstgname'] = self.all_storage[ref]['name_label']
        labels['lblstgdescription'] = self.all_storage[ref]['name_description']
        labels['lblstgtags'] = ", ".join(self.all_storage[ref]['tags'])
        stg_other_config = self.all_storage[ref]['other_config']
        if "folder" in stg_other_config:
            labels['lblstgfolder'] = stg_other_config['folder']
        else:
            labels['lblstgfolder'] = ""
        labels['lblstgtype'] = self.all_storage[ref]['type'].upper()
        labels['lblstgsize'] = "%s used of %s total (%s allocated)" % \
                (self.convert_bytes(self.all_storage[ref]['physical_utilisation']),
                 self.convert_bytes(self.all_storage[ref]['physical_size']),
                 self.convert_bytes(self.all_storage[ref]['virtual_allocation'])
                )
        if "devserial" in self.all_storage[ref]['sm_config']:
            devserial =  self.all_storage[ref]['sm_config']['devserial'].split("-",2)
            labels['lblstgserial'] =  devserial[0].upper() + " ID:"
            if len(devserial) > 1:
                    labels['lblstgscsi'] = devserial[1]
            else:
                labels['lblstgscsi'] = devserial[0]
        else:
            labels['lblstgscsi'] = ""
      
        broken = False
        # Fix using PBD and "currently_attached"
        if len(self.all_storage[ref]['PBDs']) == 0:
            broken = True
            labels['lblstgstate'] = "<span foreground='red'><b>Detached</b></span>"
            labels['lblstghostcon'] = "<span foreground='red'><b>Connection Missing</b></span>"
        else:
            broken = False
            for pbd_ref in self.all_storage[ref]['PBDs']:
                if not self.all_pbd[pbd_ref]['currently_attached']:
                    labels['lblstgstate'] = "<span foreground='red'><b>Broken</b></span>"
                    labels['lblstghostcon'] = "<span foreground='red'><b>Unplugged</b></span>"
                    broken = True
        if not broken:
            if len(self.all_storage[ref]['PBDs']) > 0:
                labels['lblstgstate'] = "<span foreground='green'><b>OK</b></span>"
                labels['lblstghostcon'] = "Connected"
            """
            elif len(self.all_storage[ref]['PBDs']) > 0:
                labels['lblstgstate'] = "<span foreground='red'><b>Dettached</b></span>"
                labels['lblstghostcon'] = "<span foreground='red'><b>Connection Missing</b></span>"
            """
        labels['lblstghost'] = self.wine.selected_host
        if len(self.all_storage[ref]['PBDs']) == 0:
            labels['lblstgmultipath'] = "No"
        else:
            pbd = self.all_pbd[self.all_storage[ref]['PBDs'][0]]
            if "multipathed" in pbd['other_config'] and  pbd['other_config']["multipathed"] == "true":
                if "SCSIid" in pbd['device_config']:
                    #{'uuid': '232b7d15-d8cb-e183-3838-dfd33f6bd597', 'SR': 'OpaqueRef:1832f6e1-73fa-b43d-fcd2-bac969abf867', 'other_config': {'mpath-3600a0b8000294d50000045784b85e36f': '[1, 1, -1, -1]', 'multipathed': 'true'}, 'host': 'OpaqueRef:5c0a69d1-7719-946b-7f3c-683a7058338d', 'currently_attached': True, 'device_config': {'SCSIid': '3600a0b8000294d50000045784b85e36f'}}
                    scsiid = pbd['device_config']["SCSIid"] 
                    paths = eval(pbd["other_config"]["mpath-" + scsiid])
                    if paths[0] == paths[1]:
                        labels['lblstgmultipath'] = "<span foreground='green'>%s of %s paths active</span>" % (paths[0], paths[1])
                    else:
                        labels['lblstgmultipath'] = "<span foreground='red'>%s of %s paths active</span>" % (paths[0], paths[1])
                else:
                    labels['lblstgmultipath'] = "Yes"
            else:
                labels['lblstgmultipath'] = "No"

        for label in labels.keys():
            builder.get_object(label).set_label(labels[label])

    def is_storage_broken(self, ref):
        for pbd_ref in self.all_storage[ref]['PBDs']:
            if not self.all_pbd[pbd_ref]['currently_attached']:
                return True
        return False
         
    def update_tab_template(self, ref, builder):
        labels = {}
        labels['lbltplname'] = self.all_vms[ref]['name_label']
        labels['lbltpldescription'] = self.all_vms[ref]['name_description']
        if not self.all_vms[ref]['HVM_boot_policy']:
            labels['lbltplboot'] = "Boot order:"
            labels["lbltplparameters"] = self.all_vms[ref]['PV_args']
        else:
            labels['lbltplboot'] = "OS boot parameters:"
            labels['lbltplparameters'] = ""
            for param in list(self.all_vms[ref]['HVM_boot_params']['order']):
                    if param == 'c':
                        labels['lbltplparameters'] += "Hard Disk\n"
                    elif param == 'd':
                        labels['lbltplparameters'] += "DVD-Drive\n"
                    elif param == 'n':
                        labels['lbltplparameters'] += "Network\n"

        other_config = self.all_vms[ref]['other_config']
        if "folder" in other_config:
            labels['lbltplfolder'] = other_config['folder']
        else:
            labels['lbltplfolder'] = ""

        labels["lbltplmemory"] = self.convert_bytes(self.all_vms[ref]['memory_dynamic_max'])

        if self.all_vms[ref]['tags']:
            labels["lbltpltags"] = ", ".join(self.all_vms[ref]['tags'])
        else:
            labels["lbltpltags"] = "" 

        labels["lbltplcpu"] = self.all_vms[ref]['VCPUs_at_startup']
        if "auto_poweron" in other_config and other_config["auto_poweron"] == "true":
            labels["lbltplautoboot"] = "Yes"
        else:
            labels["lbltplautoboot"] = "No"


        priority = self.all_vms[ref]["VCPUs_params"]
        if "weight" in priority:
            #labels["lbltplpriority"] = priority['weight']
            weight = priority['weight']
            if weight == 1:
                labels["lbltplpriority"] = "Lowest"
            elif weight <= 4:
                labels["lbltplpriority"] = "Very Low"
            elif weight <= 32:
                labels["lbltplpriority"] = "Low"
            elif weight <= 129:
                labels["lbltplpriority"] = "Below Normal"
            elif weight <= 512:
                labels["lbltplpriority"] = "Normal"
            elif weight <= 2048:
                labels["lbltplpriority"] = "Above Normal"
            elif weight <= 4096:
                labels["lbltplpriority"] = "High"
            elif weight <= 16384:
                labels["lbltplpriority"] = "Very High"
            else:
                labels["lbltplpriority"] = "Highest"
        else:
            labels["lbltplpriority"] = "Normal"
       
        #FIXME 
        #labels["lblvmstartup"] =  str(self.connection.VM_metrics.get_start_time(self.session_uuid,metric)['Value'])
        metric = self.all_vms[ref]['metrics']
        if metric not in self.all_vm_metrics:
           res = self.connection.VM_metrics.get_record(self.session_uuid, ref)
           if "Value" in res:
               self.all_vm_metrics[ref] = res["Value"]
        
        for label in labels.keys():
            builder.get_object(label).set_label(labels[label])
        pass
    def update_tab_host_general(self, ref, builder):
        labels = {}
        software_version = self.all_hosts[ref]['software_version']
        license_params = self.all_hosts[ref]['license_params']
        labels['lblhostname'] = self.all_hosts[ref]['name_label']
        labels['lblhostdescription'] = self.all_hosts[ref]['name_description']
        labels['lblhosttags'] = ", ".join(self.all_hosts[ref]['tags'])
        host_other_config = self.all_hosts[ref]['other_config']
        if "folder" in host_other_config:
            labels['lblhostfolder'] = host_other_config['folder']
        else:
            labels['lblhostfolder'] = "" 
        # FIXME
        if "iscsi_iqn" in host_other_config:
            labels['lblhostiscsi'] = host_other_config['iscsi_iqn'] 
        else:
            labels['lblhostiscsi'] = ""
        #FIXME
        labels['lblhostpool'] = ""
        #str(self.connection.session.get_pool(
        #             self.session_uuid, self.session['Value'])['Value'])
        logging =  self.all_hosts[ref]['logging']
        if "syslog_destination" in logging:
            labels['lblhostlog'] = logging['syslog_destination']
        else:
            labels['lblhostlog'] = "Local" 

        boot_time = self.humanize_time(time.time() - int(host_other_config['boot_time'][:-1]))
        tool_boot_time = self.humanize_time(time.time() - int(host_other_config['agent_start_time'][:-1]))
        labels['lblhostuptime'] = boot_time
        labels['lblhosttooluptime'] = tool_boot_time
        labels['lblhostdns'] =  self.all_hosts[ref]['hostname']
        labels['lblhostprimary'] =  self.all_hosts[ref]['address']
        resident_vms = self.all_hosts[ref]['resident_VMs']
        host_vms_memory = ""
        for resident_vm_uuid in resident_vms:
            if self.all_vms[resident_vm_uuid]['is_control_domain']:
               host_memory =  self.all_vms[resident_vm_uuid]['memory_target']
            else:
               host_vms_memory += self.all_vms[resident_vm_uuid]['name_label'] \
                    + ": using " + \
                    self.convert_bytes(self.all_vms[resident_vm_uuid]['memory_dynamic_max']) + "\n"
        host_metrics_uuid = self.all_hosts[ref]['metrics']
        host_metrics = self.all_host_metrics[host_metrics_uuid]
        labels['lblhostmemserver'] = "%s free of %s available (%s total)"  % \
                (self.convert_bytes(host_metrics['memory_free']), \
                self.convert_bytes(int(host_metrics['memory_total']) - int(host_memory)), \
                self.convert_bytes(host_metrics['memory_total']))
        labels['lblhostmemoryvms'] = host_vms_memory
        labels['lblhostmemory'] = self.convert_bytes(host_memory)
        labels['lblhostversiondate'] = software_version['date']
        labels['lblhostversionbuildnumber'] = software_version['build_number']
        labels['lblhostversionbuildversion'] = software_version['product_version']
        expiry = self.humanize_time(self.get_seconds_difference_reverse(license_params['expiry']))
        labels['lblhostlicexpire'] = expiry
        labels['lblhostlicserver'] = license_params['sku_marketing_name']
        labels['lblhostliccode'] = license_params['productcode']
        labels['lblhostlicserial'] = license_params['serialnumber']
        host_cpus = self.all_hosts[ref]['host_CPUs']
        cpus = ""
        for host_cpu_uuid in host_cpus:
            cpus += "Vendor: %s\nModel: %s\nSpeed: %s\n" % \
                (self.all_host_cpu[host_cpu_uuid]['vendor'],
                self.all_host_cpu[host_cpu_uuid]['modelname'],
                self.all_host_cpu[host_cpu_uuid]['speed'])
                 
        labels['lblhostcpus'] = cpus

        host_patchs = self.all_hosts[ref]['patches']
        patchs = ""
        for host_cpu_patch in host_patchs:
            pool_patch = self.all_host_patch[host_cpu_patch]['pool_patch']
            patchs += self.all_pool_patch[pool_patch]['name_label'] + "\n"

        labels['lblhostpatchs'] = patchs

        # TODO: list hotfix applied
        for label in labels.keys():
            builder.get_object(label).set_label(labels[label])
    def update_tab_pool_general(self, ref, builder):
        labels = {}
        if ref not in  self.all_pools: 
            return
        labels["lblpoolname"] = self.all_pools[ref]['name_label']
        labels["lblpooldescription"] = self.all_pools[ref]['name_description']
        other_config = self.all_pools[ref]['other_config']
        if self.all_pools[ref]['tags']:
            labels["lblpooltags"] = ", ".join(self.all_pools[ref]['tags'])
        else:
            labels["lblpooltags"] = "" 
        if "folder" in other_config:
            labels["lblpoolfolder"] = other_config['folder']
        else:
            labels["lblpoolfolder"] = ""

        fullpatchs = ""
        partialpatchs = ""
        for patch in self.all_pool_patch:
            hosts = {}
            for host_patch in self.all_pool_patch[patch]["host_patches"]:
                host = self.all_host_patch[host_patch]["host"]
                if host not in hosts:
                    hosts[host] = [] 

                hosts[host] += self.all_pool_patch[patch]["host_patches"]
            if hosts.keys() == self.all_hosts.keys():
                fullpatchs += self.all_pool_patch[patch]["name_label"] + "\n"
            else:
                partialpatchs += self.all_pool_patch[patch]["name_label"] + "\n"

        labels["lblpoolfullpatchs"] = fullpatchs
        labels["lblpoolpartialpatchs"] = partialpatchs

        for label in labels.keys():
            builder.get_object(label).set_label(labels[label])
        if partialpatchs == "":
            builder.get_object("label365").hide()
            builder.get_object("lblpoolpartialpatchs").hide()
        if fullpatchs == "":
            builder.get_object("label363").hide()
            builder.get_object("lblpoolfullpatchs").hide()

    def update_tab_vm_general(self, ref, builder):
        self.builder = builder
        labels = {}
        if ref in self.all_vms:
            metric = self.all_vms[ref]['metrics']
            metric_guest = self.all_vms[ref]['guest_metrics']
            labels["lblvmname"] = self.all_vms[ref]['name_label']
            labels["lblvmdescription"] = self.all_vms[ref]['name_description']
            labels["lblvmuuid"] = self.all_vms[ref]['uuid']
            labels["lblvmmemory"] = self.convert_bytes(self.all_vms[ref]['memory_dynamic_max'])
            if self.all_vms[ref]['tags']:
                labels["lblvmtags"] = ", ".join(self.all_vms[ref]['tags'])
            else:
                labels["lblvmtags"] = "" 
            labels["lblvmcpu"] = self.all_vms[ref]['VCPUs_at_startup']
            other_config = self.all_vms[ref]['other_config']
            if "auto_poweron" in other_config and other_config["auto_poweron"] == "true":
                labels["lblvmautoboot"] = "Yes"
            else:
                labels["lblvmautoboot"] = "No"

            if not self.all_vms[ref]['HVM_boot_policy']:
                labels['lblvmboot'] = "Boot order:"
                labels["lblvmparameters"] = self.all_vms[ref]['PV_args']
            else:
                labels['lblvmboot'] = "OS boot parameters:"
                labels['lblvmparameters'] = ""
                for param in list(self.all_vms[ref]['HVM_boot_params']['order']):
                        if param == 'c':
                            labels['lblvmparameters'] += "Hard Disk\n"
                        elif param == 'd':
                            labels['lblvmparameters'] += "DVD-Drive\n"
                        elif param == 'n':
                            labels['lblvmparameters'] += "Network\n"

            priority = self.all_vms[ref]["VCPUs_params"]
            if "weight" in priority:
                weight = int(priority['weight'])
                if weight == 1:
                    labels["lblvmpriority"] = "Lowest"
                elif weight <= 4:
                    labels["lblvmpriority"] = "Very Low"
                elif weight <= 32:
                    labels["lblvmpriority"] = "Low"
                elif weight <= 129:
                    labels["lblvmpriority"] = "Below Normal"
                elif weight <= 512:
                    labels["lblvmpriority"] = "Normal"
                elif weight <= 2048:
                    labels["lblvmpriority"] = "Above Normal"
                elif weight <= 4096:
                    labels["lblvmpriority"] = "High"
                elif weight <= 16384:
                    labels["lblvmpriority"] = "Very High"
                else:
                    labels["lblvmpriority"] = "Highest"
            else:
                labels["lblvmpriority"] = "Normal"
           
            #FIXME 
            #labels["lblvmstartup"] =  str(self.connection.VM_metrics.get_start_time(self.session_uuid,metric)['Value'])
            metric = self.all_vms[ref]['metrics']
            if metric not in self.all_vm_metrics:
               res = self.connection.VM_metrics.get_record(self.session_uuid, ref)
               if "Value" in res:
                   self.all_vm_metrics[ref] = res["Value"]
            
            if metric in self.all_vm_metrics:
                if self.all_vm_metrics[metric]['start_time'] != "19700101T00:00:00Z":
                    startup = self.humanize_time(self.get_seconds_difference(self.all_vm_metrics[metric]['start_time']))
                    labels["lblvmstartup"] = startup
                else:
                    labels["lblvmstartup"] = "never started up"
            else:
                labels["lblvmstartup"] =  "" 
            labels['lblvmdistro'] = ""
            if metric_guest != "OpaqueRef:NULL" and metric_guest in self.all_vm_guest_metrics:
                guest_metrics = self.all_vm_guest_metrics[metric_guest]
                if "PV_drivers_up_to_date" in guest_metrics and guest_metrics['PV_drivers_up_to_date']:
                    state = "Optimized"
                else:
                    state = "Not optimized"
                if "PV_drivers_up_to_date" in guest_metrics and "major" in guest_metrics["PV_drivers_version"]:
                    if "build" in guest_metrics['PV_drivers_version']:
                        state = state + " (version " + guest_metrics['PV_drivers_version']['major'] + "."\
                            + guest_metrics['PV_drivers_version']['minor'] + " build "\
                            + guest_metrics['PV_drivers_version']['build'] + ")"
                    else:
                        state = state + " (version " + guest_metrics['PV_drivers_version']['major'] + "."\
                            + guest_metrics['PV_drivers_version']['minor'] + " build )"
                else:
                    state = "<b>Tools not installed</b>"    
                labels["lblvmvirtstate"] = state
                if "name" in guest_metrics["os_version"]:
                    labels["lblvmdistro"] = guest_metrics["os_version"]["name"]
            else:
                state = "<span foreground='red'><b>Tools not installed</b></span>"
            labels["lblvmvirtstate"] = state
            if "folder" in other_config:
                labels["lblvmfolder"] = other_config['folder']
            else:
                labels["lblvmfolder"] = ""
                
            for label in labels.keys():
                builder.get_object(label).set_label(labels[label])
    def export_vm(self, ref, destination, ref2=None, as_vm = False):
        if ref2:
            task_uuid = self.connection.task.create(self.session_uuid, "Exporting snapshot", "Exporting snapshot " + destination)
        else:
            task_uuid = self.connection.task.create(self.session_uuid, "Exporting VM", "Exporting VM " + destination)
        self.track_tasks[task_uuid['Value']] = ref2 if ref2 else ref
        url = "http://%s/export?ref=%s&session_id=%s&task_id=%s" % (self.wine.selected_host,  
                               ref, self.session_uuid, task_uuid['Value'])
        Thread(target=self.download_export, args=(url,destination, ref, as_vm)).start()
       
    def download_export(self, url, destination, ref, as_vm):
        #print "Saving %s to %s" % (url, destination)
        if as_vm:
             self.connection.VM.set_is_a_template(self.session_uuid, ref, False)
        urllib.urlretrieve(url, destination)
        if as_vm:
             self.connection.VM.set_is_a_template(self.session_uuid, ref, True)
    
    
    def get_actions(self, ref):
        return self.all_vms[ref]['allowed_operations'] 
    def get_connect_string(self, ref):
        #FIXME
        """
        vm_uuid  = self.connection.VM.get_by_uuid(self.session_uuid,uuid)
        consoles = self.connection.VM.get_consoles(self.session_uuid, vm_uuid['Value'])
        console  = self.connection.console.get_record(self.session_uuid,consoles['Value'][0])
        """
        return "CONNECT /console?ref=%s&session_id=%s HTTP/1.1\r\n\r\n" % (ref,self.session_uuid)
    def get_connect_parameters(self, ref, host):
        """
        vm_uuid  = self.connection.VM.get_by_uuid(self.session_uuid,uuid)
        consoles = self.connection.VM.get_consoles(self.session_uuid, vm_uuid['Value'])
        console  = self.connection.console.get_record(self.session_uuid,consoles['Value'][0])
        """
        return "%s %s %s" % (host, ref, self.session_uuid)
        
    # TODO: these should *not* be here
    # {
    def dump(self, obj):
      for attr in dir(obj):
        print "obj.%s = %s" % (attr, getattr(obj, attr))
    def humanize_time(self, secs):
        string = ""
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        days, hours = divmod(hours, 24)
        if days:
            string += "%02d days " % (days)
        if hours:
            string += "%02d hours " % (hours)
        if mins:
            string += "%02d minutes " % (mins)
        if secs:
            string += "%02d seconds " % (secs)
        return string
    def convert_bytes(self, n):
        """
        http://www.5dollarwhitebox.org/drupal/node/84
        """
        n = float(n)
        K, M, G, T = 1 << 10, 1 << 20, 1 << 30, 1 << 40
        if   n >= T:
            return '%.2fT' % (float(n) / T)
        elif n >= G:
            return '%.2fG' % (float(n) / G)
        elif n >= M:
            return '%.2fM' % (float(n) / M)
        elif n >= K:
            return '%.2fK' % (float(n) / K)
        else:
            return '%d' % n
    # }

    def thread_host_search(self, ref, list):
        Thread(target=self.fill_host_search, args=(ref, list)).start()
        return True
    def search_ref(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 6) == user_data:
            self.found_iter = iter_ref
    def event_next(self):
        print "Entering event loop"
        
        while not self.halt:
            try:
                eventn = self.connection_events.event.next(self.session_events_uuid)
                if "Value" in eventn:
                    for event in eventn["Value"]:
                           if event['class'] == "vm":
                                if event['operation'] == "add":
                                    self.all_vms[event["ref"]] =  event['snapshot']
                                    if not self.all_vms[event["ref"]]["is_a_snapshot"]:
                                        gobject.idle_add(lambda: self.add_vm_to_tree(event["ref"]) and False)
                                    else:
                                        gobject.idle_add(lambda: self.fill_vm_snapshots(self.wine.selected_ref, \
                                             self.wine.builder.get_object("treevmsnapshots"), \
                                             self.wine.builder.get_object("listvmsnapshots")) and False)

                                    gobject.idle_add(lambda: self.wine.modelfilter.clear_cache() and False)
                                    gobject.idle_add(lambda: self.wine.modelfilter.refilter() and False)
                                    for track in self.track_tasks:
                                        if self.track_tasks[track] == "Import.VM":
                                            self.track_tasks[track] = event["ref"]
                                        if self.track_tasks[track] == "Backup.Server":
                                            self.track_tasks[track] = event["ref"]
                                        if self.track_tasks[track] == "Restore.Server":
                                            self.track_tasks[track] = event["ref"]
                                        if self.track_tasks[track] == "Backup.Pool":
                                            self.track_tasks[track] = event["ref"]
                                        if self.track_tasks[track] == "Restore.Pool":
                                            self.track_tasks[track] = event["ref"]
                                        if self.track_tasks[track] == "Upload.Patch":
                                            self.track_tasks[track] = event["ref"]
                                    self.wine.builder.get_object("wprogressimportvm").hide()
                                    # Perfect -> set now import_ref to event["ref"]
                                    self.import_ref = event["ref"]
                                elif event['operation'] == "del":
                                    if not self.all_vms[event["ref"]]["is_a_snapshot"]:
                                        self.found_iter = None 
                                        self.treestore.foreach(self.search_ref, event["ref"])
                                        if self.found_iter:
                                            gobject.idle_add(lambda: self.treestore.remove(self.found_iter) and False)
                                        del self.all_vms[event["ref"]]
                                    else:
                                        gobject.idle_add(lambda: self.fill_vm_snapshots(self.wine.selected_ref, \
                                             self.wine.builder.get_object("treevmsnapshots"), \
                                             self.wine.builder.get_object("listvmsnapshots")) and False)
                                        del self.all_vms[event["ref"]]

                                else:
                                    self.filter_uuid = event['snapshot']['uuid']
                                    if self.vm_filter_uuid():
                                        #make into a template
                                        if event['snapshot']['is_a_template']  != self.all_vms[self.vm_filter_uuid()]['is_a_template']:
                                            self.all_vms[self.vm_filter_uuid()] =  event['snapshot']
                                            self.found_iter = None 
                                            self.treestore.foreach(self.search_ref, event["ref"])
                                            if self.found_iter and event['snapshot']['is_a_template']:
                                                gobject.idle_add(lambda: self.treestore.set(self.found_iter, 0,  gtk.gdk.pixbuf_new_from_file("images/user_template_16.png"), 3,  "custom_template") and False)
                                                gobject.idle_add(lambda: self.wine.update_tabs() and False)
                                        else:
                                            if event['snapshot']['resident_on'] !=  self.all_vms[self.vm_filter_uuid()]['resident_on']:
                                                self.found_iter = None 
                                                gobject.idle_add(lambda: self.treestore.foreach(self.search_ref, event["ref"]) and False)
                                                if self.found_iter:
                                                    gobject.idle_add(lambda: self.treestore.remove(self.found_iter) and False)
                                                    self.all_vms[self.vm_filter_uuid()] =  event['snapshot']
                                                    gobject.idle_add(lambda: self.add_vm_to_tree(event["ref"] and False))
             
                                            if event['snapshot']['affinity'] !=  self.all_vms[self.vm_filter_uuid()]['affinity']:
                                                print "migrate or start on or resume on2"
                                            self.all_vms[self.vm_filter_uuid()] =  event['snapshot']
                                    else:
                                        if event["ref"] in self.track_tasks:
                                            self.all_vms[self.track_tasks[event["ref"]]] =  event['snapshot']

                                        else:
                                            self.all_vms[event["ref"]] =  event['snapshot']
                                    self.all_vms[event["ref"]] =  event['snapshot']
                                    self.treestore.foreach(self.update_vm_status, "")
                                    gobject.idle_add(lambda: self.wine.update_memory_tab() and False)
                           else:
                                if event['class'] == "vm_guest_metrics":
                                    self.all_vm_guest_metrics[event['ref']] = self.connection.VM_guest_metrics.get_record(self.session_uuid, event['ref'])
                                if event['class'] == "task":
                                    #print ">>>" +  event["snapshot"]["name_label"] + " " + event["snapshot"]["status"] + " " + str(event["snapshot"]["progress"]) + ":\t", event
                                    self.all_tasks[event["ref"]] = event["snapshot"]
                                    if event["ref"] not in self.track_tasks:
                                        #print event 
                                        #print event["snapshot"]["name_label"] + " " + event["snapshot"]["status"] + " " + str(event["snapshot"]["progress"]) + ":\t", event
                                        pass
                                    if event["snapshot"]["status"] == "success":
                                       if event["ref"] in self.vboxchildprogressbar:
                                           self.vboxchildprogress[event["ref"]].hide()
                                           self.vboxchildprogressbar[event["ref"]].hide()
                                           self.vboxchildcancel[event["ref"]].hide()
                                    if event["snapshot"]["error_info"]:
                                        if event["ref"] in self.track_tasks:
                                            if self.track_tasks[event["ref"]] in self.all_vms:
                                                gobject.idle_add(lambda: self.wine.push_error_alert("%s %s %s" % (event["snapshot"]["name_label"], self.all_vms[self.track_tasks[event["ref"]]]["name_label"], event["snapshot"]["error_info"])) and False)
                                                eref =  event["ref"] 
                                                if eref in self.vboxchildcancel:
                                                    self.vboxchildcancel[eref].hide()
                                                    self.vboxchildprogressbar[eref].hide()
                                                    self.vboxchildprogress[eref].set_label(str(event["snapshot"]["error_info"]))
                                                    self.vboxchildprogress[eref].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FF0000'))

                                            else:
                                                self.wine.builder.get_object("wprogressimportvm").hide()
                                                self.wine.builder.get_object("tabboximport").set_current_page(2)
                                                gobject.idle_add(lambda: self.wine.push_error_alert("%s: %s" % (event["snapshot"]["name_description"], event["snapshot"]["error_info"])) and False)
                                    else:
                                        if event["ref"] in self.track_tasks:
                                            if self.track_tasks[event["ref"]] in self.all_vms:
                                                if event["snapshot"]["status"] == "success":
                                                    gobject.idle_add(lambda: self.wine.push_alert("%s %s completed" % (event["snapshot"]["name_label"], self.all_vms[self.track_tasks[event["ref"]]]["name_label"])) and False)
                                                else:
                                                    gobject.idle_add(lambda: self.wine.push_alert("%s %s %s" % (event["snapshot"]["name_label"], self.all_vms[self.track_tasks[event["ref"]]]["name_label"], (" %.2f%%" % (float(event["snapshot"]["progress"])*100)))) and False)
                                            else:
                                                vm = self.connection.VM.get_record(self.session_uuid, self.track_tasks[event["ref"]])
                                                if "Value" in vm:
                                                    self.all_vms[self.track_tasks[event["ref"]]] = vm['Value']
                                                    #self.add_vm_to_tree(self.track_tasks[event["ref"]])
                                                    gobject.idle_add(lambda: self.wine.modelfilter.clear_cache() and False)
                                                    gobject.idle_add(lambda: self.wine.modelfilter.refilter() and False)
                                                    gobject.idle_add(lambda: self.wine.push_alert("%s %s %s" % (event["snapshot"]["name_label"], self.all_vms[self.track_tasks[event["ref"]]]["name_label"], (" %.2f%%" % (float(event["snapshot"]["progress"])*100)))) and False)
                                                else:
                                                    gobject.idle_add(lambda: self.wine.push_alert("%s: %s %s" % (event["snapshot"]["name_label"], event["snapshot"]["name_description"],  (" %.2f%%" % (float(event["snapshot"]["progress"])*100)))) and False)
                                        else:
                                             pass  #FIXME?
                                             #self.wine.push_alert(event["snapshot"]["name_label"] + (" %.2f%%" % (float(event["snapshot"]["progress"])*100)))
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "Async.VIF.create":
                                        dom = xml.dom.minidom.parseString(event['snapshot']['result'])
                                        nodes = dom.getElementsByTagName("value")
                                        vif_ref = nodes[0].childNodes[0].data
                                        self.connection.VIF.plug(self.session_uuid, vif_ref)
                                        if self.wine.selected_tab == "VM_Network":
                                            gobject.idle_add(lambda: self.fill_vm_network(self.wine.selected_ref,
                                                    self.wine.builder.get_object("treevmnetwork"),
                                                    self.wine.builder.get_object("listvmnetwork")) and False)

                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "Async.VM.revert":
                                        self.start_vm(self.track_tasks[event["ref"]])

                                    if event["snapshot"]["status"] == "success" and \
                                            (event["snapshot"]["name_label"] == "Async.VM.clone" or event["snapshot"]["name_label"] == "Async.VM.copy"):
                                        dom = xml.dom.minidom.parseString(event['snapshot']['result'])
                                        nodes = dom.getElementsByTagName("value")
                                        vm_ref = nodes[0].childNodes[0].data
                                        #self.add_vm_to_tree(vm_ref)
                                        if event["ref"] in self.set_descriptions:
                                            self.connection.VM.set_name_description(self.session_uuid, vm_ref, self.set_descriptions[event["ref"]])
                                    if event["snapshot"]["status"] == "success" and (event["snapshot"]["name_label"] == "Async.VM.provision" or \
                                            event["snapshot"]["name_label"] == "Async.VM.clone" or event["snapshot"]["name_label"] == "Async.VM.copy"):
                                        self.filter_uuid = event['snapshot']['uuid']
                                        # TODO
                                        # Detect VM with event["ref"]
                                        if event["ref"] in self.track_tasks and self.track_tasks[event["ref"]] in self.all_vms:
                                            for vbd in self.all_vms[self.track_tasks[event["ref"]]]['VBDs']:
                                                self.all_storage[vbd] = self.connection.VBD.get_record(self.session_uuid, vbd)['Value']
                                            for vif in self.all_vms[self.track_tasks[event["ref"]]]['VIFs']:
                                                self.all_vif[vif] = self.connection.VIF.get_record(self.session_uuid, vif)['Value']
                                        if self.vm_filter_uuid() != None:
                                            self.all_vms[self.vm_filter_uuid()]['allowed_operations'] = \
                                                self.connection.VM.get_allowed_operations(self.session_uuid, self.vm_filter_uuid())['Value']
                                        else:
                                            if event["ref"] in self.track_tasks:
                                                self.all_vms[self.track_tasks[event["ref"]]]['allowed_operations'] = \
                                                    self.connection.VM.get_allowed_operations(self.session_uuid, self.track_tasks[event["ref"]])['Value']
                                                if self.all_vms[self.track_tasks[event["ref"]]]['allowed_operations'].count("start"):
                                                    if self.track_tasks[event["ref"]] in self.autostart:
                                                        host_start = self.autostart[self.track_tasks[event["ref"]]]
                                                        res = self.connection.Async.VM.start_on(self.session_uuid, self.track_tasks[event["ref"]], host_start, False, False)
                                                        if "Value" in res:
                                                            self.track_tasks[res['Value']] = self.track_tasks[event["ref"]]
                                                        else:
                                                            print res
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "Async.VM.snapshot": 
                                        self.filter_uuid = event['snapshot']['uuid']
                                        if self.track_tasks[event["ref"]] in self.all_vms:
                                            vm_uuid = self.track_tasks[event["ref"]]
                                            dom = xml.dom.minidom.parseString(event['snapshot']['result'])
                                            nodes = dom.getElementsByTagName("value")
                                            snapshot_ref = nodes[0].childNodes[0].data
                                            #self.all_vms[vm_uuid]['snapshots'].append(snapshot_ref)
                                            self.all_vms[snapshot_ref] = self.connection.VM.get_record(self.session_uuid, snapshot_ref)['Value']
                                            for vbd in self.all_vms[snapshot_ref]['VBDs']:
                                                #FIXME
                                                self.all_vbd[vbd] = self.connection.VBD.get_record(self.session_uuid, vbd)['Value']

                                            if self.track_tasks[event["ref"]] == self.wine.selected_ref and \
                                                self.wine.selected_tab == "VM_Snapshots":
                                                    gobject.idle_add(lambda: self.fill_vm_snapshots(self.wine.selected_ref, \
                                                         self.wine.builder.get_object("treevmsnapshots"), \
                                                         self.wine.builder.get_object("listvmsnapshots")) and False)
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "VM.Async.snapshot": 
                                            if self.track_tasks[event["ref"]] == self.wine.selected_ref and \
                                                self.wine.selected_tab == "VM_Snapshots":
                                                    gobject.idle_add(lambda: self.fill_vm_snapshots(self.wine.selected_ref, \
                                                         self.wine.builder.get_object("treevmsnapshots"), \
                                                         self.wine.builder.get_object("listvmsnapshots")) and False)
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "Importing VM": 
                                            if self.import_start:
                                                self.start_vm(self.track_tasks[event["ref"]])
                                            if self.import_make_into_template:
                                                self.make_into_template(self.track_tasks[event["ref"]])
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "VM.destroy": 
                                            if self.wine.selected_tab == "VM_Snapshots":
                                                    gobject.idle_add(lambda: self.fill_vm_snapshots(self.wine.selected_ref, \
                                                         self.wine.builder.get_object("treevmsnapshots"), \
                                                         self.wine.builder.get_object("listvmsnapshots")) and False)
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "VIF.destroy": 
                                            if self.wine.selected_tab == "VM_Network":
                                                    gobject.idle_add(lambda: self.fill_vm_network(self.wine.selected_ref, \
                                                         self.wine.builder.get_object("treevmnetwork"), \
                                                         self.wine.builder.get_object("listvmnetwork")) and False)
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "VIF.plug": 
                                            if self.wine.selected_tab == "VM_Network":
                                                    gobject.idle_add(lambda: self.fill_vm_network(self.wine.selected_ref, \
                                                         self.wine.builder.get_object("treevmnetwork"), \
                                                         self.wine.builder.get_object("listvmnetwork")) and False)

                                    if event["snapshot"]["status"] == "success" and \
                                            (event["snapshot"]["name_label"] == "VBD.create" or \
                                            event["snapshot"]["name_label"] == "VBD.destroy"): 
                                            if self.wine.selected_tab == "VM_Storage":
                                                    #print "fill_vm_storage start"
                                                    gobject.idle_add(lambda: self.fill_vm_storage(self.wine.selected_ref, \
                                                         self.wine.builder.get_object("listvmstorage")) and False)
                                                    #print pdb.set_trace()
                                                    #print "fill_vm_storage end"
                                    if event["snapshot"]["status"] == "success" and \
                                            (event["snapshot"]["name_label"] == "VDI.create" or \
                                            event["snapshot"]["name_label"] == "VDI.destroy"): 
                                            if self.wine.selected_tab == "Local_Storage":
                                                    gobject.idle_add(lambda: self.fill_local_storage(self.wine.selected_ref, \
                                                         self.wine.builder.get_object("liststg")) and False)
                                    if event["snapshot"]["status"] == "success" and \
                                            (event["snapshot"]["name_label"] == "network.create" or \
                                            event["snapshot"]["name_label"] == "network.destroy"): 
                                            if self.wine.selected_tab == "HOST_Network":
                                                gobject.idle_add(lambda: self.wine.update_tab_host_network() and False)

                                    if event["snapshot"]["status"] == "success" and \
                                            (event["snapshot"]["name_label"] == "Async.Bond.create" or  \
                                             event["snapshot"]["name_label"] == "Bond.create" or  \
                                             event["snapshot"]["name_label"] == "Async.Bond.destroy" or  \
                                             event["snapshot"]["name_label"] == "Bond.destroy"): 
                                             if self.wine.selected_tab == "HOST_Nics":
                                                gobject.idle_add(lambda: self.wine.update_tab_host_nics() and False)

                                    if event["ref"] in self.track_tasks:
                                        self.tasks[event["ref"]] = event
                                    if event["ref"] in self.vboxchildprogressbar:
                                         self.vboxchildprogressbar[event["ref"]].set_fraction(float(event["snapshot"]["progress"]))
                                                
                                    else:
                                       if event["ref"] in self.track_tasks:
                                            self.tasks[event["ref"]] = event
                                            if self.track_tasks[event["ref"]] == self.wine.selected_ref and \
                                                self.wine.selected_tab == "VM_Logs":
                                                if event["ref"] in self.track_tasks and event["ref"] not in self.vboxchildprogressbar:
                                                    gobject.idle_add(lambda: self.fill_vm_log(self.wine.selected_uuid, thread=True) and False)
                                       else:
                                           if event["snapshot"]["name_label"] == "Exporting VM" and event["ref"] not in self.vboxchildprogressbar:
                                               self.track_tasks[event["ref"]] = self.wine.selected_ref 
                                               self.tasks[event["ref"]] = event
                                               gobject.idle_add(lambda: self.fill_vm_log(self.wine.selected_uuid, thread=True) and False)
                                           else:
                                                #print event
                                               pass

                                else:
                                    #print event
                                    if event["class"] == "vdi":
                                        self.all_vdi[event["ref"]] = event["snapshot"]
                                        if self.wine.selected_tab == "Local_Storage":
                                            liststg = self.wine.builder.get_object("liststg")
                                            gobject.idle_add(lambda: self.fill_local_storage(self.wine.selected_ref,liststg) and False)
                                        if self.wine.selected_tab == "VM_Storage":
                                            gobject.idle_add(lambda: self.fill_vm_storage(self.wine.selected_ref, \
                                                    self.wine.builder.get_object("listvmstorage")) and False)

                                    elif event["class"] == "vbd":
                                        self.all_vbd[event["ref"]] = event["snapshot"]
                                        """
                                        if event["snapshot"]["allowed_operations"].count("attach") == 1:
                                            self.last_vbd = event["ref"]
                                        """  
                                    elif event["class"] == "pif":
                                       self.all_pif[event["ref"]]  = event["snapshot"]
                                       if self.wine.selected_tab == "HOST_Nics":
                                           gobject.idle_add(lambda: self.wine.update_tab_host_nics() and False)

                                    elif event["class"] == "bond":
                                       if event["operation"] == "del":
                                           del self.all_bond[event["ref"]]
                                       else:
                                           self.all_bond[event["ref"]]  = event["snapshot"]
                                       if self.wine.selected_tab == "HOST_Nics":
                                           gobject.idle_add(lambda: self.wine.update_tab_host_nics() and False)

                                    elif event["class"] == "vif":
                                        if event["operation"] == "del":
                                            del self.all_vif[event["ref"]]
                                        else:
                                            if event["operation"] == "add":
                                                self.connection.VIF.plug(self.session_uuid, event["ref"])
                                            self.all_vif[event["ref"]]  = event["snapshot"]
                                    elif event["class"] == "sr":
                                        self.filter_uuid = event['snapshot']['uuid']
                                        self.all_storage[event["ref"]]  = event["snapshot"]
                                        self.treestore.foreach(self.update_storage_status, "")
                                        if event["operation"] == "del":
                                            self.filter_uuid = event['snapshot']['uuid']
                                            gobject.idle_add(lambda: self.treestore.foreach(self.delete_storage, "") and False)
                                        if event["operation"] == "add":
                                            sr = event["ref"]
                                            # FIXME
                                            host = self.all_hosts.keys()[0]
                                            if self.poolroot:
                                                #iter_ref = self.treestore.append(self.poolroot, [\
                                                gobject.idle_add(lambda: self.treestore.append(self.poolroot, [\
                                                   gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png"),\
                                                   self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                                                   "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None]) and False)
                                            else:
                                                #iter_ref = self.treestore.append(self.hostroot[host], [\
                                                 gobject.idle_add(lambda: self.treestore.append(self.hostroot[host], [\
                                                   gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png"),\
                                                   self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                                                   "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None]) and False)

                                    elif event["class"] == "pool":
                                        if self.all_pools[event["ref"]]['name_label'] != event["snapshot"]["name_label"]:
                                            if self.poolroot:
                                                gobject.idle_add(lambda: self.wine.treestore.remove(self.poolroot) and False)
                                            else:
                                                for host_ref in self.hostroot.keys():
                                                    gobject.idle_add(lambda: self.wine.treestore.remove(self.hostroot[host_ref]) and False)

                                            self.sync()
                                        if self.all_pools[event["ref"]]['default_SR'] != event["snapshot"]["default_SR"]:
                                            self.treestore.foreach(self.update_default_sr, \
                                                   [self.all_pools[event["ref"]]['default_SR'], event["snapshot"]["default_SR"]])
                                        self.all_pools[event["ref"]]  = event["snapshot"]
                                        if self.wine.selected_type == "pool":
                                            self.update_tab_pool_general(self.wine.selected_ref, self.wine.builder)
                                    elif event["class"] == "message":
                                       if event["operation"] == "del":
                                           del self.all_messages[event["ref"]]
                                       elif event["operation"] == "add":
                                           self.all_messages[event["ref"]] = event["snapshot"]
                                           self.add_alert(event["snapshot"], event["ref"], 
                                                   self.wine.listalerts)
                                           self.wine.update_n_alerts()
                                       else:
                                           print event
                                    elif event["class"] == "vm_guest_metrics":
                                        self.all_vm_guest_metrics[event["ref"]] = event["snapshot"] 
                                    elif event["class"] == "network":
                                        if event["operation"] == "del":
                                            del self.all_network[event["ref"]]
                                        else:
                                            self.all_network[event["ref"]] = event["snapshot"] 
                                        if self.wine.selected_tab == "HOST_Network":
                                            gobject.idle_add(lambda: self.wine.update_tab_host_network() and False)
                                    elif event["class"] == "vlan":
                                       if event["operation"] == "del":
                                           if event["ref"] in self.all_vlan:
                                               del self.all_vlan[event["ref"]]
                                       self.all_vlan[event["ref"]] = event["snapshot"] 

                                    elif event["class"] == "host":
                                       if event["operation"] == "del":
                                           self.filter_uuid = event['snapshot']['uuid']
                                           self.treestore.foreach(self.delete_host, "")
                                           del self.all_hosts[event["ref"]]

                                       elif event["operation"] == "add":
                                           self.all_hosts[event["ref"]] = event["snapshot"] 
                                           self.wine.show_error_dlg("Host added, please reconnect for sync all info")
                                       else:
                                           self.filter_uuid = event['snapshot']['uuid']
                                           self.all_hosts[event["ref"]] = event["snapshot"] 
                                           self.treestore.foreach(self.update_host_status, "")
                                    elif event["class"] == "pif_metrics":
                                        self.all_pif_metrics[event["ref"]] = event["snapshot"] 
                                    elif event["class"] == "host_metrics":
                                        self.all_host_metrics[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "vbd_metrics":
                                        self.all_vbd_metrics[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "vif_metrics":
                                        self.all_vif_metrics[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "vm_metrics":
                                        self.all_vm_metrics[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "console":
                                        self.all_console[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "host_patch":
                                        if event["operation"] == "del":
                                           del self.all_host_patch[event["ref"]]
                                        else:
                                           self.all_host_patch[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "pool_patch":
                                        if event["operation"] == "del":
                                           del self.all_pool_patch[event["ref"]]
                                        else:
                                           self.all_pool_patch[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "pbd":
                                        self.all_pbd[event["ref"]] = event["snapshot"]
                                        if event["operation"] == "add":
                                            sr = event["snapshot"]["SR"]
                                            host = event["snapshot"]["host"]
                                            gobject.idle_add(lambda: self.treestore.insert_after(self.hostroot[host], self.last_storage_iter, [\
                                               gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png"),\
                                               self.all_storage[sr]['name_label'], self.all_storage[sr]['uuid'],\
                                               "storage", None, self.host, sr, self.all_storage[sr]['allowed_operations'], None]) and False)
                                    elif event["class"] == "host_cpu":
                                        self.all_host_cpu[event["ref"]] = event["snapshot"]
                                    else:
                                        print event["class"] + " => ",event
            except socket, msg:
                self.halt = True
                # FIXME TODO
                # Disconnect
            except:
                print "Unexpected error:", sys.exc_info()
                print traceback.print_exc()
                
        print "Exiting event loop"


    def update_default_sr(self, model, path, iter_ref, user_data):
        """
        user_data contains:
        [0] -> old default sr
        [1] -> new default sr
        """
        sr = self.treestore.get_value(iter_ref, 6)
        if sr == user_data[0]:
            gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png")) and False)
        if sr == user_data[1]:
            gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_default_16.png")) and False)
            self.default_sr = sr
        if sr == user_data[0] or sr == user_data[1]:
            if len(self.all_storage[sr]['PBDs']) == 0:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_detached_16.png")) and False)
            broken = False
            for pbd_ref in self.all_storage[sr]['PBDs']:
                if not self.all_pbd[pbd_ref]['currently_attached']:
                    broken = True
                    gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_broken_16.png")) and False)
            if not broken:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png")) and False)

    def update_vm_status(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            vm =  self.all_vms[self.vm_filter_uuid()]
            if not self.all_vms[self.vm_filter_uuid()]["is_a_template"]:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  1, \
                   vm['name_label']) and False)
                if len(self.all_vms[self.vm_filter_uuid()]["current_operations"]):
                    gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, \
                       gtk.gdk.pixbuf_new_from_file("images/tree_starting_16.png")) and False)
                else:
                    gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, \
                       gtk.gdk.pixbuf_new_from_file("images/tree_%s_16.png" % \
                       vm['power_state'].lower())) and False)
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  4, \
                   vm['power_state']) and False)
                self.wine.selected_state = vm['power_state']
                self.wine.selected_actions = vm['allowed_operations']
            else:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  1, \
                   vm['name_label']) and False)
                   
            if self.wine.selected_ref == self.treestore.get_value(iter_ref, 6):
                gobject.idle_add(lambda: self.wine.update_tabs() and False)
                gobject.idle_add(lambda: self.wine.builder.get_object("headimage").set_from_pixbuf(self.treestore.get_value(iter_ref, 0)) and False)
                gobject.idle_add(lambda: self.wine.builder.get_object("headlabel").set_label(self.treestore.get_value(iter_ref,  1)) and False)

    def update_storage_status(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            storage = self.all_storage[self.storage_filter_uuid()]
            gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  1, \
               storage['name_label']
               ) and False)
            if self.wine.selected_ref == self.treestore.get_value(iter_ref, 6):
                gobject.idle_add(lambda: self.wine.update_tabs() and False)
                gobject.idle_add(lambda: self.wine.builder.get_object("headimage").set_from_pixbuf(self.treestore.get_value(iter_ref, 0)) and False)
                gobject.idle_add(lambda: self.wine.builder.get_object("headlabel").set_label(self.treestore.get_value(iter_ref,  1)) and False)
            sr = self.treestore.get_value(iter_ref, 6)
            if len(self.all_storage[sr]['PBDs']) == 0:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_detached_16.png")) and False)
            broken = False
            for pbd_ref in self.all_storage[sr]['PBDs']:
                if not self.all_pbd[pbd_ref]['currently_attached']:
                    broken = True
                    gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_broken_16.png")) and False)
            if not broken:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png")) and False)

    def delete_storage(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            self.treestore.remove(iter_ref)

    def update_host_status(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
                if self.treestore.get_value(iter_ref, 1):
                    host = self.all_hosts[self.host_filter_uuid()]
                    gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  1, \
                       host['name_label']
                       ) and False)
                    if host["enabled"]:
                        gobject.idle_add(lambda: self.treestore.set_value(iter_ref, 0,  gtk.gdk.pixbuf_new_from_file("images/tree_connected_16.png")) and False)
                    else:
                        gobject.idle_add(lambda: self.treestore.set_value(iter_ref, 0,  gtk.gdk.pixbuf_new_from_file("images/tree_disabled_16.png")) and False)
                    gobject.idle_add(lambda: self.wine.update_tabs() and False)
                    gobject.idle_add(lambda: self.wine.update_toolbar() and False)
                    gobject.idle_add(lambda: self.wine.update_menubar()  and False)
                    gobject.idle_add(lambda: self.wine.builder.get_object("headimage").set_from_pixbuf(self.treestore.get_value(iter_ref, 0)) and False)
                    gobject.idle_add(lambda: self.wine.builder.get_object("headlabel").set_label(self.treestore.get_value(iter_ref,  1)) and False)

    def delete_host(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            gobject.idle_add(lambda: self.treestore.remove(iter_ref) and False)
            gobject.idle_add(lambda: self.wine.update_tabs() and False)

    def log_filter_uuid(self, item):
        return item["obj_uuid"] == self.filter_uuid   

    def task_filter_uuid(self, item_ref):
        if item_ref in self.all_tasks:
            item = self.all_tasks[item_ref]
            if item_ref in self.track_tasks:
                if self.track_tasks[item_ref] in self.all_vms:
                    return self.all_vms[self.track_tasks[item_ref]]["uuid"] == self.filter_uuid   
                    #return True
            if "ref" in item and item["ref"] in self.track_tasks and self.track_tasks[item["ref"]] in self.all_vms:
                return self.all_vms[self.track_tasks[item["ref"]]]["uuid"] == self.filter_uuid   
            else:
                if "resident_on" in item:
                    return item["resident_on"] == self.filter_ref
                if "uuid" in item:
                    self.get_task_ref_by_uuid(item["uuid"])
            return False
        
    def get_task_ref_by_uuid(self, uuid):
            for task in self.tasks.keys():
                if "uuid" in self.tasks[task]:
                    if uuid == self.tasks[task]["uuid"]:
                        return task
                else:
                    print self.tasks[task]

    def filter_vif_ref(self, item):
        return item["VM"] == self.filter_ref

    def filter_vbd_ref(self, item):
        return item["VM"] == self.filter_ref

    def filter_vbd_uuid(self, uuid):
        for vbd in self.all_vbd:    
            if self.all_vbd[vbd]["uuid"] == uuid:
                return vbd 
        return None

    def filter_vm_uuid(self, item):
        return item["uuid"] == self.filter_uuid   

    def vm_filter_uuid(self):
        for vm in self.all_vms:
           if self.all_vms[vm]["uuid"] == self.filter_uuid:
               return vm   
        return None

    def storage_filter_uuid(self):
        for stg in self.all_storage:
           if self.all_storage[stg]["uuid"] == self.filter_uuid:
               return stg   
        return None

    def host_filter_uuid(self):
        for host in self.all_hosts:
           if self.all_hosts[host]["uuid"] == self.filter_uuid:
               return host
        return None

    def filter_custom_template(self, item):
        if not item["is_a_template"]:
            return False
        if  item["name_label"][:7] == "__gui__":
            return False
        if item["last_booted_record"] != "":
            return True 
        return False
    def filter_normal_template(self, item):
        if not item["is_a_template"]:
            return False
        elif  item["name_label"][:7] == "__gui__":
            return False
        elif item["last_booted_record"] == "":
            return True 
        return False
    def filter_vdi_ref(self):
        for vdi in self.all_vdi.keys():
            if vdi == self.filter_vdi:
                return vdi
    def search_in_liststore(self, list, ref, field):
        """
        Function retrns iter of element found or None
        """
        print list.__len__()
        for i in range(0, list.__len__()):
            iter_ref = list.get_iter((i,))
            print list.get_value(iter_ref, field)
            if ref == list.get_value(iter_ref, field):
                return iter_ref 
        return None
