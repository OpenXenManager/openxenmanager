# -----------------------------------------------------------------------
# OpenXenManager
#
# Copyright (C) 2009 Alberto Gonzalez Rodriguez alberto@pesadilla.org
# Copyright (C) 2011 Cheng Sun <chengsun9@gmail.com>
# Copyright (C) 2014 Daniel Lintott <daniel@serverb.co.uk>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#  USA.
#
# -----------------------------------------------------------------------
# System Imports
import httplib
import xml.dom.minidom
import traceback
from datetime import datetime
import time
import urllib
import socket
import ssl

# Local Imports
from messages import get_msg
from oxcSERVER_vm import *
from oxcSERVER_host import *
from oxcSERVER_properties import *
from oxcSERVER_storage import *
from oxcSERVER_alerts import *
from oxcSERVER_addserver import *
from oxcSERVER_newvm import *
from oxcSERVER_menuitem import *
from pygtk_chart import line_chart
from rrd import RRD, XPORT
import put
import rrdinfo
import utils


class oxcSERVER(oxcSERVERvm, oxcSERVERhost, oxcSERVERproperties,
                oxcSERVERstorage, oxcSERVERalerts, oxcSERVERaddserver,
                oxcSERVERnewvm, oxcSERVERmenuitem):
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

    def __init__(self, host, user, password, wine, use_ssl=False,
                 verify_ssl=False, port=80):
        super(oxcSERVER, self).__init__()
        self.host = host
        self.hostname = host
        self.wine = wine
        self.user = user
        self.password = password
        self.ssl = use_ssl
        self.verify_ssl = verify_ssl
        self.port = port

        self.dbg_track_num = 0

        if not verify_ssl and hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context

    def logout(self):
        self.halt_search = True
        self.halt = True
        if self.is_connected:
            self.connection.event.unregister(self.session_uuid, ["*"])
            self.connection.session.logout(self.session_uuid)
            self.is_connected = False

    def is_vm_running(self, ref):
        """
        Returns True is a VM is running
        :param ref: VM Ref
        :return: Boolean
        """
        if self.all['vms'][ref]['power_state'] == 'Running':
            return True
        else:
            return False

    def get_network_relation(self, ref, show_halted_vms):
        # Get network -> VM relation
        relation = {}
        for network in self.all['network']:
            network_name = self.all['network'][network]['name_label'].replace(
                'Pool-wide network associated with eth', 'Network ')
            vms = []
            for vif in self.all['network'][network]['VIFs']:
                vm = self.all['VIF'][vif]['VM']
                if not vms.count(vm + "_" + self.all['vms'][vm]['name_label']):
                    if show_halted_vms or self.is_vm_running(vm):
                        vms.append(vm + "_" + self.all['vms'][vm]['name_label'])
            relation[network + "_" + network_name] = vms

        return relation

    def get_storage_relation(self, ref, show_halted_vms):
        # Get network -> VM relation
        relation = {}
        for storage in self.all['SR']:
            storage_name = self.all['SR'][storage]['name_label']
            vms = []
            for vdi in self.all['SR'][storage]['VDIs']:
                vbds = self.all['VDI'][vdi]['VBDs']
                for vbd in vbds:
                    vm = self.all['VBD'][vbd]['VM']
                    if not vms.count(vm + "_" +
                                     self.all['vms'][vm]['name_label']):
                        if show_halted_vms or self.is_vm_running(vm):
                            vms.append(vm + "_" +
                                       self.all['vms'][vm]['name_label'])
            relation[storage + "_" + storage_name] = vms

        return relation

    def get_seconds(self, to_convert):
        converted = self.format_date(to_convert)
        to_time = int(time.mktime(converted.timetuple()))
        return to_time

    @staticmethod
    def format_date(to_convert):
        converted = datetime.strptime(str(to_convert), "%Y%m%dT%H:%M:%SZ")
        return converted

    def get_seconds_difference_reverse(self, to_convert):
        converted = self.format_date(to_convert)
        now_time = datetime.now()
        time_diff = (converted - now_time).total_seconds() - 3600
        return time_diff

    def get_seconds_difference(self, to_convert):
        converted = self.format_date(to_convert)
        now_time = datetime.now()
        time_diff = (now_time - converted).total_seconds() - 3600
        return time_diff

    def get_dmesg(self, ref):
        return self.connection.host.dmesg(self.session_uuid, ref)["Value"]

    def restore_server(self, ref, filename, name):
        # <?xml version="1.0"?><methodCall><methodName>task.create</methodName>
        # <params><param><value><string>OpaqueRef:149c1416-9934-3955-515a-d644a
        # addc38f</string></value></param><param><value><string>uploadTask
        # </string></value></param><param><value><string>http://83.165.161.223
        # /host_restore?session_id=OpaqueRef:149c1416-9934-3955-515a-d644aaddc
        # 38f</string></value></param></params></methodCall>
        task_uuid = self.connection.task.create(self.session_uuid,
                                                "Restoring Server",
                                                "Restoring Server %s from "
                                                "%s " % (name, filename))
        self.track_tasks[task_uuid['Value']] = "Restore.Server"
        # size=os.stat(file)[6]

        fp = open(filename, 'rb')
        url = self.wine.selected_ip
        put.putfile(fp, 'https://' + url +
                    '/host_restore?session_id=%s&task_id=%s&dry_run=true' %
                    (self.session_uuid, task_uuid['Value']))
        fp.close()

    def save_screenshot(self, ref, filename):
        url = "https://" + self.wine.selected_ip + \
              '/vncsnapshot?session_id=%s&ref=%s' % (self.session_uuid, ref)
        urllib.urlretrieve(url, filename)

    def pool_backup_database(self, ref, filename, name):
        task_uuid = self.connection.task.create(
            self.session_uuid, "Backup Pool database",
            "Backing up database pool " + name)
        self.track_tasks[task_uuid['Value']] = "Backup.Pool"
        url = "https://" + self.wine.selected_ip + \
              '/pool/xmldbdump?session_id=%s&task_id=%s' % \
              (self.session_uuid, task_uuid['Value'])
        urllib.urlretrieve(url, filename)

    def pool_restore_database(self, ref, filename, name, dry_run="true"):
        task_uuid = self.connection.task.create(
            self.session_uuid, "Restore Pool database",
            "Restoring database pool " + filename)
        self.track_tasks[task_uuid['Value']] = "Restore.Pool"

        size = os.path.getsize(filename)
        url = self.wine.selected_ip
        fp = open(filename, 'r')
        put.putfile(fp, 'https://' + url +
                    '/pool/xmldbdump?session_id=%s&task_id=%s&dry_run=%s' %
                    (self.session_uuid, task_uuid['Value'], dry_run))
        fp.close()

    def host_download_logs(self, ref, filename, name):
        task_uuid = self.connection.task.create(
            self.session_uuid, "Downloading host logs",
            "Downloading logs from host " + name)
        self.track_tasks[task_uuid['Value']] = "Download.Logs"
        url = "https://" + self.wine.selected_ip + \
              '/host_logs_download?session_id=%s&sr_id=%s&task_id=%s' % \
              (self.session_uuid, ref, task_uuid['Value'])
        urllib.urlretrieve(url, filename)

    def host_download_status_report(self, ref, refs, filename, name):
        task_uuid = self.connection.task.create(
            self.session_uuid, "Downloading status report",
            "Downloading status report from host " + name)
        self.track_tasks[task_uuid['Value']] = self.host_vm[ref][0]
        url = "https://" + self.wine.selected_ip + \
              '/system-status?session_id=%s&entries=%s&task_id=%s' \
              '&output=tar' % (self.session_uuid, refs, task_uuid['Value'])
        urllib.urlretrieve(url, filename)

    def backup_server(self, ref, filename, name):
        task_uuid = self.connection.task.create(
            self.session_uuid, "Backup Server", "Backing up server " + name)
        self.track_tasks[task_uuid['Value']] = "Backup.Server"
        url = "https://" + self.wine.selected_ip + \
              '/host_backup?session_id=%s&sr_id=%s&task_id=%s' % \
              (self.session_uuid, ref, task_uuid['Value'])
        urllib.urlretrieve(url, filename)

    def import_vm(self, ref, filename):
        task_uuid = self.connection.task.create(
            self.session_uuid, "Importing VM", "Importing VM " + filename)
        self.track_tasks[task_uuid['Value']] = "Import.VM"

        size = os.stat(filename)[6]
        url = self.wine.selected_ip
        fp = open(filename, 'r')
        put.putfile(fp, 'https://' + url +
                    '/import?session_id=%s&sr_id=%s&task_id=%s' %
                    (self.session_uuid, ref, task_uuid['Value']))
        fp.close()

    def add_alert(self, message, ref, list):
        if message['cls'] == "Host":
            msg = get_msg(message['name'])
            if msg:
                parent = list.prepend(None,
                                      [gtk.gdk.pixbuf_new_from_file(
                                          utils.image_path("info.gif")),
                                       self.hostname, msg['header'],
                                       str(self.format_date(
                                           str(message['timestamp']))),
                                       ref, self.host])
                list.prepend(parent, [None, "", msg['detail'] % self.hostname,
                                      "", ref, self.host])
            else:
                parent = list.prepend(None,
                                      [gtk.gdk.pixbuf_new_from_file(
                                          utils.image_path("info.gif")),
                                       self.hostname, message['name'],
                                       str(self.format_date(
                                           str(message['timestamp']))),
                                       ref, self.host])
                list.prepend(parent, [None, "", message['name'], "", ref,
                                      self.host])
        elif message['name'] == "ALARM":
            vm = self.vm_filter_uuid(message['obj_uuid'])
            if vm not in self.all['vms']:
                return None
            if not self.all['vms'][vm]['is_control_domain']:
                value = message['body'].split("\n")[0].split(" ")[1]
                dom = xml.dom.minidom.parseString(
                    message['body'].split("config:")[1][1:])
                nodes = dom.getElementsByTagName("name")
                # alert = message['body'].split('value="')[1].split('"')[0]
                alert = nodes[0].attributes.getNamedItem("value").value
                nodes = dom.getElementsByTagName("alarm_trigger_level")
                level = nodes[0].attributes.getNamedItem("value").value
                nodes = dom.getElementsByTagName("alarm_trigger_period")
                period = nodes[0].attributes.getNamedItem("value").value

                msg = get_msg('alert_' + alert)
                if msg:
                    parent = list.prepend(None,
                                          [gtk.gdk.pixbuf_new_from_file(
                                              utils.image_path("warn.gif")),
                                           self.hostname, msg['header'],
                                           str(self.format_date(
                                               str(message['timestamp']))),
                                           ref, self.host])
                    list.prepend(parent, [None, "", msg['detail'] %
                                          (self.all['vms'][vm]['name_label'],
                                           float(value)*100, int(period),
                                           float(level)*100), "", ref,
                                          self.host])
                else:
                    print message['name']
                    print message['body']
            else:
                value = message['body'].split("\n")[0].split(" ")[1]
                alert = message['body'].split('value="')[1].split('"')[0]
                msg = get_msg('host_alert_' + alert)
                if msg:
                    parent = list.prepend(
                        None,
                        [gtk.gdk.pixbuf_new_from_file(
                            utils.image_path("warn.gif")),
                         self.hostname, msg['header'] % "Control Domain",
                         str(self.format_date(str(message['timestamp']))),
                         ref, self.host])
                    list.prepend(parent, [None, "", msg['detail'] %
                                          ("Control Domain", self.hostname,
                                           float(value)), "", ref, self.host])
                else:
                    print message['name']
                    print message['body']

    def add_vm_to_tree(self, vm):
        if self.all['vms'][vm]['resident_on'] != "OpaqueRef:NULL" \
                and self.all['vms'][vm]['resident_on'] in self.hostroot:
            resident = self.all['vms'][vm]['resident_on']
            self.treestore.prepend(self.hostroot[resident], [
                gtk.gdk.pixbuf_new_from_file(
                    utils.image_path("tree_%s_16.png" %
                                     self.all['vms'][vm]['power_state'].lower())),
                self.all['vms'][vm]['name_label'], self.all['vms'][vm]['uuid'],
                "vm", self.all['vms'][vm]['power_state'], self.host,
                vm, self.all['vms'][vm]['allowed_operations'],
                self.all['host'][resident]['address']])

        elif self.all['vms'][vm]['affinity'] != "OpaqueRef:NULL" \
                and self.all['vms'][vm]['affinity'] in self.hostroot:
            affinity = self.all['vms'][vm]['affinity']
            self.treestore.prepend(self.hostroot[affinity], [
                gtk.gdk.pixbuf_new_from_file(
                    utils.image_path("tree_%s_16.png" %
                                     self.all['vms'][vm]['power_state'].lower())),
                self.all['vms'][vm]['name_label'], self.all['vms'][vm]['uuid'], "vm",
                self.all['vms'][vm]['power_state'], self.host, vm,
                self.all['vms'][vm]['allowed_operations'],
                self.all['host'][affinity]['address']])
        else:
            if self.poolroot:
                self.treestore.prepend(self.poolroot, [
                    gtk.gdk.pixbuf_new_from_file(
                        utils.image_path(
                            "tree_%s_16.png" %
                            self.all['vms'][vm]['power_state'].lower())),
                    self.all['vms'][vm]['name_label'], self.all['vms'][vm]['uuid'],
                    "vm", self.all['vms'][vm]['power_state'], self.host,
                    vm, self.all['vms'][vm]['allowed_operations'],  self.host])
            else:
                self.treestore.prepend(
                    self.hostroot[self.all['host'].keys()[0]],
                    [gtk.gdk.pixbuf_new_from_file(utils.image_path(
                        "tree_%s_16.png" % self.all['vms'][vm]['power_state'].lower())),
                     self.all['vms'][vm]['name_label'], self.all['vms'][vm]['uuid'],
                     "vm", self.all['vms'][vm]['power_state'], self.host,
                     vm, self.all['vms'][vm]['allowed_operations'], self.host])

    def fill_allowed_operations(self, ref):
        actions = self.connection.VM.get_allowed_operations(self.session_uuid,
                                                            ref)['Value']
        self.all['vms'][ref]['allowed_operations'] = actions
        return actions

    def fill_vm_network(self, ref, tree, list1):
        list1.clear()
        if ref in self.all['vms']:
            guest_metrics = self.all['vms'][ref]['guest_metrics']

            for vif_ref in self.all['vms'][ref]['VIFs']:
                vif = self.all['VIF'][vif_ref]

                # QOS Parameters
                limit = vif['qos_algorithm_params'].get('kbps', '')

                # IP Addresses
                net_addrs = (
                    self.all['VM_guest_metrics'].get(
                        guest_metrics, {'networks': ()}).
                    get('networks', ()))
                addresses = [
                    addr for key, addr in net_addrs.items()
                    if key.startswith(vif['device'] + '/ip')
                ]

                # FIXME - Fix what?
                # Network name
                if vif['network'] in self.all['network']:
                    network = self.all['network'][vif['network']]['name_label'].\
                        replace('Pool-wide network associated with eth',
                                'Network ')
                else:
                    network = ""

                list1.append((vif['device'], vif['MAC'], limit, network,
                             '\n'.join(addresses),
                              str(vif['currently_attached']), vif_ref))
        else:
            print "VM not found %s" % ref

    def set_vif_limit(self, ref, limit, vm_ref):
        qos_algorithm_params = {'kbps': str(limit)}
        res = self.connection.VIF.set_qos_algorithm_params(
            self.session_uuid, ref, qos_algorithm_params)
        if "Value" in res:
            self.track_tasks[res['Value']] = vm_ref
        else:
            print res

    def set_vif_to_manual(self, ref, vm_ref):
        res = self.connection.VIF.set_MAC_autogenerated(self.session_uuid,
                                                        ref, False)
        if "Value" in res:
            self.track_tasks[res['Value']] = vm_ref
        else:
            print res

    def fill_vm_snapshots(self, uuid, tree=None, list=None):
        list.clear()
        if uuid in self.all['vms']:
            all_snapshots = self.all['vms'][uuid]['snapshots']
            for snapshot_uuid in all_snapshots:
                snapshot_name = self.all['vms'][snapshot_uuid]['name_label']
                snapshot_time = self.format_date(
                    self.all['vms'][snapshot_uuid]['snapshot_time'])
                snapshot_of = self.all['vms'][snapshot_uuid]['snapshot_of']
                snapshot_size = 0
                for vbd in self.all['vms'][snapshot_uuid]['VBDs']:
                    vbd_data = self.all['VBD'][vbd]
                    if vbd_data['type'] == 'Disk':
                        snapshot_size += int(self.connection.VDI.get_record(
                            self.session_uuid,
                            vbd_data['VDI'])['Value']['physical_utilisation'])
                list.append([snapshot_uuid, "<b>" + snapshot_name +
                             "</b>\n\nTaken on: " + str(snapshot_time) +
                             "\n\nSize: " + self.convert_bytes(snapshot_size) +
                             "\n\n" + "Used by: " + self.wine.selected_name +
                             "\n"])

    def update_performance(self, uuid, ref, ip, host=False, period=5):
        # Default three hours of period
        self.halt_performance = False

        # TODO: James - Commented this out GUI Has changed
        #for widget in ["scrwin_cpuusage", "scrwin_memusage", "scrwin_netusage", "scrwin_diskusage"]:
        # widget = self.wine.builder.get_object(widget).get_children()[0]
        # if widget.get_children():
        #     gtk.gdk.threads_enter()
        #     widget.remove(widget.get_children()[0])
        #     gtk.gdk.threads_leave()

        if host:
            data_sources = self.connection.host.get_data_sources(self.session_uuid, ref)
        else:
            data_sources = self.connection.VM.get_data_sources(self.session_uuid, ref)
        if "Value" not in data_sources:
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
                    if name not in ("memory_internal_free",
                                    "xapi_free_memory_kib",
                                    "xapi_memory_usage_kib",
                                    "xapi_live_memory_kib") \
                            and name[:6] != "pif___":
                                ds[name[:3]].append([name, desc])
        if host:
            if os.path.exists(os.path.join(self.wine.pathconfig,
                                           "host_rrds.rrd")):
                os.unlink(os.path.join(self.wine.pathconfig, "host_rrds.rrd"))
            urllib.urlretrieve("https://%s/host_rrds?session_id=%s" %
                               (ip, self.session_uuid),
                               os.path.join(self.wine.pathconfig,
                                            "host_rrds.rrd"))
            rrd = RRD(os.path.join(self.wine.pathconfig, "host_rrds.rrd"))
        else:
            if os.path.exists(os.path.join(self.wine.pathconfig,
                                           "vm_rrds.rrd")):
                os.unlink(os.path.join(self.wine.pathconfig, "vm_rrds.rrd"))
            urllib.urlretrieve("https://%s/vm_rrds?session_id=%s&uuid=%s" %
                               (ip, self.session_uuid, uuid),
                               os.path.join(self.wine.pathconfig,
                                            "vm_rrds.rrd"))
            rrd = RRD(os.path.join(self.wine.pathconfig, "vm_rrds.rrd"))
        rrdinfo = rrd.get_data(period)

        def show_tic(value):
            if time.strftime("%S", time.localtime(value)) == "00":
                return time.strftime("%H:%M", time.localtime(value))
            else:
                return ""

        def hovered(chart, graph, (x, y)):
            # print chart.get_title()
            # self.wine.builder.get_object("lblperf" +
            # graph.get_title()[:3].lower()).set_label(
            #    "%s - %s = %0.2f" % (time.strftime("%d/%m %H:%M:%S",
            # time.localtime(x)),  graph.get_title(), y))
            pass

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
            chart[name].legend.set_position(line_chart.POSITION_RIGHT)
            chart[name].set_padding(0)
            chart[name].yaxis.set_label("kBps")
        chart["cpu"].yaxis.set_label("%")
        chart["mem"].yaxis.set_label("MB")

        # CPU Graph
        chart["cpu"].set_yrange((0, 100))
        for key in rrdinfo.keys():
            if key[:3] == "cpu":
                data = rrdinfo[key]["values"]

                for i in range(len(data)):
                    data[i][1] *= 100
                graph[key] = line_chart.Graph(key, key, data)
                graph[key].set_show_title(False)
                chart["cpu"].add_graph(graph[key])

        chart["cpu"].set_size_request(len(data)*20, 250)
        gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_cpuusage").add(chart["cpu"]) and False)
        gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_cpuusage").show_all() and False)

        # Memory
        if "memory_internal_free" in rrdinfo and "memory" in rrdinfo:
            chart["mem"].set_yrange(
                (0, int(rrdinfo["memory"]["max_value"])/1024/1024))
            data = rrdinfo["memory"]["values"]
            data2 = rrdinfo["memory_internal_free"]["values"]
            for i in range(len(data2)):
                data[i][1] = (data[i][1] - data2[i][1]*1024)/1024/1024
            graph["mem"] = line_chart.Graph("Memory used", "Memory used", data)
            graph["mem"].set_show_title(False)
            chart["mem"].add_graph(graph["mem"])
            chart["mem"].set_size_request(len(data)*20, 250)

            gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_memusage").add(chart["mem"]) and False)
            gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_memusage").show_all() and False)
        elif "memory_total_kib" in rrdinfo \
                and "xapi_free_memory_kib" in rrdinfo:
            chart["mem"].set_yrange(
                (0, int(rrdinfo["memory_total_kib"]["max_value"])/1024/1024))
            data = rrdinfo["memory_total_kib"]["values"]
            data2 = rrdinfo["xapi_free_memory_kib"]["values"]
            for i in range(len(data2)):
                data[i][1] = (data[i][1] - data2[i][1]*1024)/1024/1024
            graph["mem"] = line_chart.Graph("Memory used", "Memory used", data)
            graph["mem"].set_show_title(False)
            chart["mem"].add_graph(graph["mem"])
            chart["mem"].set_size_request(len(data)*20, 250)

            gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_memusage").add(chart["mem"]) and False)
            gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_memusage").show_all() and False)

        else:
            label = gtk.Label()
            label.set_markup("<b>No data available</b>")
            gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_memusage").add(label) and False)
            gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_memusage").show_all() and False)

        # Network
        max_value = 0
        data = None
        for key in rrdinfo.keys():
            if key[:3] == "vif" or key[:3] == "pif":
                data = rrdinfo[key]["values"]
                for i in range(len(data)):
                    data[i][1] /= 1024
                    if data[i][1] > max_value:
                        max_value = data[i][1]
                graph[key] = line_chart.Graph(key, key, data)
                graph[key].set_show_title(False)
                chart["vif"].add_graph(graph[key])
        if data:
            chart["vif"].set_yrange((0, max_value))
            chart["vif"].set_size_request(len(data)*20, 250)

            gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_netusage").add(chart["vif"]) and False)
            gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_netusage").show_all() and False)
        else:
            label = gtk.Label()
            label.set_markup("<b>No data available</b>")
            gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_netusage").add(label) and False)
            gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_netusage").show_all() and False)

        # Disk
        if not host:
            max_value = 0
            data = None
            for key in rrdinfo.keys():
                if key[:3] == "vbd":
                    data = rrdinfo[key]["values"]
                    for i in range(len(data)):
                        data[i][1] /= 1024
                    graph[key] = line_chart.Graph(key, key, data)
                    graph[key].set_show_title(False)
                    chart["vbd"].add_graph(graph[key])
                    if rrdinfo[key]['max_value']/1024 > max_value:
                        max_value = rrdinfo[key]['max_value']/1024

            chart["vbd"].set_yrange((0, max_value))
            chart["vbd"].set_size_request(len(data)*20, 250)
            if data:
                gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_diskusage").add(chart["vbd"]) and False)
                gobject.idle_add(lambda: self.wine.builder.get_object("scrwin_diskusage").show_all() and False)

        if max_value == 0:  # TODO: What's this for?
            max_value = 1
        # TODO: James - disabled this. Maybe reenable it properly
        #gobject.idle_add(lambda: self.wine.adjust_scrollbar_performance() and False)

        time.sleep(5)
        while not self.halt_performance:
            if os.path.exists(os.path.join(self.wine.pathconfig,
                                           "update.rrd")):
                os.unlink(os.path.join(self.wine.pathconfig, "update.rrd"))
            urllib.urlretrieve("https://%s/rrd_updates?session_id=%s&start=%s"
                               "&cf=AVERAGE&interval=5&vm_uuid=%s" %
                               (ip, self.session_uuid, int(time.time())-10,
                                uuid),
                               os.path.join(self.wine.pathconfig,
                                            "update.rrd"))
            rrd = XPORT(os.path.join(self.wine.pathconfig, "update.rrd"))
            rrdinfo = rrd.get_data()

            for key in rrdinfo:
                if key in graph:
                    if rrdinfo[key]['values']:
                        if key[:3] == "cpu":
                            data = rrdinfo[key]["values"]
                            for i in range(len(data)):
                                data[i][1] *= 100

                            graph[key].add_data(data)
                            chart[key[:3]].queue_draw()
                        elif key[:3] == "vif":
                            data = rrdinfo[key]["values"]
                            for i in range(len(data)):
                                data[i][1] /= 1024
                            graph[key].add_data(data)
                            chart[key[:3]].queue_draw()
                        elif key[:3] == "vbd":
                            data = rrdinfo[key]["values"]
                            for i in range(len(data)):
                                data[i][1] /= 1024
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
            gobject.idle_add(lambda: self.wine.builder.get_object(
                "vmtablelog").remove(ch) and False)

        for task_ref in filter(self.task_filter_uuid, self.tasks):
            task = self.all['task'][task_ref]
            if "snapshot" in task:
                self.add_box_log(task['snapshot']['name_label'],
                                 str(task['snapshot']['created']),
                                 "%s %s" % (task["snapshot"]["name_label"],
                                            self.all['vms'][self.track_tasks[task["ref"]]]["name_label"]),
                                 str(task['snapshot']['created']), task['ref'], task,
                                 float(task['snapshot']['progress']), i % 2)  # TODO: Check variable type float vs int
            else:
                if "ref" in task:
                    self.add_box_log(task['name_label'], str(task['created']),
                                     "%s %s" % (task["name_label"],
                                                self.all['vms'][self.track_tasks[task["ref"]]]["name_label"]),
                                     str(task['created']), self.get_task_ref_by_uuid(task['uuid']), task,
                                     float(task['progress']), i % 2)  # TODO: Check variable type float vs int
                else:
                    self.add_box_log(task['name_label'], str(task['created']),
                                     "%s %s" % (task["name_label"], task["name_description"]),
                                     str(task['created']), task_ref, task,
                                     float(task['progress']), i % 2)  # TODO: Check variable type float vs int
                i += 1
        for log in sorted(filter(self.log_filter_uuid, self.all_messages.values()),
                          key=itemgetter("timestamp"), reverse=True):
            timestamp = str(log['timestamp'])
            if thread:
                gobject.idle_add(lambda: self.add_box_log(log['name'], timestamp,
                                                          log['body'], str(log['timestamp']),
                                                          alt=i % 2) and False)
            else:
                self.add_box_log(log['name'], timestamp, log['body'],
                                 str(log['timestamp']), alt=i % 2)
            i += 1

    def add_box_log(self, title, date, description, time, id=None, task=None, progress=0, alt=0):
        date = str(self.format_date(date))
        vboxframe = gtk.Frame()
        vboxframe.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#d5e5f7"))
        if task:
            vboxframe.set_size_request(900, 100)
        else:
            vboxframe.set_size_request(900, 80)
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
        vboxchildlabel3.set_size_request(-1, -1) # x=600
        vboxchildlabel3.set_line_wrap(True)
        vboxchildlabel4 = gtk.Label()
        vboxchildlabel4.set_selectable(True)
        # FIXME
        # vboxchildprogressbar.set_style(1)
        vboxchildlabel2.set_label(date)
        msg = get_msg(title)
        if msg:
            vboxchildlabel1.set_label(msg['header'])
            vboxchildlabel3.set_label(msg['detail'] % self.wine.selected_name)
        else:
            vboxchildlabel1.set_label(title)
            vboxchildlabel3.set_label(description)

        vboxchildlabel1.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))
        # vboxchildlabel4.set_label(time)
        vboxchild.put(vboxchildlabel1, 25, 12)
        vboxchild.put(vboxchildlabel2, 600, 12)
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
            self.vboxchildprogressbar[id].set_size_request(500, 20)
            self.vboxchildprogressbar[id].set_fraction(progress)
            if ("snapshot" in task and (task["snapshot"]["status"] != "failure"
                                        and task["snapshot"]["status"] != "success")) or \
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
                    vboxchildlabel4.set_label("Finished: %s" % str(self.format_date(str(task["finished"]))))

            vboxchild.put(self.vboxchildprogress[id], 25, 72)
            if "snapshot" in task and task["snapshot"]["status"] == "success":
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
        for storage in self.all['SR'].values():
            on_host = False
            for pbd in storage['PBDs']:
                if self.all['PBD'][pbd]['host'] == ref:
                    on_host = True
            # if storage['type'] != "iso":
            if on_host:
                if "physical_size" in storage:
                    if int(storage['physical_size']) > 0:
                        usage = "%d%% (%s used)" % \
                                (((float(storage['physical_utilisation'])/1073741824) /
                                (float(storage['physical_size'])/1073741824) * 100),
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
        """
        Populate the treestore with the XenServer hosts for the HOST_search tab

        :param ref:
        :param list:
        """
        while not self.halt_search:
            gobject.idle_add(lambda: list.clear() and False)
            position = 0
            hosts = {}
            # FIXME: what happen when a pool exists?
            for host in self.all['host'].keys():
                metrics = self.all['host'][host]['metrics']
                memory_free = int(self.all['host_metrics'][metrics]['memory_free'])
                memory_total = int(self.all['host_metrics'][metrics]['memory_total'])
                if memory_total == 0:
                    memory = ""
                    memory_img = 0
                else:
                    memory = str(((memory_total-memory_free)*100)/memory_total) + "% used of " + \
                        self.convert_bytes(memory_total)  # Column 5
                    memory_img = int((((memory_total-memory_free)*100)/memory_total)/10)

                start_time = self.all['host'][host]['other_config']['boot_time'][:-1]
                uptime = self.humanize_time(time.time() - int(start_time))

                # Prepare the variables for the treestore
                img_connected = os.path.join(utils.module_path(), "images/tree_connected_16.png")  # Column 0
                name = "<b>" + self.all['host'][host]['name_label'] + "</b>\n<i>" + \
                       self.all['host'][host]['name_description'] + "</i>"  # Column 1
                load_img = os.path.join(utils.module_path(), "images/usagebar_5.png")  # Column 2
                load_txt = ""  # Column 3
                mem_img = os.path.join(utils.module_path(), "images/usagebar_%s.png" % str(memory_img))  # Column 4
                net_address = self.all['host'][host]['address']

                hosts[host] = position
                gobject.idle_add(lambda item: list.append(None, item) and False,
                                 ([gtk.gdk.pixbuf_new_from_file(img_connected), name,
                                   gtk.gdk.pixbuf_new_from_file(load_img), load_txt,
                                   gtk.gdk.pixbuf_new_from_file(mem_img), memory, "-", "",
                                   net_address, uptime, None]))

                position += 1

            for host in self.all['host'].keys():
                Thread(target=self.fill_vm_search, args=(host, list, hosts)).start()
            for i in range(0, 60):
                if not self.halt_search:
                    time.sleep(1)

    def fill_vm_search(self, host, list, hosts):
        rrd_updates = rrdinfo.RRDUpdates("https://%s/rrd_updates?session_id=%s&"
                                         "start=%d&cf=AVERAGE&interval=5&host=true" %
                                         (self.all['host'][host]["address"], self.session_uuid, time.time()-600))
        rrd_updates.refresh()
        for uuid in rrd_updates.get_vm_list():
            for vm in self.all['vms']:
                if self.all['vms'][vm]["uuid"] == uuid:
                    break
            guest_metrics = self.all['vms'][vm]['guest_metrics']
            ips = []
            with_tools = True
            if guest_metrics != "OpaqueRef:NULL":
                for vif in self.all['vms'][vm]['VIFs']:
                    if "networks" in self.all['VM_guest_metrics'][guest_metrics]:
                        if self.all['VIF'][vif]['device'] + "/ip" in self.all['VM_guest_metrics'][guest_metrics]['networks']:
                            if self.all['VM_guest_metrics'][guest_metrics]['networks'][self.all['VIF'][vif]['device'] + "/ip"]:
                                ips.append(self.all['VM_guest_metrics'][guest_metrics]['networks'][self.all['VIF'][vif]['device'] + "/ip"])
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
                    data = [0]
                    media = 0.0
                    i = 0
                    row = None
                    for row in range(rrd_updates.get_nrows()):
                        value1 = rrd_updates.get_vm_data(uuid, param, row)
                        if value1 != "NaN":
                            data.append(value1)
                            media += value1
                            i += 1
                    if i == 0:
                        i = 1
                    if row:
                        if param.count("cpu") > 0:
                            cpu += 1
                            cpu_pct += int(rrd_updates.get_vm_data(uuid, param, row) * 100)
                        elif param.count("vbd") > 0 and param.count("write"):
                            try:
                                vbd_write_avg += int((media/i)/1024)
                                vbd_write_max += int(max(data)/1024)
                            except:  # TODO: Identify Exception Type
                                vbd_write_avg += 0
                                vbd_write_max += 0
                        elif param.count("vbd") > 0 and param.count("read"):
                            try:
                                vbd_read_avg += int((media/i)/1024)
                                vbd_read_max += int(max(data)/1024)
                            except:  # TODO: Identify Exception Type
                                vbd_read_avg += 0
                                vbd_read_max += 0
                        elif param.count("vif") > 0 and param.count("tx"):
                            try:
                                vif_write_avg += int((media/i)/1024)
                                vif_write_max += int(max(data)/1024)
                            except:  # TODO: Identify Exception Type
                                vif_write_avg += 0
                                vif_write_max += 0
                        elif param.count("vif") > 0 and param.count("rx"):
                            try:
                                vif_read_avg += int((media/i)/1024)
                                vif_read_max += int(max(data)/1024)
                            except:  # TODO: Identify Exception Type
                                vif_read_avg += 0
                                vif_read_max += 0
                        elif param.count("memory_internal_free") > 0:
                            if uuid == "NaN" or param == "NaN" or row == "NaN":
                                print "NaN variables"
                                print "  uuid: " + str(uuid)
                                print "param: " + str(param)
                                print "  row: " + str(row)

                            memory = int(rrd_updates.get_vm_data(uuid, param, row))*1024
                            memory_total = int(self.all['vms'][vm]['memory_dynamic_max'])
                        else:
                            # print str(media/i) + "/" + str(max(data))
                            # print "last: " + str(rrd_updates.get_vm_data(uuid,param,row))
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
                parent = self.all['vms'][vm]['resident_on']
                if parent == "OpaqueRef:NULL":
                    parent = self.all['vms'][vm]['affinity']
                if not self.all['vms'][vm]['is_control_domain']:
                    if self.all['vms'][vm]['metrics'] not in self.all['VM_metrics']:
                        self.all['VM_metrics'][self.all['vms'][vm]['metrics']] = \
                            self.connection.VM_metrics.get_record(self.session_uuid,
                                                                  self.all['vms'][vm]['metrics'])['Value']
                    start_time = self.all['VM_metrics'][self.all['vms'][vm]['metrics']]['start_time']
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
                            gobject.idle_add(lambda parent_path, item: list.append(list.get_iter(parent_path), item)
                                             and False, hosts[parent],
                                             ([gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                            "images/tree_running_16.png")),
                                               self.all['vms'][vm]['name_label'] + "\n<i>" +
                                               self.all['vms'][vm]['name_description'] + "</i>",
                                               gtk.gdk.pixbuf_new_from_file(
                                                   os.path.join(utils.module_path(),
                                                                "images/usagebar_%s.png" % load_img)),
                                               load + "% of " + str(cpu) + " cpus",
                                               gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                            "images/usagebar_%s.png" %
                                                                            abs(int(memory_img)))),
                                               memory_used + "% of " + self.convert_bytes(memory_total),
                                               str(vbd_write_avg) + "/" + str(vbd_write_max) + " | " +
                                               str(vbd_read_avg) + "/" + str(vbd_read_max),
                                               str(vif_write_avg) + "/" + str(vif_write_max) + " | " +
                                               str(vif_read_avg) + "/" + str(vif_read_max),
                                               "\n".join(ips), uptime, None]))
                        else:
                            gobject.idle_add(lambda parent_path, item: list.append(list.get_iter(parent_path), item)
                                             and False, hosts[parent],
                                             ([gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                            "images/tree_running_16.png")),
                                               self.all['vms'][vm]['name_label'] + "\n<i>" +
                                               self.all['vms'][vm]['name_description'] + "</i>",
                                               gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                            "images/usagebar_%s.png" % load_img)),
                                               load + "% of " + str(cpu) + " cpus",
                                               gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                            "images/usagebar_0.png")),
                                               "", "<span foreground='red'><b>XenServer tools</b></span>",
                                               "<span foreground='red'><b>not installed</b></span>", "-",
                                               uptime, None]))
                    else:
                        pass
                        """
                        list.append(None,
                          ([gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                          "images/tree_running_16.png")),
                            self.all['vms'][vm]['name_label'] + "\n<i>" + self.all['vms'][vm]['name_description'] + "</i>",
                            gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                            "images/usagebar_%s.png" % load_img)),
                            load + "% of " + str(cpu) + " cpus",
                            gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                            "images/usagebar_0.png")),
                            "",
                            "<span foreground='red'><b>XenServer tools</b></span>",
                            "<span foreground='red'><b>not installed</b></span>",
                            "-",
                            uptime,
                            None
                         ]))
                        """
                        # print  self.all['vms'][vm]
                else:
                    gobject.idle_add(lambda: list.set(list.get_iter(hosts[parent]), 2,
                                                      gtk.gdk.pixbuf_new_from_file(os.path.join(
                                                          utils.module_path(),
                                                          "images/usagebar_%s.png" % load_img)),
                                                      3,  load + "% of " + str(cpu) + " cpus",
                                                      7, str(vif_write_avg) + "/" + str(vif_write_max) + " | " +
                                                      str(vif_read_avg) + "/" + str(vif_read_max)) and False)
            gobject.idle_add(lambda: self.wine.treesearch.expand_all() and False)

    def fill_local_storage(self, ref, list):
        list.clear()
        """
        for pbd in self.all['SR'][ref]['PBDs']:
            print self.all['PBD'][pbd]
        print "*************"
        """
        if ref in self.all['SR']:
            for vdi in self.all['SR'][ref]['VDIs']:
                pct = (int(self.all['VDI'][vdi]['physical_utilisation'])/int(self.all['VDI'][vdi]['virtual_size']))*100
                if self.all['VDI'][vdi]['VBDs']:
                    vbd = self.all['VBD'][self.all['VDI'][vdi]['VBDs'][0]]
                    vm = self.all['vms'][vbd['VM']]['name_label']
                else:
                    vm = ""
                if self.all['VDI'][vdi]['is_a_snapshot']:
                    vm += " (snapshot)"
                # FIXME
                if self.all['VDI'][vdi]['name_label'] != "base copy":
                    list.append([vdi, self.all['VDI'][vdi]['name_label'],
                                 self.all['VDI'][vdi]['name_description'],
                                 self.convert_bytes(self.all['VDI'][vdi]['virtual_size']) +
                                 " (" + str(pct) + "% on disk)", vm])

    def fill_vm_storage(self, ref, storage_list):
        self.filter_ref = ref
        all_vbds = filter(self.filter_vbd_ref, self.all['VBD'].values())
        storage_list.clear()
        if ref not in self.all['vms']:
            return
        for vbd_ref in self.all['vms'][ref]['VBDs']:
            vbd = self.all['VBD'][vbd_ref]
            if vbd['VDI'] != "OpaqueRef:NULL" and vbd['type'] != "CD":
                if vbd['mode'] == "RW":
                    ro = "False"
                else:
                    ro = "True"
                if vbd['VDI']:
                    self.filter_vdi = vbd['VDI']
                    vdi = self.all['VDI'][self.filter_vdi_ref()]
                    vdi_name_label = vdi['name_label']
                    vdi_name_description = vdi['name_description']
                    vdi_virtual_size = vdi['virtual_size']
                    vdi_sr = vdi['SR']
                    sr_name = self.all['SR'][vdi_sr]['name_label']
                    storage_list.append((vdi_name_label, vdi_name_description,
                                         sr_name, vbd['userdevice'],
                                         self.convert_bytes(vdi_virtual_size),
                                         ro, "0 (Lowest) ",
                                         str(vbd['currently_attached']),
                                         "/dev/" + vbd['device'], vbd['VDI'],
                                         vbd_ref, vbd['bootable']))

    def fill_vm_storage_dvd(self, ref, list):
        i = 0
        active = 0
        self.filter_ref = ref
        all_vbds = filter(self.filter_vbd_ref, self.all['VBD'].values())
        vmvdi = ""
        for vbd in all_vbds:
            if vbd['type'] == "CD":
                vmvdi = vbd['VDI']
        list.clear()
        list.append(["<empty>", "empty", True, True])
        list.append(["DVD drives", "", False, True])
        for sr in self.all['SR']:
            if self.all['SR'][sr]['type'] == "udev" and self.all['SR'][sr]['sm_config']["type"] == "cd":
                if len(self.all['SR'][sr]['VDIs']):
                    i += 1
                    if self.all['SR'][sr]['VDIs'][0] == vmvdi:
                            active = i
                    if self.all['SR'][sr]['VDIs'][0] in self.all['VDI']:
                        info = self.all['VDI'][self.all['SR'][sr]['VDIs'][0]]
                        list.append(["\tDVD Drive " + info['location'][-1:],
                                     self.all['SR'][sr]['VDIs'][0], True, False])
                    else:
                        list.append(["\tDVD Drive",  self.all['SR'][sr]['VDIs'][0], True, False])
        for sr in self.all['SR']:
            if self.all['SR'][sr]['type'] == "iso":

                list.append([self.all['SR'][sr]['name_label'], sr, False, True])
                i += 1
                isos = {}
                for vdi in self.all['SR'][sr]['VDIs']:
                    isos[str(self.all['VDI'][vdi]['name_label'])] = vdi
                for vdi_ref in sorted(isos):
                    vdi = isos[vdi_ref]
                    list.append(["\t" + self.all['VDI'][vdi]['name_label'], vdi, True, False])
                    i += 1
                    if vdi == vmvdi:
                        active = i
        if active == 0:
            return active
        else:
            return active + 1

    def update_tab_storage(self, ref, builder):
        labels = {}
        labels['lblstgname'] = self.all['SR'][ref]['name_label']
        labels['lblstgdescription'] = self.all['SR'][ref]['name_description']
        labels['lblstgtags'] = ", ".join(self.all['SR'][ref]['tags'])
        stg_other_config = self.all['SR'][ref]['other_config']
        if "folder" in stg_other_config:
            labels['lblstgfolder'] = stg_other_config['folder']
        else:
            labels['lblstgfolder'] = "<None>"
        labels['lblstgtype'] = self.all['SR'][ref]['type'].upper()
        labels['lblstgsize'] = "%s used of %s total (%s allocated)" % \
                               (self.convert_bytes(self.all['SR'][ref]['physical_utilisation']),
                                self.convert_bytes(self.all['SR'][ref]['physical_size']),
                                self.convert_bytes(self.all['SR'][ref]['virtual_allocation']))

        if "devserial" in self.all['SR'][ref]['sm_config']:
            devserial = self.all['SR'][ref]['sm_config']['devserial'].split("-", 2)
            labels['lblstgserial'] = devserial[0].upper() + " ID:"
            if len(devserial) > 1:
                    labels['lblstgscsi'] = devserial[1]
            else:
                labels['lblstgscsi'] = devserial[0]
        else:
            labels['lblstgscsi'] = ""

        broken = False
        # Fix using PBD and "currently_attached"
        if len(self.all['SR'][ref]['PBDs']) == 0:
            broken = True
            labels['lblstgstate'] = "<span foreground='red'><b>Detached</b></span>"
            labels['lblstghostcon'] = "<span foreground='red'><b>Connection Missing</b></span>"
        else:
            broken = False
            for pbd_ref in self.all['SR'][ref]['PBDs']:
                if not self.all['PBD'][pbd_ref]['currently_attached']:
                    labels['lblstgstate'] = "<span foreground='red'><b>Broken</b></span>"
                    labels['lblstghostcon'] = "<span foreground='red'><b>Unplugged</b></span>"
                    broken = True
        if not broken:
            if len(self.all['SR'][ref]['PBDs']) > 0:
                labels['lblstgstate'] = "<span foreground='green'><b>OK</b></span>"
                labels['lblstghostcon'] = "Connected"
            """
            elif len(self.all['SR'][ref]['PBDs']) > 0:
                labels['lblstgstate'] = "<span foreground='red'><b>Dettached</b></span>"
                labels['lblstghostcon'] = "<span foreground='red'><b>Connection Missing</b></span>"
            """
        labels['lblstghost'] = self.wine.selected_host
        if len(self.all['SR'][ref]['PBDs']) == 0:
            labels['lblstgmultipath'] = "No"
        else:
            pbd = self.all['PBD'][self.all['SR'][ref]['PBDs'][0]]
            if "multipathed" in pbd['other_config'] and pbd['other_config']["multipathed"] == "true":
                if "SCSIid" in pbd['device_config']:
                    #{'uuid': '232b7d15-d8cb-e183-3838-dfd33f6bd597', 'SR': 'OpaqueRef:1832f6e1-73fa-b43d-fcd2-bac969abf867', 'other_config': {'mpath-3600a0b8000294d50000045784b85e36f': '[1, 1, -1, -1]', 'multipathed': 'true'}, 'host': 'OpaqueRef:5c0a69d1-7719-946b-7f3c-683a7058338d', 'currently_attached': True, 'device_config': {'SCSIid': '3600a0b8000294d50000045784b85e36f'}}
                    scsiid = pbd['device_config']["SCSIid"]
                    paths = eval(pbd["other_config"]["mpath-" + scsiid])
                    if paths[0] == paths[1]:
                        labels['lblstgmultipath'] = "<span foreground='green'>%s of %s paths active</span>" % \
                                                    (paths[0], paths[1])
                    else:
                        labels['lblstgmultipath'] = "<span foreground='red'>%s of %s paths active</span>" % \
                                                    (paths[0], paths[1])
                else:
                    labels['lblstgmultipath'] = "Yes"
            else:
                labels['lblstgmultipath'] = "No"

        for label in labels.keys():
            builder.get_object(label).set_label(labels[label])

    def is_storage_broken(self, ref):
        for pbd_ref in self.all['SR'][ref]['PBDs']:
            if not self.all['PBD'][pbd_ref]['currently_attached']:
                return True
        return False

    def update_tab_template(self, ref, builder):
        labels = {}
        labels['lbltplname'] = self.all['vms'][ref]['name_label']
        labels['lbltpldescription'] = self.all['vms'][ref]['name_description']
        if not self.all['vms'][ref]['HVM_boot_policy']:
            labels['lbltplboot'] = "Boot order:"
            labels["lbltplparameters"] = self.all['vms'][ref]['PV_args']
        else:
            labels['lbltplboot'] = "OS boot parameters:"
            labels['lbltplparameters'] = ""
            for param in list(self.all['vms'][ref]['HVM_boot_params']['order']):
                    if param == 'c':
                        labels['lbltplparameters'] += "Hard Disk\n"
                    elif param == 'd':
                        labels['lbltplparameters'] += "DVD-Drive\n"
                    elif param == 'n':
                        labels['lbltplparameters'] += "Network\n"

        other_config = self.all['vms'][ref]['other_config']
        if "folder" in other_config:
            labels['lbltplfolder'] = other_config['folder']
        else:
            labels['lbltplfolder'] = "<None>"

        labels["lbltplmemory"] = self.convert_bytes(self.all['vms'][ref]['memory_dynamic_max'])

        if self.all['vms'][ref]['tags']:
            labels["lbltpltags"] = ", ".join(self.all['vms'][ref]['tags'])
        else:
            labels["lbltpltags"] = "<None>"

        labels["lbltplcpu"] = self.all['vms'][ref]['VCPUs_at_startup']
        if "auto_poweron" in other_config and other_config["auto_poweron"] == "true":
            labels["lbltplautoboot"] = "Yes"
        else:
            labels["lbltplautoboot"] = "No"

        priority = self.all['vms'][ref]["VCPUs_params"]
        if "weight" in priority:
            # labels["lbltplpriority"] = priority['weight']
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

        # FIXME
        # labels["lblvmstartup"] =  str(self.connection.VM_metrics.get_start_time(self.session_uuid,metric)['Value'])
        metric = self.all['vms'][ref]['metrics']
        if metric not in self.all['VM_metrics']:
            res = self.connection.VM_metrics.get_record(self.session_uuid, ref)
            if "Value" in res:
                self.all['VM_metrics'][ref] = res["Value"]

        for label in labels.keys():
            builder.get_object(label).set_label(labels[label])
        pass

    def update_tab_host_general(self, ref, builder):
        labels = {}
        software_version = self.all['host'][ref]['software_version']
        license_params = self.all['host'][ref]['license_params']
        labels['lblhostname'] = self.all['host'][ref]['name_label']
        labels['lblhostdescription'] = self.all['host'][ref]['name_description']
        if len(self.all['host'][ref]['tags']) == 0:
            labels['lblhosttags'] = '<None>'
        else:
            labels['lblhosttags'] = ", ".join(self.all['host'][ref]['tags'])
        host_other_config = self.all['host'][ref]['other_config']
        if "folder" in host_other_config:
            labels['lblhostfolder'] = host_other_config['folder']
        else:
            labels['lblhostfolder'] = '<None>'
        # FIXME
        if "iscsi_iqn" in host_other_config:
            labels['lblhostiscsi'] = host_other_config['iscsi_iqn']
        else:
            labels['lblhostiscsi'] = ""
        # FIXME
        labels['lblhostpool'] = ""
        # str(self.connection.session.get_pool(
        #             self.session_uuid, self.session['Value'])['Value'])
        logging = self.all['host'][ref]['logging']
        if "syslog_destination" in logging:
            labels['lblhostlog'] = logging['syslog_destination']
        else:
            labels['lblhostlog'] = "Local"

        boot_time = self.humanize_time(time.time() - int(host_other_config['boot_time'][:-1]))
        tool_boot_time = self.humanize_time(time.time() - int(host_other_config['agent_start_time'][:-1]))
        labels['lblhostuptime'] = boot_time
        labels['lblhosttooluptime'] = tool_boot_time
        labels['lblhostuuid'] = self.all['host'][ref]['uuid']
        labels['lblhostdns'] = self.all['host'][ref]['hostname']
        labels['lblhostprimary'] = self.all['host'][ref]['address']
        resident_vms = self.all['host'][ref]['resident_VMs']
        host_vms_memory = []
        for resident_vm_uuid in resident_vms:
            if self.all['vms'][resident_vm_uuid]['is_control_domain']:
                host_memory = self.all['vms'][resident_vm_uuid]['memory_target']
            else:
                host_vms_memory.append(self.all['vms'][resident_vm_uuid]['name_label']
                                       + ": using " +
                                       self.convert_bytes(self.all['vms'][resident_vm_uuid]['memory_dynamic_max']))
        host_metrics_uuid = self.all['host'][ref]['metrics']
        host_metrics = self.all['host_metrics'][host_metrics_uuid]
        labels['lblhostmemserver'] = "%s free of %s available (%s total)" % \
                                     (self.convert_bytes(host_metrics['memory_free']),
                                      self.convert_bytes(int(host_metrics['memory_total']) - int(host_memory)),
                                      self.convert_bytes(host_metrics['memory_total']))
        labels['lblhostmemoryvms'] = '\n'.join(host_vms_memory)
        labels['lblhostmemory'] = self.convert_bytes(host_memory)
        labels['lblhostversiondate'] = software_version['date']
        labels['lblhostversionbuildnumber'] = software_version['build_number']
        labels['lblhostversionbuildversion'] = software_version['product_version']
        expiry = self.humanize_time(self.get_seconds_difference_reverse(license_params['expiry']))
        labels['lblhostlicexpire'] = expiry
        labels['lblhostlicserver'] = license_params['sku_marketing_name']
        labels['lblhostliccode'] = license_params['productcode']
        labels['lblhostlicserial'] = license_params['serialnumber']
        host_cpus = self.all['host'][ref]['host_CPUs']
        cpus = []
        for host_cpu_uuid in host_cpus:
            cpus.append("Vendor: %s\nModel: %s\nSpeed: %s" % (
                self.all['host_cpu'][host_cpu_uuid]['vendor'],
                self.all['host_cpu'][host_cpu_uuid]['modelname'],
                self.all['host_cpu'][host_cpu_uuid]['speed']))

        labels['lblhostcpus'] = '\n'.join(cpus)

        host_patchs = self.all['host'][ref]['patches']
        patchs = []
        for host_cpu_patch in host_patchs:
            pool_patch = self.all['host_patch'][host_cpu_patch]['pool_patch']
            patchs.append(self.all['pool_patch'][pool_patch]['name_label'])

        labels['lblhostpatchs'] = '\n'.join(sorted(patchs))

        # TODO: list hotfix applied
        for label in labels.keys():
            try:
                builder.get_object(label).set_label(labels[label])
            except AttributeError:
                print '%s does not exist' % label

    def update_tab_pool_general(self, ref, builder):
        labels = {}
        if ref not in self.all['pool']:
            return
        labels["lblpoolname"] = self.all['pool'][ref]['name_label']
        labels["lblpooldescription"] = self.all['pool'][ref]['name_description']
        other_config = self.all['pool'][ref]['other_config']
        if self.all['pool'][ref]['tags']:
            labels["lblpooltags"] = ", ".join(self.all['pool'][ref]['tags'])
        else:
            labels["lblpooltags"] = "<None>"
        if "folder" in other_config:
            labels["lblpoolfolder"] = other_config['folder']
        else:
            labels["lblpoolfolder"] = "<None>"

        fullpatchs = []
        partialpatchs = []
        for patch in self.all['pool_patch']:
            hosts = {}
            for host_patch in self.all['pool_patch'][patch]["host_patches"]:
                host = self.all['host_patch'][host_patch]["host"]
                if host not in hosts:
                    hosts[host] = []

                hosts[host] += self.all['pool_patch'][patch]["host_patches"]
            if hosts.keys() == self.all['host'].keys():
                fullpatchs.append(self.all['pool_patch'][patch]["name_label"])
            else:
                partialpatchs.append(self.all['pool_patch'][patch]["name_label"])

        labels["lblpoolfullpatchs"] = '\n'.join(sorted(fullpatchs))
        labels["lblpoolpartialpatchs"] = '\n'.join(sorted(partialpatchs))

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
        if ref in self.all['vms']:
            metric = self.all['vms'][ref]['metrics']
            metric_guest = self.all['vms'][ref]['guest_metrics']
            labels["lblvmname"] = self.all['vms'][ref]['name_label']
            labels["lblvmdescription"] = self.all['vms'][ref]['name_description']
            labels["lblvmuuid"] = self.all['vms'][ref]['uuid']
            labels["lblvmmemory"] = self.convert_bytes(self.all['vms'][ref]['memory_dynamic_max'])
            if self.all['vms'][ref]['tags']:
                labels["lblvmtags"] = ", ".join(self.all['vms'][ref]['tags'])
            else:
                labels["lblvmtags"] = "<None>"
            labels["lblvmcpu"] = self.all['vms'][ref]['VCPUs_at_startup']
            other_config = self.all['vms'][ref]['other_config']
            if "auto_poweron" in other_config and other_config["auto_poweron"] == "true":
                labels["lblvmautoboot"] = "Yes"
            else:
                labels["lblvmautoboot"] = "No"

            if not self.all['vms'][ref]['HVM_boot_policy']:
                labels['lblvmboot'] = "OS boot parameters:"
                labels["lblvmparameters"] = self.all['vms'][ref]['PV_args']
            else:
                labels['lblvmboot'] = "Boot order:"
                labels['lblvmparameters'] = ""
                for param in list(self.all['vms'][ref]['HVM_boot_params']['order']):
                        if param == 'c':
                            labels['lblvmparameters'] += "Hard Disk\n"
                        elif param == 'd':
                            labels['lblvmparameters'] += "DVD-Drive\n"
                        elif param == 'n':
                            labels['lblvmparameters'] += "Network\n"

            priority = self.all['vms'][ref]["VCPUs_params"]
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

            # FIXME
            # labels["lblvmstartup"] =  str(self.connection.VM_metrics.get_start_time(self.session_uuid,metric)['Value'])
            metric = self.all['vms'][ref]['metrics']
            if metric not in self.all['VM_metrics']:
                res = self.connection.VM_metrics.get_record(self.session_uuid, ref)
                if "Value" in res:
                    self.all['VM_metrics'][ref] = res["Value"]

            if metric in self.all['VM_metrics']:
                if self.all['VM_metrics'][metric]['start_time'] != "19700101T00:00:00Z":
                    startup = self.humanize_time(self.get_seconds_difference(self.all['VM_metrics'][metric]['start_time']))
                    labels["lblvmstartup"] = startup
                else:
                    labels["lblvmstartup"] = "never started up"
            else:
                labels["lblvmstartup"] = ""
            labels['lblvmdistro'] = ""
            if metric_guest != "OpaqueRef:NULL" and metric_guest in self.all['VM_guest_metrics']:
                guest_metrics = self.all['VM_guest_metrics'][metric_guest]
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
                if "os_version" in guest_metrics and "name" in guest_metrics["os_version"]:
                    labels["lblvmdistro"] = guest_metrics["os_version"]["name"]
            else:
                state = "<span foreground='red'><b>Tools not installed</b></span>"
            labels["lblvmvirtstate"] = state
            if "folder" in other_config:
                labels["lblvmfolder"] = other_config['folder']
            else:
                labels["lblvmfolder"] = "<None>"

            for label in labels.keys():
                builder.get_object(label).set_label(labels[label])

    def export_vm(self, ref, destination, ref2=None, as_vm=False):
        if ref2:
            task_uuid = self.connection.task.create(self.session_uuid, "Exporting snapshot",
                                                    "Exporting snapshot " + destination)
        else:
            task_uuid = self.connection.task.create(self.session_uuid, "Exporting VM",
                                                    "Exporting VM " + destination)
        self.track_tasks[task_uuid['Value']] = ref2 if ref2 else ref
        url = "https://%s/export?ref=%s&session_id=%s&task_id=%s" % (self.wine.selected_host,
                                                                    ref, self.session_uuid,
                                                                    task_uuid['Value'])
        Thread(target=self.download_export, args=(url, destination, ref, as_vm)).start()

    def download_export(self, url, destination, ref, as_vm):
        # print "Saving %s to %s" % (url, destination)
        if as_vm:
            self.connection.VM.set_is_a_template(self.session_uuid, ref, False)
        urllib.urlretrieve(url, destination)
        if as_vm:
            self.connection.VM.set_is_a_template(self.session_uuid, ref, True)

    def get_actions(self, ref):
        return self.all['vms'][ref]['allowed_operations']

    def get_connect_string(self, ref):
        # FIXME
        """
        vm_uuid  = self.connection.VM.get_by_uuid(self.session_uuid,uuid)
        consoles = self.connection.VM.get_consoles(self.session_uuid, vm_uuid['Value'])
        console  = self.connection.console.get_record(self.session_uuid,consoles['Value'][0])
        """
        return "CONNECT /console?ref=%s&session_id=%s HTTP/1.1\r\n\r\n" % (ref, self.session_uuid)

    def get_connect_parameters(self, ref, host):
        """
        vm_uuid  = self.connection.VM.get_by_uuid(self.session_uuid,uuid)
        consoles = self.connection.VM.get_consoles(self.session_uuid, vm_uuid['Value'])
        console  = self.connection.console.get_record(self.session_uuid,consoles['Value'][0])
        """
        return "%s %s %s" % (host, ref, self.session_uuid)

    # TODO: these should *not* be here
    # {
    @staticmethod
    def dump(self, obj):
        for attr in dir(obj):
            print "obj.%s = %s" % (attr, getattr(obj, attr))

    @staticmethod
    def humanize_time(seconds):
        string = ""
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        if days:
            string += "%02d days " % days
        else:
            string += "00 days "
        if hours:
            string += "%02d hours " % hours
        else:
            string += "00 hours "
        if minutes:
            string += "%02d minutes" % minutes
        else:
            string += "00 minutes"
        return string

    def convert_bytes(self, n):
        """
        http://www.5dollarwhitebox.org/drupal/node/84
        """
        n = float(n)
        K, M, G, T = 1 << 10, 1 << 20, 1 << 30, 1 << 40
        if n >= T:
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
        # support function -  to evalue msg expression before pushing to GTK loop
        def push_alert(msg):
            gobject.idle_add(lambda: self.wine.push_alert(msg))

        while not self.halt:
            try:
                eventn = self.connection_events.event.next(self.session_events_uuid)
                if "Value" in eventn:
                    for event in eventn["Value"]:
                        if event['class'] == "vm":
                            if event['operation'] == "add":
                                self.all['vms'][event["ref"]] = event['snapshot']
                                if not self.all['vms'][event["ref"]]["is_a_snapshot"]:
                                    gobject.idle_add(lambda: self.add_vm_to_tree(event["ref"]) and False)
                                else:
                                    gobject.idle_add(lambda: self.fill_vm_snapshots(
                                        self.wine.selected_ref, self.wine.builder.get_object("treevmsnapshots"),
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
                                if not self.all['vms'][event["ref"]]["is_a_snapshot"]:
                                    self.found_iter = None
                                    self.treestore.foreach(self.search_ref, event["ref"])
                                    if self.found_iter:
                                        gobject.idle_add(lambda: self.treestore.remove(self.found_iter) and False)
                                    del self.all['vms'][event["ref"]]
                                else:
                                    gobject.idle_add(lambda: self.fill_vm_snapshots(
                                        self.wine.selected_ref, self.wine.builder.get_object("treevmsnapshots"),
                                        self.wine.builder.get_object("listvmsnapshots")) and False)
                                    del self.all['vms'][event["ref"]]

                            else:
                                filter_uuid = event['snapshot']['uuid']
                                vm_id = self.vm_filter_uuid(filter_uuid)
                                if vm_id:
                                    # make into a template
                                    if event['snapshot']['is_a_template'] != \
                                            self.all['vms'][vm_id]['is_a_template']:
                                        self.all['vms'][vm_id] = event['snapshot']
                                        self.found_iter = None
                                        self.treestore.foreach(self.search_ref, event["ref"])
                                        if self.found_iter and event['snapshot']['is_a_template']:
                                            gobject.idle_add(lambda: self.treestore.set(
                                                self.found_iter, 0,
                                                gtk.gdk.pixbuf_new_from_file(os.path.join(
                                                    utils.module_path(), "images/user_template_16.png")), 3,
                                                "custom_template") and False)
                                            gobject.idle_add(lambda: self.wine.update_tabs() and False)
                                    else:
                                        if event['snapshot']['resident_on'] != \
                                                self.all['vms'][vm_id]['resident_on']:
                                            self.found_iter = None
                                            gobject.idle_add(lambda: self.treestore.foreach(self.search_ref,
                                                                                            event["ref"]) and False)
                                            if self.found_iter:
                                                gobject.idle_add(lambda: self.treestore.remove(self.found_iter)
                                                                 and False)
                                                self.all['vms'][vm_id] = event['snapshot']
                                                gobject.idle_add(lambda: self.add_vm_to_tree(event["ref"] and False))

                                        if event['snapshot']['affinity'] != \
                                                self.all['vms'][vm_id]['affinity']:
                                            print "migrate or start on or resume on2"
                                        self.all['vms'][vm_id] = event['snapshot']
                                else:
                                    if event["ref"] in self.track_tasks:
                                        self.all['vms'][self.track_tasks[event["ref"]]] = event['snapshot']

                                    else:
                                        self.all['vms'][event["ref"]] = event['snapshot']
                                self.all['vms'][event["ref"]] = event['snapshot']
                                self.treestore.foreach(self.update_vm_status, filter_uuid)
                                gobject.idle_add(lambda: self.wine.update_memory_tab() and False)
                        elif event['class'] == "vm_guest_metrics":
                            self.all['VM_guest_metrics'][event['ref']] = \
                                self.connection.VM_guest_metrics.get_record(self.session_uuid, event['ref'])
                        elif event['class'] == "task":
                            # print ">>>" +  event["snapshot"]["name_label"] + " " + event["snapshot"]["status"] + " " + str(event["snapshot"]["progress"]) + ":\t", event
                            self.all['task'][event["ref"]] = event["snapshot"]
                            if event["ref"] not in self.track_tasks:
                                # print event
                                # print event["snapshot"]["name_label"] + " " + event["snapshot"]["status"] + " " + str(event["snapshot"]["progress"]) + ":\t", event
                                pass
                            if event["snapshot"]["status"] == "success":
                                if event["ref"] in self.vboxchildprogressbar:
                                    self.vboxchildprogress[event["ref"]].hide()
                                    self.vboxchildprogressbar[event["ref"]].hide()
                                    self.vboxchildcancel[event["ref"]].hide()
                            if event["snapshot"]["error_info"]:
                                if event["ref"] in self.track_tasks:
                                    if self.track_tasks[event["ref"]] in self.all['vms']:
                                        gobject.idle_add(lambda: self.wine.push_error_alert(
                                            "%s %s %s" % (event["snapshot"]["name_label"],
                                                          self.all['vms'][self.track_tasks[event["ref"]]]["name_label"],
                                                          event["snapshot"]["error_info"])) and False)
                                        eref = event["ref"]
                                        if eref in self.vboxchildcancel:
                                            self.vboxchildcancel[eref].hide()
                                            self.vboxchildprogressbar[eref].hide()
                                            self.vboxchildprogress[eref].set_label(str(event["snapshot"]["error_info"]))
                                            self.vboxchildprogress[eref].modify_fg(gtk.STATE_NORMAL,
                                                                                   gtk.gdk.color_parse('#FF0000'))

                                    else:
                                        self.wine.builder.get_object("wprogressimportvm").hide()
                                        self.wine.builder.get_object("tabboximport").set_current_page(2)
                                        gobject.idle_add(lambda: self.wine.push_error_alert(
                                            "%s: %s" % (event["snapshot"]["name_description"],
                                                        event["snapshot"]["error_info"])) and False)
                            else:
                                if event["ref"] in self.track_tasks:
                                    name_lbl = event['snapshot']['name_label']
                                    vm_ref = self.track_tasks[event["ref"]]
                                    vm_name = self.all['vms'][vm_ref]['name_label']
                                    progress = event['snapshot']['progress']

                                    if vm_ref in self.all['vms']:
                                        if event["snapshot"]["status"] == "success":
                                            gobject.idle_add(
                                                lambda: self.wine.push_alert(
                                                    "%s %s completed" % (
                                                        name_lbl, vm_name))
                                                and False)
                                        else:
                                            gobject.idle_add(
                                                lambda: self.wine.push_alert(
                                                    "%s %s %s" %
                                                    (name_lbl, vm_name,
                                                     (" %.2f%%" %
                                                      (float(progress)*100))))
                                                and False)
                                    else:
                                        vm = self.connection.VM.get_record(self.session_uuid,
                                                                           self.track_tasks[event["ref"]])
                                        if "Value" in vm:
                                            self.all['vms'][self.track_tasks[event["ref"]]] = vm['Value']
                                            # self.add_vm_to_tree(self.track_tasks[event["ref"]])
                                            gobject.idle_add(lambda: self.wine.modelfilter.clear_cache() and False)
                                            gobject.idle_add(lambda: self.wine.modelfilter.refilter() and False)
                                            gobject.idle_add(lambda: self.wine.push_alert(
                                                "%s %s %s" % (
                                                    event["snapshot"]["name_label"],
                                                    self.all['vms'][self.track_tasks[event["ref"]]]["name_label"],
                                                    (" %.2f%%" % (float(event["snapshot"]["progress"])*100))))
                                                and False)
                                        else:
                                            gobject.idle_add(lambda: self.wine.push_alert(
                                                "%s: %s %s" % (
                                                    event["snapshot"]["name_label"],
                                                    event["snapshot"]["name_description"],
                                                    (" %.2f%%" % (float(event["snapshot"]["progress"])*100))))
                                                and False)
                                else:
                                    pass  # FIXME?
                                    # self.wine.push_alert(event["snapshot"]["name_label"] + (" %.2f%%" % (float(event["snapshot"]["progress"])*100)))

                                self.dbg_track_num += 1

                            if event["snapshot"]["status"] == "success":
                                if event["snapshot"]["name_label"] == "Async.VIF.create":
                                    dom = xml.dom.minidom.parseString(event['snapshot']['result'])
                                    nodes = dom.getElementsByTagName("value")
                                    vif_ref = nodes[0].childNodes[0].data
                                    self.connection.VIF.plug(self.session_uuid, vif_ref)
                                    if self.wine.selected_tab == "VM_Network":
                                        gobject.idle_add(lambda: self.fill_vm_network(
                                            self.wine.selected_ref,
                                            self.wine.builder.get_object("treevmnetwork"),
                                            self.wine.builder.get_object("listvmnetwork")) and False)
                                if event["snapshot"]["name_label"] == "Async.VM.revert":
                                    self.start_vm(self.track_tasks[event["ref"]])

                                if event["snapshot"]["name_label"] in ("Async.VM.clone", "Async.VM.copy"):
                                    dom = xml.dom.minidom.parseString(event['snapshot']['result'])
                                    nodes = dom.getElementsByTagName("value")
                                    vm_ref = nodes[0].childNodes[0].data
                                    # self.add_vm_to_tree(vm_ref)
                                    if event["ref"] in self.set_descriptions:
                                        self.connection.VM.set_name_description(self.session_uuid, vm_ref,
                                                                                self.set_descriptions[event["ref"]])
                                if event["snapshot"]["name_label"] in ("Async.VM.provision", "Async.VM.clone",
                                                                       "Async.VM.copy"):
                                    filter_uuid = event['snapshot']['uuid']
                                    vm_id = self.vm_filter_uuid(filter_uuid)
                                    # TODO
                                    # Detect VM with event["ref"]
                                    if event["ref"] in self.track_tasks and self.track_tasks[event["ref"]] in \
                                            self.all['vms']:
                                        for vbd in self.all['vms'][self.track_tasks[event["ref"]]]['VBDs']:
                                            self.all['SR'][vbd] = self.connection.VBD.get_record(self.session_uuid,
                                                                                                   vbd)['Value']
                                        for vif in self.all['vms'][self.track_tasks[event["ref"]]]['VIFs']:
                                            self.all['VIF'][vif] = self.connection.VIF.get_record(self.session_uuid,
                                                                                               vif)['Value']
                                    if vm_id is not None:
                                        self.all['vms'][vm_id]['allowed_operations'] = \
                                            self.connection.VM.get_allowed_operations(self.session_uuid,
                                                                                      vm_id)['Value']
                                    else:
                                        if event["ref"] in self.track_tasks:
                                            self.all['vms'][self.track_tasks[event["ref"]]]['allowed_operations'] = \
                                                self.connection.VM.get_allowed_operations(
                                                    self.session_uuid, self.track_tasks[event["ref"]])['Value']
                                            if self.all['vms'][self.track_tasks[event["ref"]]][
                                               'allowed_operations'].count("start"):
                                                if self.track_tasks[event["ref"]] in self.autostart:
                                                    host_start = self.autostart[self.track_tasks[event["ref"]]]
                                                    res = self.connection.Async.VM.start_on(
                                                        self.session_uuid, self.track_tasks[event["ref"]],
                                                        host_start, False, False)
                                                    if "Value" in res:
                                                        self.track_tasks[res['Value']] = self.track_tasks[event["ref"]]
                                                    else:
                                                        print res
                                if event["snapshot"]["name_label"] == "Async.VM.snapshot":
                                    self.filter_uuid = event['snapshot']['uuid']
                                    if self.track_tasks[event["ref"]] in self.all['vms']:
                                        vm_uuid = self.track_tasks[event["ref"]]
                                        dom = xml.dom.minidom.parseString(event['snapshot']['result'])
                                        nodes = dom.getElementsByTagName("value")
                                        snapshot_ref = nodes[0].childNodes[0].data
                                        # self.all['vms'][vm_uuid]['snapshots'].append(snapshot_ref)
                                        self.all['vms'][snapshot_ref] = self.connection.VM.get_record(
                                            self.session_uuid, snapshot_ref)['Value']
                                        for vbd in self.all['vms'][snapshot_ref]['VBDs']:
                                            # FIXME
                                            self.all['VBD'][vbd] = self.connection.VBD.get_record(
                                                self.session_uuid, vbd)['Value']

                                        if self.track_tasks[event["ref"]] == self.wine.selected_ref and \
                                           self.wine.selected_tab == "VM_Snapshots":
                                                gobject.idle_add(lambda: self.fill_vm_snapshots(
                                                    self.wine.selected_ref,
                                                    self.wine.builder.get_object("treevmsnapshots"),
                                                    self.wine.builder.get_object("listvmsnapshots")) and False)
                                if event["snapshot"]["name_label"] == "VM.Async.snapshot":
                                        if self.track_tasks[event["ref"]] == self.wine.selected_ref and \
                                           self.wine.selected_tab == "VM_Snapshots":
                                                gobject.idle_add(lambda: self.fill_vm_snapshots(
                                                    self.wine.selected_ref,
                                                    self.wine.builder.get_object("treevmsnapshots"),
                                                    self.wine.builder.get_object("listvmsnapshots")) and False)
                                if event["snapshot"]["name_label"] == "Importing VM":
                                        if self.import_start:
                                            self.start_vm(self.track_tasks[event["ref"]])
                                        if self.import_make_into_template:
                                            self.make_into_template(self.track_tasks[event["ref"]])
                                if event["snapshot"]["name_label"] == "VM.destroy":
                                        if self.wine.selected_tab == "VM_Snapshots":
                                                gobject.idle_add(lambda: self.fill_vm_snapshots(
                                                    self.wine.selected_ref,
                                                    self.wine.builder.get_object("treevmsnapshots"),
                                                    self.wine.builder.get_object("listvmsnapshots")) and False)
                                if event["snapshot"]["name_label"] == "VIF.destroy":
                                        if self.wine.selected_tab == "VM_Network":
                                                gobject.idle_add(lambda: self.fill_vm_network(
                                                    self.wine.selected_ref,
                                                    self.wine.builder.get_object("treevmnetwork"),
                                                    self.wine.builder.get_object("listvmnetwork")) and False)
                                if event["snapshot"]["name_label"] == "VIF.plug":
                                        if self.wine.selected_tab == "VM_Network":
                                                gobject.idle_add(lambda: self.fill_vm_network(
                                                    self.wine.selected_ref,
                                                    self.wine.builder.get_object("treevmnetwork"),
                                                    self.wine.builder.get_object("listvmnetwork")) and False)

                                if event["snapshot"]["name_label"] in ("VBD.create", "VBD.destroy"):
                                        if self.wine.selected_tab == "VM_Storage":
                                                # print "fill_vm_storage start"
                                                gobject.idle_add(lambda: self.fill_vm_storage(
                                                    self.wine.selected_ref,
                                                    self.wine.builder.get_object("listvmstorage")) and False)
                                                # print pdb.set_trace()
                                                # print "fill_vm_storage end"
                                if event["snapshot"]["name_label"] in ("VDI.create", "VDI.destroy"):
                                        if self.wine.selected_tab == "Local_Storage":
                                                gobject.idle_add(lambda: self.fill_local_storage(
                                                    self.wine.selected_ref,
                                                    self.wine.builder.get_object("liststg")) and False)
                                if event["snapshot"]["name_label"] in ("network.create", "network.destroy"):
                                        if self.wine.selected_tab == "HOST_Network":
                                            gobject.idle_add(lambda: self.wine.update_tab_host_network() and False)

                                if event["snapshot"]["name_label"] in ("Async.Bond.create", "Bond.create",
                                                                       "Async.Bond.destroy", "Bond.destroy"):
                                        if self.wine.selected_tab == "HOST_Nics":
                                            gobject.idle_add(lambda: self.wine.update_tab_host_nics() and False)

                            if event["ref"] in self.track_tasks:
                                self.tasks[event["ref"]] = event
                            if event["ref"] in self.vboxchildprogressbar:
                                self.vboxchildprogressbar[event["ref"]].set_fraction(
                                    float(event["snapshot"]["progress"]))

                            else:
                                if event["ref"] in self.track_tasks:
                                    self.tasks[event["ref"]] = event
                                    if self.track_tasks[event["ref"]] == self.wine.selected_ref and \
                                       self.wine.selected_tab == "VM_Logs":
                                        if event["ref"] in self.track_tasks \
                                                and event["ref"] not in self.vboxchildprogressbar:
                                            gobject.idle_add(lambda: self.fill_vm_log(self.wine.selected_uuid,
                                                                                      thread=True) and False)
                                else:
                                    if event["snapshot"]["name_label"] == "Exporting VM" \
                                            and event["ref"] not in self.vboxchildprogressbar:
                                        self.track_tasks[event["ref"]] = self.wine.selected_ref
                                        self.tasks[event["ref"]] = event
                                        gobject.idle_add(lambda: self.fill_vm_log(self.wine.selected_uuid,
                                                                                  thread=True) and False)
                                    else:
                                        # print event
                                        pass

                        elif event["class"] == "vdi":
                            self.all['VDI'][event["ref"]] = event["snapshot"]
                            if self.wine.selected_tab == "Local_Storage":
                                liststg = self.wine.builder.get_object("liststg")
                                gobject.idle_add(lambda: self.fill_local_storage(self.wine.selected_ref, liststg)
                                                 and False)
                            if self.wine.selected_tab == "VM_Storage":
                                gobject.idle_add(lambda: self.fill_vm_storage(
                                    self.wine.selected_ref,
                                    self.wine.builder.get_object("listvmstorage")) and False)

                        elif event["class"] == "vbd":
                            self.all['VBD'][event["ref"]] = event["snapshot"]
                            """
                            if event["snapshot"]["allowed_operations"].count("attach") == 1:
                                self.last_vbd = event["ref"]
                            """
                        elif event["class"] == "pif":
                            self.all['PIF'][event["ref"]] = event["snapshot"]
                            if self.wine.selected_tab == "HOST_Nics":
                                gobject.idle_add(lambda: self.wine.update_tab_host_nics() and False)

                        elif event["class"] == "bond":
                            if event["operation"] == "del":
                                del self.all['Bond'][event["ref"]]
                            else:
                                self.all['Bond'][event["ref"]] = event["snapshot"]
                            if self.wine.selected_tab == "HOST_Nics":
                                gobject.idle_add(lambda: self.wine.update_tab_host_nics() and False)

                        elif event["class"] == "vif":
                            if event["operation"] == "del":
                                del self.all['VIF'][event["ref"]]
                            else:
                                if event["operation"] == "add":
                                    self.connection.VIF.plug(self.session_uuid, event["ref"])
                                self.all['VIF'][event["ref"]] = event["snapshot"]
                        elif event["class"] == "sr":
                            self.filter_uuid = event['snapshot']['uuid']
                            self.all['SR'][event["ref"]] = event["snapshot"]
                            self.treestore.foreach(self.update_storage_status, "")
                            if event["operation"] == "del":
                                self.filter_uuid = event['snapshot']['uuid']
                                gobject.idle_add(lambda: self.treestore.foreach(self.delete_storage, "") and False)
                            if event["operation"] == "add":
                                sr = event["ref"]
                                # FIXME
                                host = self.all['host'].keys()[0]
                                if self.poolroot:
                                    # iter_ref = self.treestore.append(self.poolroot, [\
                                    gobject.idle_add(lambda: self.treestore.append(self.poolroot, [
                                        gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                                  "images/storage_shaped_16.png")),
                                        self.all['SR'][sr]['name_label'], self.all['SR'][sr]['uuid'],
                                        "storage", None, self.host, sr, self.all['SR'][sr]['allowed_operations'],
                                        None]) and False)
                                else:
                                    # iter_ref = self.treestore.append(self.hostroot[host], [\
                                    gobject.idle_add(lambda: self.treestore.append(self.hostroot[host], [
                                        gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                                  "images/storage_shaped_16.png")),
                                        self.all['SR'][sr]['name_label'], self.all['SR'][sr]['uuid'],
                                        "storage", None, self.host, sr, self.all['SR'][sr]['allowed_operations'],
                                        None]) and False)

                        elif event["class"] == "pool":
                            if self.all['pool'][event["ref"]]['name_label'] != event["snapshot"]["name_label"]:
                                if self.poolroot:
                                    gobject.idle_add(lambda: self.wine.treestore.remove(self.poolroot) and False)
                                else:
                                    for host_ref in self.hostroot.keys():
                                        gobject.idle_add(lambda: self.wine.treestore.remove(self.hostroot[host_ref])
                                                         and False)

                                self.sync()
                            if self.all['pool'][event["ref"]]['default_SR'] != event["snapshot"]["default_SR"]:
                                self.treestore.foreach(self.update_default_sr,
                                                       [self.all['pool'][event["ref"]]['default_SR'],
                                                        event["snapshot"]["default_SR"]])
                            self.all['pool'][event["ref"]] = event["snapshot"]
                            if self.wine.selected_type == "pool":
                                self.update_tab_pool_general(self.wine.selected_ref, self.wine.builder)
                        elif event["class"] == "message":
                            if event["operation"] == "del":
                                del self.all_messages[event["ref"]]
                            elif event["operation"] == "add":
                                self.all_messages[event["ref"]] = event["snapshot"]
                                self.add_alert(event["snapshot"], event["ref"], self.wine.listalerts)
                                self.wine.update_n_alerts()
                            else:
                                print event
                        elif event["class"] == "vm_guest_metrics":
                            self.all['VM_guest_metrics'][event["ref"]] = event["snapshot"]
                        elif event["class"] == "network":
                            if event["operation"] == "del":
                                del self.all['network'][event["ref"]]
                            else:
                                self.all['network'][event["ref"]] = event["snapshot"]
                            if self.wine.selected_tab == "HOST_Network":
                                gobject.idle_add(lambda: self.wine.update_tab_host_network() and False)
                        elif event["class"] == "vlan":
                            if event["operation"] == "del":
                                if event["ref"] in self.all['vlan']:
                                    del self.all['vlan'][event["ref"]]
                            self.all['vlan'][event["ref"]] = event["snapshot"]

                        elif event["class"] == "host":
                            if event["operation"] == "del":
                                self.filter_uuid = event['snapshot']['uuid']
                                self.treestore.foreach(self.delete_host, "")
                                del self.all['host'][event["ref"]]

                            elif event["operation"] == "add":
                                self.all['host'][event["ref"]] = event["snapshot"]
                                self.wine.show_error_dlg("Host added, please reconnect for sync all info")
                            else:
                                self.filter_uuid = event['snapshot']['uuid']
                                self.all['host'][event["ref"]] = event["snapshot"]
                                self.treestore.foreach(self.update_host_status, "")
                        elif event["class"] == "pif_metrics":
                            self.all['PIF_metrics'][event["ref"]] = event["snapshot"]
                        elif event["class"] == "host_metrics":
                            self.all['host_metrics'][event["ref"]] = event["snapshot"]
                        elif event["class"] == "vbd_metrics":
                            self.all['VBD_metrics'][event["ref"]] = event["snapshot"]
                        elif event["class"] == "vif_metrics":
                            self.all['VIF_metrics'][event["ref"]] = event["snapshot"]
                        elif event["class"] == "vm_metrics":
                            self.all['VM_metrics'][event["ref"]] = event["snapshot"]
                        elif event["class"] == "console":
                            self.all['console'][event["ref"]] = event["snapshot"]
                        elif event["class"] == "host_patch":
                            if event["operation"] == "del":
                                del self.all['host_patch'][event["ref"]]
                            else:
                                self.all['host_patch'][event["ref"]] = event["snapshot"]
                        elif event["class"] == "pool_patch":
                            if event["operation"] == "del":
                                del self.all['pool_patch'][event["ref"]]
                            else:
                                self.all['pool_patch'][event["ref"]] = event["snapshot"]
                        elif event["class"] == "pbd":
                            self.all['PBD'][event["ref"]] = event["snapshot"]
                            if event["operation"] == "add":
                                sr = event["snapshot"]["SR"]
                                host = event["snapshot"]["host"]
                                gobject.idle_add(lambda: self.treestore.insert_after(
                                    self.hostroot[host], self.last_storage_iter,
                                    [gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                               "images/storage_shaped_16.png")),
                                     self.all['SR'][sr]['name_label'], self.all['SR'][sr]['uuid'],
                                     "storage", None, self.host, sr, self.all['SR'][sr]['allowed_operations'], None])
                                    and False)
                        elif event["class"] == "host_cpu":
                            self.all['host_cpu'][event["ref"]] = event["snapshot"]
                        else:
                            print event["class"] + " => ", event
            except socket, msg:
                self.halt = True
                # FIXME TODO
                # Disconnect
            except httplib.CannotSendRequest:
                # TODO: csun: this is a common error/complaint. Find out why this is happening and fix this?
                print "Event loop received CannotSendRequest exception, retrying..."
                time.sleep(0.1)
            except:
                print "Event loop -- unexpected error:"
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
            gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file(os.path.join(
                utils.module_path(), "images/storage_shaped_16.png"))) and False)
        if sr == user_data[1]:
            gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file(os.path.join(
                utils.module_path(), "images/storage_default_16.png"))) and False)
            self.default_sr = sr
        if sr == user_data[0] or sr == user_data[1]:
            if len(self.all['SR'][sr]['PBDs']) == 0:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file(
                    os.path.join(utils.module_path(), "images/storage_detached_16.png"))) and False)
            broken = False
            for pbd_ref in self.all['SR'][sr]['PBDs']:
                if not self.all['PBD'][pbd_ref]['currently_attached']:
                    broken = True
                    gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file(
                        os.path.join(utils.module_path(), "images/storage_broken_16.png"))) and False)
            if not broken:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file(
                    os.path.join(utils.module_path(), "images/storage_shaped_16.png"))) and False)

    def update_vm_status(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == user_data:
            vm = self.all['vms'][self.vm_filter_uuid(user_data)]
            if not vm["is_a_template"]:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  1, vm['name_label']) and False)
                if len(vm["current_operations"]):
                    gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file(
                        os.path.join(utils.module_path(), "images/tree_starting_16.png"))) and False)
                else:
                    gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file(
                        os.path.join(utils.module_path(), "images/tree_%s_16.png" % vm['power_state'].lower())))
                        and False)
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  4, vm['power_state']) and False)
                self.wine.selected_state = vm['power_state']
                self.wine.selected_actions = vm['allowed_operations']
            else:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  1, vm['name_label']) and False)

            if self.wine.selected_ref == self.treestore.get_value(iter_ref, 6):
                gobject.idle_add(lambda: self.wine.update_tabs() and False)
                gobject.idle_add(lambda: self.wine.builder.get_object("headimage").set_from_pixbuf(
                    self.treestore.get_value(iter_ref, 0)) and False)
                gobject.idle_add(lambda: self.wine.builder.get_object("headlabel").set_label(
                    self.treestore.get_value(iter_ref,  1)) and False)

    def update_storage_status(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            storage = self.all['SR'][self.storage_filter_uuid()]
            gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  1, storage['name_label']) and False)
            if self.wine.selected_ref == self.treestore.get_value(iter_ref, 6):
                gobject.idle_add(lambda: self.wine.update_tabs() and False)
                gobject.idle_add(lambda: self.wine.builder.get_object("headimage").set_from_pixbuf(
                    self.treestore.get_value(iter_ref, 0)) and False)
                gobject.idle_add(lambda: self.wine.builder.get_object("headlabel").set_label(
                    self.treestore.get_value(iter_ref,  1)) and False)
            sr = self.treestore.get_value(iter_ref, 6)
            if len(self.all['SR'][sr]['PBDs']) == 0:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file(
                    os.path.join(utils.module_path(), "images/storage_detached_16.png"))) and False)
            broken = False
            for pbd_ref in self.all['SR'][sr]['PBDs']:
                if not self.all['PBD'][pbd_ref]['currently_attached']:
                    broken = True
                    gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file(
                        os.path.join(utils.module_path(), "images/storage_broken_16.png"))) and False)
            if not broken:
                gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file(
                    os.path.join(utils.module_path(), "images/storage_shaped_16.png"))) and False)

    def delete_storage(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            self.treestore.remove(iter_ref)

    def update_host_status(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
                if self.treestore.get_value(iter_ref, 1):
                    host = self.all['host'][self.host_filter_uuid()]
                    gobject.idle_add(lambda: self.treestore.set_value(iter_ref,  1, host['name_label']) and False)
                    if host["enabled"]:
                        gobject.idle_add(lambda: self.treestore.set_value(iter_ref, 0,  gtk.gdk.pixbuf_new_from_file(
                            os.path.join(utils.module_path(), "images/tree_connected_16.png"))) and False)
                    else:
                        gobject.idle_add(lambda: self.treestore.set_value(iter_ref, 0,  gtk.gdk.pixbuf_new_from_file(
                            os.path.join(utils.module_path(), "images/tree_disabled_16.png"))) and False)
                    gobject.idle_add(lambda: self.wine.update_tabs() and False)
                    gobject.idle_add(lambda: self.wine.update_toolbar() and False)
                    gobject.idle_add(lambda: self.wine.update_menubar()  and False)
                    gobject.idle_add(lambda: self.wine.builder.get_object("headimage").set_from_pixbuf(
                        self.treestore.get_value(iter_ref, 0)) and False)
                    gobject.idle_add(lambda: self.wine.builder.get_object("headlabel").set_label(
                        self.treestore.get_value(iter_ref,  1)) and False)

    def delete_host(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            gobject.idle_add(lambda: self.treestore.remove(iter_ref) and False)
            gobject.idle_add(lambda: self.wine.update_tabs() and False)

    def log_filter_uuid(self, item):
        return item["obj_uuid"] == self.filter_uuid

    def task_filter_uuid(self, item_ref):
        if item_ref in self.all['task']:
            item = self.all['task'][item_ref]
            if item_ref in self.track_tasks:
                if self.track_tasks[item_ref] in self.all['vms']:
                    return self.all['vms'][self.track_tasks[item_ref]]["uuid"] == self.filter_uuid
                    # return True
            if "ref" in item and item["ref"] in self.track_tasks and self.track_tasks[item["ref"]] in self.all['vms']:
                return self.all['vms'][self.track_tasks[item["ref"]]]["uuid"] == self.filter_uuid
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
        for vbd in self.all['VBD']:
            if self.all['VBD'][vbd]["uuid"] == uuid:
                return vbd
        return None

    def filter_vm_uuid(self, item):
        return item["uuid"] == self.filter_uuid

    def vm_filter_uuid(self, uuid):
        for vm in self.all['vms']:
            if self.all['vms'][vm]["uuid"] == uuid:
                return vm
        return None

    def storage_filter_uuid(self):
        for stg in self.all['SR']:
            if self.all['SR'][stg]["uuid"] == self.filter_uuid:
                return stg
        return None

    def host_filter_uuid(self):
        for host in self.all['host']:
            if self.all['host'][host]["uuid"] == self.filter_uuid:
                return host
        return None

    @staticmethod
    def filter_custom_template(item):
        if not item["is_a_template"]:
            return False
        if item["name_label"][:7] == "__gui__":
            return False
        if item["last_booted_record"] != "":
            return True
        return False

    @staticmethod
    def filter_normal_template(item):
        if not item["is_a_template"]:
            return False
        elif item["name_label"][:7] == "__gui__":
            return False
        elif item["last_booted_record"] == "":
            return True
        return False

    def filter_vdi_ref(self):
        for vdi in self.all['VDI'].keys():
            if vdi == self.filter_vdi:
                return vdi

    @staticmethod
    def search_in_liststore(list, ref, field):
        """
        Function returns iter of element found or None
        """
        print list.__len__()
        for i in range(0, list.__len__()):
            iter_ref = list.get_iter((i,))
            print list.get_value(iter_ref, field)
            if ref == list.get_value(iter_ref, field):
                return iter_ref
        return None
