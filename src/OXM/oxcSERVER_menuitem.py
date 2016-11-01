# -----------------------------------------------------------------------
# OpenXenManager
#
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
# USA.
#
# -----------------------------------------------------------------------
import gtk
from os import path
import xml.dom.minidom
from operator import itemgetter
import gobject
from OXM.capabilities import capabilities_text
import utils


class oxcSERVERmenuitem:
    last_pool_data = []

    def pause_vm(self, ref):
        res = self.connection.Async.VM.pause(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def unsuspend_vm(self, ref):
        res = self.connection.Async.VM.unsuspend(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def resume_vm(self, ref):
        res = self.connection.Async.VM.resume(self.session_uuid, ref, False,
                                              True)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def hard_shutdown_vm(self, ref):
        res = self.connection.Async.VM.hard_shutdown(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def hard_reboot_vm(self, ref):
        res = self.connection.Async.VM.hard_reboot(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def start_vm(self, ref):
        res = self.connection.Async.VM.start(self.session_uuid, ref, False,
                                             False)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def start_vm_recovery_mode(self, ref):
        change_policy = False
        if not self.all['vms'][ref]['HVM_boot_policy']:
            self.connection.VM.set_HVM_boot_policy(self.session_uuid, ref,
                                                   "BIOS order")
            change_policy = True
        order = ""
        if "order" in self.all['vms'][ref]['HVM_boot_params']:
            order = self.all['vms'][ref]['HVM_boot_params']['order']
        self.connection.VM.set_HVM_boot_params(self.session_uuid, ref,
                                               {"order": "dn"})

        res = self.connection.VM.start(self.session_uuid, ref, False, False)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

        if change_policy:
            self.connection.VM.set_HVM_boot_policy(self.session_uuid, ref, "")
        self.connection.VM.set_HVM_boot_params(self.session_uuid, ref,
                                               {"order": order})

    def clean_shutdown_vm(self, ref):
        res = self.connection.Async.VM.clean_shutdown(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def clean_reboot_vm(self, ref):
        res = self.connection.Async.VM.clean_reboot(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def can_start(self, ref, host_uuid):
        can_boot = self.connection.VM.assert_can_boot_here(self.session_uuid,
                                                           ref, host_uuid)
        if "ErrorDescription" in can_boot:
            return can_boot["ErrorDescription"][0].replace("_", "__")
        else:
            return ""

    def suspend_vm(self, ref):
        res = self.connection.Async.VM.suspend(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def unpause_vm(self, ref):
        res = self.connection.VM.unpause(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def make_into_template(self, ref):
        res = self.connection.VM.set_is_a_template(self.session_uuid, ref,
                                                   True)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def start_vm_on(self, widget, ref, host):
        res = self.connection.Async.VM.start_on(self.session_uuid, ref, host,
                                                False, False)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def resume_vm_on(self, widget, ref, host):
        res = self.connection.Async.VM.resume_on(self.session_uuid, ref, host,
                                                 False, False)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def migrate_vm(self, widget, ref, host):
        res = self.connection.Async.VM.pool_migrate(self.session_uuid, ref,
                                                    host, {})
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def fill_list_updates(self, ref, list):
        list.clear()
        for patch in self.all['pool_patch']:
            list.append([patch, self.all['pool_patch'][patch]['name_label']])

    def fill_list_report(self, ref, list):
        list.clear()
        result = self.connection.host.get_system_status_capabilities(
            self.session_uuid, ref)['Value']
        privacy = {"yes": "1", "maybe": "2", "if_customized": "3", "no": "4"}
        dom = xml.dom.minidom.parseString(result)
        nodes = dom.getElementsByTagName("capability")
        capabilities = {}
        for node in nodes:
            attr = node.attributes
            key, checked, pii, minsize, maxsize, mintime, maxtime = \
                [attr.getNamedItem(k).value for k
                    in ["key", "default-checked", "pii", "min-size",
                        "max-size", "min-time", "max-time"]]
            capabilities[privacy[pii] + "_" + key] = [checked, minsize,
                                                      maxsize, mintime,
                                                      maxtime]

        for key in sorted(capabilities.keys()):
            if key.split("_", 2)[1] in capabilities_text:
                confidentiality, ref = key.split("_", 2)
                name, desc = capabilities_text[key.split("_", 2)[1]]
                checked, minsize, maxsize, mintime, maxtime = \
                    [value for value in capabilities[key]]
                size1, time1 = 0, 0
                if minsize == maxsize:
                    if maxsize != "-1" and checked:
                        size1 = int(maxsize)
                    size = self.convert_bytes(maxsize)
                elif minsize == "-1":
                    if checked:
                        size1 = int(maxsize)
                    size = "< %s" % self.convert_bytes(maxsize)
                else:
                    size1 = int(maxsize)
                    size = "%s-%s" % (self.convert_bytes(minsize),
                                      self.convert_bytes(maxsize))

                if mintime == maxtime:
                    if maxtime == "-1":
                        time = "Negligible"
                    else:
                        if checked:
                            time1 = int(maxtime)
                        time = maxtime
                elif mintime == "-1":
                    if checked:
                        time1 = int(maxtime)
                    time = "< %s" % maxtime
                else:
                    if checked:
                        time1 = int(maxtime)
                    time = "%s-%s" % (mintime, maxtime)

                list.append([ref, checked == "yes", name,
                             gtk.gdk.pixbuf_new_from_file(
                                 path.join(utils.module_path(),
                                           "images/confidentiality%s.png" %
                                           confidentiality)), desc, size,
                             time, size1, time1, int(confidentiality)])

    def fill_list_templates(self, list):
        list.clear()
        for vm in filter(self.filter_custom_template,
                         sorted(self.all['vms'].values(),
                                key=itemgetter('name_label'))):
            vm_uuid = self.vm_filter_uuid(vm["uuid"])
            if vm["is_a_snapshot"]:
                list.append([gtk.gdk.pixbuf_new_from_file(
                    path.join(utils.module_path(), "images/snapshots.png")),
                    vm["name_label"], vm_uuid, "Snapshots"])
            else:
                list.append([gtk.gdk.pixbuf_new_from_file(
                    path.join(utils.module_path(),
                              "images/user_template_16.png")),
                            vm["name_label"], vm_uuid, "Custom"])

        for vm in filter(self.filter_normal_template,
                         sorted(self.all['vms'].values(),
                                key=itemgetter('name_label'))):
            vm_uuid = self.vm_filter_uuid(vm["uuid"])
            if vm["name_label"].lower().count("centos"):
                image = path.join(utils.module_path(), "images/centos.png")
                category = "CentOS"
            elif vm["name_label"].lower().count("windows"):
                image = path.join(utils.module_path(), "images/windows.png")
                category = "Windows"
            elif vm["name_label"].lower().count("debian"):
                image = path.join(utils.module_path(), "images/debian.png")
                category = "Debian"
            elif vm["name_label"].lower().count("red hat"):
                image = path.join(utils.module_path(), "images/redhat.png")
                category = "Red Hat"
            elif vm["name_label"].lower().count("suse"):
                image = path.join(utils.module_path(), "images/suse.png")
                category = "SuSe"
            elif vm["name_label"].lower().count("oracle"):
                image = path.join(utils.module_path(), "images/oracle.png")
                category = "Oracle"
            elif vm["name_label"].lower().count("citrix"):
                image = path.join(utils.module_path(), "images/xen.png")
                category = "Citrix"

            else:
                image = path.join(utils.module_path(),
                                  "images/template_16.png")
                category = "Misc"
            list.append([gtk.gdk.pixbuf_new_from_file(image),
                         vm["name_label"], vm_uuid, category])

    def fill_list_isoimages(self, list):
        list.clear()
        for sr in self.all['SR']:
            if self.all['SR'][sr]['type'] == "iso":
                list.append([self.all['SR'][sr]['name_label'], "", 1, 0])
                for vdi in self.all['SR'][sr]['VDIs']:
                    list.append(["\t" + self.all['VDI'][vdi]['name_label'],
                                 vdi, 0, 1])

    def fill_list_phydvd(self, list):
        list.clear()
        for sr in self.all['SR']:
            if self.all['SR'][sr]['type'] == "udev" \
                    and self.all['SR'][sr]['sm_config']["type"] == "cd":
                if len(self.all['SR'][sr]['PBDs']):
                    vdis = self.all['SR'][sr]['VDIs']
                    for vdi in vdis:
                        list.append(["DVD Drive " +
                                     self.all['VDI'][vdi]['location'][-1:],
                                     vdi])
                    """
                    if self.all['PBD'][pbd]['host'] == self.wine.selected_ref:
                        list.append([self.all['SR'][sr]['name_label'], pbd])
                    """

    def fill_list_networks(self, list, list2):
        list.clear()
        list2.clear()
        i = 0
        for network in self.all['network']:
            if self.all['network'][network]['bridge'] != "xenapi":
                if "automatic" in self.all['network'][network]['other_config'] and \
                        self.all['network'][network]['other_config']["automatic"] == "true":
                    list.append(["interface " + str(i), "auto-generated",
                                 self.all['network'][network]['name_label'].replace('Pool-wide network associated with eth', 'Network '), network])
                    i += 1
            list2.append([self.all['network'][network]['name_label'].replace('Pool-wide network associated with eth', 'Network '), network])

    def fill_management_networks(self, list, network_ref):
        list.clear()
        i = 0
        current = 0
        for network in self.all['network']:
            if self.all['network'][network]['bridge'] != "xenapi":
                if self.all['network'][network]['PIFs'] \
                        and self.all['PIF'][self.all['network'][network]['PIFs'][0]]['bond_slave_of'] == "OpaqueRef:NULL":
                    if network == network_ref:
                        current = i
                    list.append([network, self.all['network'][network]['name_label'].replace('Pool-wide network associated with eth', 'Network ')])
                    i += 1
        return current

    def fill_mamagement_ifs_list(self, list):
        list.clear()
        for pif in self.all['PIF']:
            if self.all['PIF'][pif]['management']:
                network = self.all['network'][self.all['PIF'][pif]['network']]['name_label']
                if self.all['PIF'][pif]['device'][-1:] == "0":
                    text = "<b>Primary</b>" + "\n    <i>" + network + "</i>"
                    list.append([pif, gtk.gdk.pixbuf_new_from_file(path.join(utils.module_path(),
                                                                             "images/prop_networksettings.png")), text])
                else:
                    text = "<b>Interface " + str(self.all['PIF'][pif]['device'][-1:]) + "</b>\n     <i>" + network + "</i>"
                    list.append([pif, gtk.gdk.pixbuf_new_from_file(path.join(utils.module_path(),
                                                                             "images/prop_network.png")), text])

    def fill_listnewvmhosts(self, list):
        list.clear()
        vm_path = 0
        i = 0
        for host in self.all['host'].keys():
            resident_vms = self.all['host'][host]['resident_VMs']
            host_memory = 0
            for resident_vm_uuid in resident_vms:
                if self.all['vms'][resident_vm_uuid]['is_control_domain']:
                    host_memory = self.all['vms'][resident_vm_uuid]['memory_dynamic_max']

            host_metrics_uuid = self.all['host'][host]['metrics']
            host_metrics = self.all['host_metrics'][host_metrics_uuid]
            host_memory = "%s free of %s available (%s total)" % (self.convert_bytes(host_metrics['memory_free']),
                                                                  self.convert_bytes(int(host_metrics['memory_total']) - int(host_memory)),
                                                                  self.convert_bytes(host_metrics['memory_total']))
            if self.all['host'][host]['enabled']:
                vm_path = i
                list.append([gtk.gdk.pixbuf_new_from_file(path.join(utils.module_path(),
                                                                    "images/tree_connected_16.png")),
                             self.all['host'][host]['name_label'], host_memory, host])
            else:
                list.append([gtk.gdk.pixbuf_new_from_file(path.join(utils.module_path(),
                                                                    "images/tree_disconnected_16.png")),
                             self.all['host'][host]['name_label'], host_memory, host])
            i += 1
        return vm_path

    def set_default_storage(self, ref):
        pool_ref = self.all['pool'].keys()[0]
        res = self.connection.pool.set_default_SR(self.session_uuid, pool_ref,
                                                  ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

        res = self.connection.pool.set_suspend_image_SR(self.session_uuid,
                                                        pool_ref, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

        res = self.connection.pool.set_crash_dump_SR(self.session_uuid,
                                                     pool_ref, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def fill_listrepairstorage(self, list, ref):
        list.clear()
        for pbd_ref in self.all['SR'][ref]['PBDs']:
            host = self.all['host'][self.all['PBD'][pbd_ref]["host"]]["name_label"]
            host_ref = self.all['PBD'][pbd_ref]["host"]
            if not self.all['PBD'][pbd_ref]['currently_attached']:
                list.append([pbd_ref, gtk.gdk.pixbuf_new_from_file(path.join(utils.module_path(),
                                                                             "images/storage_broken_16.png")), host,
                             "<span foreground='red'><b>Unplugged</b></span>", host_ref, True])
            else:
                list.append([pbd_ref, gtk.gdk.pixbuf_new_from_file(path.join(utils.module_path(),
                                                                             "images//storage_shaped_16.png")), host,
                             "<span foreground='green'><b>Connected</b></span>", host_ref, False])

    def repair_storage(self, list, ref):
        error = False
        for pbd_ref in self.all['SR'][ref]['PBDs']:
            value = self.connection.Async.PBD.plug(
                self.session_uuid, pbd_ref)["Value"]
            task = self.connection.task.get_record(
                self.session_uuid, value)['Value']
            while task["status"] == "pending":
                task = self.connection.task.get_record(
                    self.session_uuid, value)['Value']

            if len(task["error_info"]):
                print task["error_info"]
                error = True
                gobject.idle_add(lambda: self.wine.builder.get_object(
                    "lblrepairerror").set_markup("<span foreground='red'><b>"
                                                 "Host could not be contacted"
                                                 "</b></span>") and False)
            for i in range(0, list.__len__()):
                if list.get_value(list.get_iter((i,)), 0) == pbd_ref:
                    if error:
                        gobject.idle_add(lambda: list.set_value(list.get_iter((i,)), 3, "<span foreground='red'><b>Unplugged</b></span>") and False)
                    else:
                        gobject.idle_add(lambda: list.set_value(list.get_iter((i,)), 3, "<span foreground='green'><b>Connected</b></span>") and False)
        if not error:
            gobject.idle_add(lambda: self.wine.builder.get_object("lblrepairerror").set_markup("<span foreground='green'><b>All repaired.</b></span>") and False)
        gobject.idle_add(lambda: self.wine.builder.get_object("acceptrepairstorage").set_sensitive(True) and False)
        gobject.idle_add(lambda: self.wine.builder.get_object("cancelrepairstorage").set_label("Close") and False)

    def remove_server_from_pool(self, ref):
        self.connection.pool.eject(self.session_uuid, ref)

    def shutdown_server(self, ref):
        res = self.connection.host.disable(self.session_uuid, ref)
        if "Value" in res:
            res = self.connection.host.shutdown(self.session_uuid, ref)
            if "Value" in res:
                self.track_tasks[res['Value']] = self.host_vm[ref][0]
                return "OK"
            else:
                self.wine.push_alert("%s: %s" % (res["ErrorDescription"][0],
                                                 res["ErrorDescription"][1]))
        else:
            self.wine.push_alert("%s: %s" % (res["ErrorDescription"][0],
                                             res["ErrorDescription"][1]))

    def reboot_server(self, ref):
        res = self.connection.host.disable(self.session_uuid, ref)
        if "Value" in res:
            res = self.connection.host.reboot(self.session_uuid, ref)
            if "Value" in res:
                self.track_tasks[res['Value']] = self.host_vm[ref][0]
                return "OK"
            else:
                self.wine.push_alert("%s: %s" % (res["ErrorDescription"][0],
                                                 res["ErrorDescription"][1]))
        else:
            self.wine.push_alert("%s: %s" % (res["ErrorDescription"][0],
                                             res["ErrorDescription"][1]))

    def set_license_host(self, ref, licensehost, licenseport, edition):
        res = self.connection.host.set_license_server(self.session_uuid, ref,
                                                      {"address": licensehost,
                                                       "port": licenseport})
        if "Value" in res:
            res = self.connection.host.apply_edition(self.session_uuid, ref,
                                                     edition)
            if res not in "Value":
                self.wine.push_alert("%s: %s" % (res["ErrorDescription"][0],
                                                 res["ErrorDescription"][1]))
        else:
            # self.wine.builder.get_object("warninglicense").show()
            self.wine.push_alert("%s: %s" % (res["ErrorDescription"][0],
                                             res["ErrorDescription"][1]))

    def add_server_to_pool(self, widget, ref, server, server_ref, master_ip):
        user = self.wine.xc_servers[server].user
        password = self.wine.xc_servers[server].password
        host = master_ip
        res = self.wine.xc_servers[server].connection.pool.join(
            self.session_uuid, host, user, password)
        if "Value" in res:
            self.track_tasks[res['Value']] = self.host_vm[self.all['host'].keys()[0]][0]
            self.last_pool_data = []
            self.wine.last_host_pool = None
        else:
            self.wine.push_alert("%s: %s" % (res["ErrorDescription"][0],
                                             res["ErrorDescription"][1]))
            if res["ErrorDescription"][0] == "HOSTS_NOT_HOMOGENEOUS":
                self.last_pool_data = [server, server_ref, master_ip]
                self.wine.last_host_pool = server
                self.wine.builder.get_object("forcejoinpool").show()

    def add_server_to_pool_force(self, ref, data=None):
        server = data[0]
        server_ref = data[1]
        master_ip = data[2]
        user = self.wine.xc_servers[server].user
        password = self.wine.xc_servers[server].password
        host = master_ip
        res = self.wine.xc_servers[server].connection.pool.join_force(
            self.session_uuid, host, user, password)
        if "Value" in res:
            self.track_tasks[res['Value']] = self.host_vm[self.all['host'].keys()[0]][0]
        else:
            self.wine.push_alert("%s: %s" % (res["ErrorDescription"][0],
                                             res["ErrorDescription"][1]))

    def delete_pool(self, pool_ref):
        res = self.connection.pool.set_name_label(self.session_uuid, pool_ref,
                                                  "")
        if "Value" in res:
            self.track_tasks[res['Value']] = pool_ref
        else:
            print res
        master = self.all['pool'][pool_ref]['master']
        for host in self.all['host']:
            if host != master:
                res = self.connection.pool.eject(self.session_uuid, pool_ref,
                                                 host)
                if "Value" in res:
                    self.track_tasks[res['Value']] = pool_ref
                else:
                    print res

    def destroy_vm(self, ref, delete_vdi, delete_snap):
        # FIXME
        if delete_vdi:
            if ref in self.all['vms']:
                for vbd in self.all['vms'][ref]['VBDs']:
                    if vbd in self.all['VBD'] \
                            and self.all['VBD'][vbd]['type'] != "CD":
                        res = self.connection.VBD.destroy(self.session_uuid,
                                                          vbd)
                        if "Value" in res:
                            self.track_tasks[res['Value']] = ref
                        else:
                            print res
        if delete_snap:
            all_snapshots = self.all['vms'][ref]['snapshots']
            for snap in all_snapshots:
                self.destroy_vm(snap, True, False)
        res = self.connection.VM.destroy(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def fill_listcopystg(self, list_ref, host):
        list_ref.clear()
        i = 0
        default_sr = 0
        for sr in self.all['SR'].keys():
            storage = self.all['SR'][sr]
            if storage['type'] != "iso" and storage['type'] != "udev":
                if self.default_sr == sr:
                    default_sr = i
                if not self.all['SR'][sr]['PBDs'] \
                        or not self.all['PBD'][self.all['SR'][sr]['PBDs'][0]]['currently_attached'] \
                        or self.all['SR'][sr]['PBDs'] \
                        and self.all['SR'][sr]["allowed_operations"].count("unplug") == 0:
                    pass
                else:
                    phys_size = int(storage['physical_size'])
                    phys_size_bytes = self.convert_bytes(phys_size)
                    virt_alloc = int(storage['virtual_allocation'])
                    free = self.convert_bytes(phys_size - virt_alloc)

                    if self.default_sr == sr:
                        image = path.join(utils.module_path(),
                                          "images/storage_default_16.png")
                    else:
                        image = path.join(utils.module_path(),
                                          "images/storage_shaped_16.png")

                    list_ref.append(
                        [gtk.gdk.pixbuf_new_from_file(image), sr,
                         storage['name_label'],
                         "%s free of %s" % (free, phys_size_bytes)])

                # else:  FIXME: set_sensitive(False) row
                #    list.append([gtk.gdk.pixbuf_new_from_file(path.join(utils.module_path(),
                #                                                        "images/storage_broken_16.png")), sr,
                #                 storage['name_label'],
                #         self.convert_bytes(int(storage['physical_size'])-int(storage['virtual_allocation'])) + " free of " + \
                #         self.convert_bytes(storage['physical_size'])])
                # else:

                i += 1
        return default_sr
