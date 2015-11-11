# -----------------------------------------------------------------------
# OpenXenManager
#
# Copyright (C) 2009 Alberto Gonzalez Rodriguez alberto@pesadilla.org
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
import os
import xml.dom.minidom
import utils


class oxcSERVERproperties:
    def get_vbd(self, ref):
        return self.all['VBD'][ref]

    def get_vdi(self, ref):
        if ref in self.all['VDI']:
            return self.all['VDI'][ref]
        else:
            return {}

    def get_storage(self, ref):
        return self.all['SR'][ref]

    def get_allowed_vbd_devices(self, ref):
        return self.connection.VM.get_allowed_VBD_devices(self.session_uuid,
                                                          ref)['Value']

    def set_vm_affinity(self, ref, affinity):
        res = self.connection.VM.set_affinity(self.session_uuid, ref, affinity)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_network_name_label(self, ref, name):
        res = self.connection.network.set_name_label(self.session_uuid, ref,
                                                     name)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_network_name_description(self, ref, desc):
        res = self.connection.network.set_name_description(self.session_uuid,
                                                           ref, desc)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_vdi_other_config(self, ref, other_config):
        res = self.connection.VDI.set_other_config(self.session_uuid, ref,
                                                   other_config)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res
 
    def set_vdi_name_label(self, ref_vdi, name):
        res = self.connection.VDI.set_name_label(self.session_uuid, ref_vdi,
                                                 name)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref_vdi
        else:
            print res

    def set_vdi_name_description(self, ref_vdi, desc):
        res = self.connection.VDI.set_name_description(self.session_uuid,
                                                       ref_vdi, desc)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref_vdi
        else:
            print res

    def resize_vdi(self, ref_vdi, size):
        res = self.connection.VDI.resize(self.session_uuid, ref_vdi,
                                         str(int(size)))
        if "Value" in res:
            self.track_tasks[res['Value']] = ref_vdi
        else:
            print res
            
    def set_vbd_userdevice(self, ref_vbd, userdevice):
        res = self.connection.VBD.set_userdevice(self.session_uuid, ref_vbd,
                                                 userdevice)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref_vbd
        else:
            print res

    def set_vbd_mode(self, ref_vbd, mode):
        res = self.connection.VBD.set_mode(self.session_uuid, ref_vbd, mode)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref_vbd
        else:
            print res

    def set_vbd_bootable(self, ref_vbd, bootable):
        res = self.connection.VBD.set_bootable(self.session_uuid, ref_vbd,
                                               bootable)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref_vbd
        else:
            print res

    def set_network_other_config(self, ref, other_config):
        res = self.connection.network.set_other_config(self.session_uuid, ref,
                                                       other_config)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res
  
    def set_network_automatically(self, ref, auto):
        other_config = {'automatic': str(auto).lower()}
        res = self.connection.network.set_other_config(self.session_uuid, ref,
                                                       other_config)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_host_other_config(self, ref, other_config):
        res = self.connection.host.set_other_config(self.session_uuid, ref,
                                                    other_config)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res
 
    def set_host_name_label(self, ref, name):
        res = self.connection.host.set_name_label(self.session_uuid, ref, name)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_host_name_description(self, ref, desc):
        res = self.connection.host.set_name_description(self.session_uuid, ref,
                                                        desc)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res
 
    def set_host_log_destination(self, ref, dest):
        if dest:
            log = {'syslog_destination': dest, }
        else:
            log = {}

        res = self.connection.host.set_logging(self.session_uuid, ref, log)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

        res = self.connection.host.syslog_reconfigure(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_storage_other_config(self, ref, other_config):
        res = self.connection.SR.set_other_config(self.session_uuid, ref,
                                                  other_config)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_storage_name_label(self, ref, name):
        res = self.connection.SR.set_name_label(self.session_uuid, ref, name)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_storage_name_description(self, ref, desc):
        res = self.connection.SR.set_name_description(self.session_uuid, ref,
                                                      desc)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_pool_other_config(self, ref, other_config):
        res = self.connection.pool.set_other_config(self.session_uuid, ref,
                                                    other_config)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_pool_name_label(self, ref, name):
        res = self.connection.pool.set_name_label(self.session_uuid, ref, name)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_pool_name_description(self, ref, desc):
        res = self.connection.pool.set_name_description(self.session_uuid, ref,
                                                        desc)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_vm_other_config(self, ref, other_config):
        res = self.connection.VM.set_other_config(self.session_uuid, ref,
                                                  other_config)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_vm_name_label(self, ref, name):
        res = self.connection.VM.set_name_label(self.session_uuid, ref, name)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_vm_name_description(self, ref, desc):
        res = self.connection.VM.set_name_description(self.session_uuid, ref,
                                                      desc)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_vm_memory(self, ref, memory):
        memory = str(int(memory * 1024 * 1024))

        res = self.connection.VM.set_memory_limits(self.session_uuid, ref,
                                                   str(16777216), memory,
                                                   memory, memory)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            if res["ErrorDescription"][0] == "MESSAGE_METHOD_UNKNOWN":
                # Set Memory Static Minimum
                res = self.connection.VM.set_memory_static_min(self.session_uuid, ref,  memory)
                if "Value" in res:
                    self.track_tasks[res['Value']] = ref
                else:
                    print res
                # Set Memory Dynamic Minimum
                res = self.connection.VM.set_memory_dynamic_min(self.session_uuid, ref, memory)
                if "Value" in res:
                    self.track_tasks[res['Value']] = ref
                else:
                    print res
                # Set Memory Static Max
                res = self.connection.VM.set_memory_static_max(self.session_uuid, ref, memory)
                if "Value" in res:
                    self.track_tasks[res['Value']] = ref
                else:
                    print res
                # Set Memory Dynamic Minimum
                res = self.connection.VM.set_memory_dynamic_max(self.session_uuid, ref, memory)
                if "Value" in res:
                    self.track_tasks[res['Value']] = ref
                else:
                    print res
            else:
                print res

    def set_vm_vcpus(self, ref, vcpus):
        self.connection.VM.set_VCPUs_max(self.session_uuid, ref,
                                         str(int(vcpus)))
        res = self.connection.VM.set_VCPUs_at_startup(self.session_uuid, ref,
                                                      str(int(vcpus)))
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res       # TODO: Add error handling code

    def set_vm_prio(self, ref, prio):
        prio = {'weight': str(int(prio))}
        res = self.connection.VM.set_VCPUs_params(self.session_uuid, ref, prio)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_vm_poweron(self, ref, poweron):
        other_config = self.all['vms'][ref]['other_config']
        other_config["auto_poweron"] = str(poweron).lower()
        res = self.connection.VM.set_other_config(self.session_uuid, ref, other_config)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_vm_bootpolicy(self, ref, bootpolicy):
        res = self.connection.VM.set_PV_args(self.session_uuid, ref, bootpolicy)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_vm_memory_multiplier(self, ref, multiplier):
        res = self.connection.VM.set_HVM_shadow_multiplier(self.session_uuid, ref, float(multiplier))
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_vm_boot_params(self, ref, order):
        boot_params = self.all['vms'][ref]['HVM_boot_params']
        boot_params["order"] = order
        res = self.connection.VM.set_HVM_boot_params(self.session_uuid, ref, boot_params)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def set_pool_custom_fields(self, xml):
        pool_ref = self.all['pool'].keys()[0]
        self.connection.pool.remove_from_gui_config(self.session_uuid, pool_ref, "XenCenter.CustomFields")
        res = self.connection.pool.add_to_gui_config(self.session_uuid, pool_ref, "XenCenter.CustomFields", xml)
        if "Value" in res:
            self.all['pool'][pool_ref]["gui_config"]["XenCenter.CustomFields"] = xml
            self.track_tasks[res['Value']] = pool_ref
        else:
            print res

    def fill_listcustomfields(self, clist):
        clist.clear()
        pool_ref = self.all['pool'].keys()[0]
        if "XenCenter.CustomFields" in self.all['pool'][pool_ref]["gui_config"]:
            dom = xml.dom.minidom.parseString(
                self.all['pool'][pool_ref]["gui_config"]["XenCenter.CustomFields"])
            for node in dom.getElementsByTagName("CustomFieldDefinition"):
                name = node.attributes.getNamedItem("name").value
                ctype = node.attributes.getNamedItem("type").value
                clist.append((["%s (%s)" % (name, str(ctype)), name, ctype]))

    def fill_listhomeserver(self, list, ref):
        list.clear()
        path = 0
        i = 0
        for host in self.all['host'].keys():
            resident_vms = self.all['host'][host]['resident_VMs']
            host_memory = 0
            vm_memory = 0
            for resident_vm_uuid in resident_vms:
                if self.all['vms'][resident_vm_uuid]['is_control_domain']:
                    host_memory = int(self.all['vms'][resident_vm_uuid]['memory_dynamic_max'])
                else:     
                    vm_memory += int(self.all['vms'][resident_vm_uuid]['memory_dynamic_max'])
            
            host_metrics_uuid = self.all['host'][host]['metrics']
            host_metrics = self.all['host_metrics'][host_metrics_uuid]
            hostmemory = "%s free of %s available (%s total)" % \
                (self.convert_bytes(int(host_metrics['memory_total'])-vm_memory-host_memory),
                 self.convert_bytes(int(host_metrics['memory_total']) - host_memory),
                 self.convert_bytes(host_metrics['memory_total']))
            if self.all['host'][host]['enabled']:
                if host == ref:
                    path = i 
                list.append([host, gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                             "images/tree_connected_16.png")),
                             self.all['host'][host]['name_label'], hostmemory, ])
            i += 1
        return path

    def fill_vdi_location(self, ref, list):
        list.clear()
        i = 0
        selected = 0
        for sr in self.all['SR'].keys():
            if self.all['SR'][sr]['name_label'] != "XenServer Tools":
                if sr == ref:
                    selected = i
                    name = "<b>" + self.all['SR'][sr]['name_label'] + "</b>"
                else:
                    name = self.all['SR'][sr]['name_label']
                if len(self.all['SR'][sr]['PBDs']) == 0 or self.all['PBD'][self.all['SR'][sr]['PBDs'][0]]['currently_attached'] == False \
                    or len(self.all['SR'][sr]['PBDs']) > 0 and self.all['SR'][sr]["allowed_operations"].count("unplug") ==  0:
                        list.append([sr, gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                                   "images/storage_broken_16.png")),
                                     name])
                else:
                    if sr == self.default_sr:
                        list.append([sr, gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                                   "images/storage_default_16.png")),
                                     name])
                    else:
                        list.append([sr, gtk.gdk.pixbuf_new_from_file(os.path.join(utils.module_path(),
                                                                                   "images/storage_shaped_16.png")),
                                     name])
                i += 1
        return selected


