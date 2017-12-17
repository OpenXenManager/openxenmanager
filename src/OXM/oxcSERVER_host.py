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
from os import path
import gtk
from threading import Thread
from oxcSERVER_host_nics import *
from oxcSERVER_host_network import *
import utils


class oxcSERVERhost(oxcSERVERhostnics, oxcSERVERhostnetwork):
    def upload_patch(self, ref, filename):
        import httplib
        import os
        task_uuid = self.connection.task.create(self.session_uuid,
                                                "Uploading Patch",
                                                "Uploading Patch %s " %
                                                filename)
        self.track_tasks[task_uuid['Value']] = "Upload.Patch"
        size = os.stat(filename)[6]
        url = self.wine.selected_ip
        conn = httplib.HTTPS(url)
        conn.putrequest('PUT', '/pool_patch_upload?session_id=%s&task_id=%s' %
                        (self.session_uuid, task_uuid['Value']))
        conn.putheader('Content-Type', 'text/plain')
        conn.putheader('Content-Length', str(size))
        conn.endheaders()
        fp = open(filename, 'rb')
        blocknum = 0
        uploaded = 0
        blocksize = 4096
        while not self.halt_import:
            bodypart = fp.read(blocksize)
            blocknum += 1
            if blocknum % 10 == 0:
                uploaded += len(bodypart)

            if not bodypart:
                break
            conn.send(bodypart)

        fp.close()
        print "Finish upload.."

    def remove_patch(self, ref, patch):
        res = self.connection.Async.pool_patch.destroy(self.session_uuid,
                                                       patch)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def apply_patch(self, ref, patch):
        res = self.connection.Async.pool_patch.apply(self.session_uuid, ref,
                                                     patch)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def reconfigure_pif(self, pif_ref, conf_mode, ip, mask, gw, dns, ref):
        res = self.connection.PIF.reconfigure_ip(self.session_uuid, pif_ref,
                                                 conf_mode, ip, mask, gw, dns)
        if "Value" in res:
            self.track_tasks[res['Value']] = self.host_vm[ref][0]
        else:
            print res

    def change_server_password(self, old, new):
        self.connection.session.change_password(self.session_uuid, old, new)
        self.password = new

    def install_license_key(self, ref, filename):
        encoded = open(filename, "rb").read().encode("base64").replace("\n",
                                                                       "")
        res = self.connection.host.license_apply(self.session_uuid, ref,
                                                 encoded)
        if "Value" in res:
            print res
            self.track_tasks[res['Value']] = self.host_vm[ref][0]
        else:
            self.wine.builder.get_object("warninglicense").show()

    def join_pool(self, host, user, password):
        res = self.connection.pool.join(self.session_uuid, host,
                                        user, password)
        if "Value" in res:
            self.track_tasks[res['Value']] = self.host_vm[
                self.all['host'].keys()[0]][0]
        else:
            self.wine.push_alert("%s: %s" % (res["ErrorDescription"][0],
                                             res["ErrorDescription"][1]))

    def fill_vms_which_prevent_evacuation(self, ref, list):
        list.clear()
        vms = self.connection.host.get_vms_which_prevent_evacuation(
            self.session_uuid, ref)["Value"]
        for vm in vms.keys():
            # vms[vm][0]
            list.append([gtk.gdk.pixbuf_new_from_file(path.join(
                utils.module_path(), "images/tree_running_16.png")),
                self.all['vms'][vm]['name_label'],
                "Suspend or shutdown VM"])

    def enter_maintancemode(self, ref):
        maint_mode = ["MAINTENANCE_MODE_EVACUATED_VMS_MIGRATED",
                      "MAINTENANCE_MODE_EVACUATED_VMS_HALTED",
                      "MAINTENANCE_MODE_EVACUATED_VMS_SUSPENDED",
                      "MAINTENANCE_MODE"]
        res = self.connection.Async.host.evacuate(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = self.host_vm[ref][0]
            self.connection.host.disable(self.session_uuid, ref)

            for conf in maint_mode:
                self.connection.host.remove_from_other_config(
                    self.session_uuid, ref, conf)

            for conf in maint_mode:
                if conf != "MAINTENANCE_MODE":
                    self.connection.host.add_to_other_config(
                        self.session_uuid, ref, conf, "")
                else:
                    self.connection.host.add_to_other_config(
                        self.session_uuid, ref, conf, True)
        else:
            print res

    def exit_maintancemode(self, ref):
        maint_mode = ["MAINTENANCE_MODE_EVACUATED_VMS_MIGRATED",
                      "MAINTENANCE_MODE_EVACUATED_VMS_HALTED",
                      "MAINTENANCE_MODE_EVACUATED_VMS_SUSPENDED",
                      "MAINTENANCE_MODE"]
        self.connection.host.enable(self.session_uuid, ref)

        for conf in maint_mode:
            self.connection.host.remove_from_other_config(
                self.session_uuid, ref, conf)

    def thread_restore_server(self, ref, filename, name):
        Thread(target=self.restore_server, args=(ref, filename, name)).start()

    def thread_backup_server(self, ref, filename, name):
        Thread(target=self.backup_server, args=(ref, filename, name)).start()

    def thread_host_download_logs(self, ref, filename, name):
        Thread(target=self.host_download_logs,
               args=(ref, filename, name)).start()

    def create_pool(self, name, desc):
        pool_ref = self.all['pool'].keys()[0]
        res = self.connection.pool.set_name_label(self.session_uuid, pool_ref,
                                                  name)
        res = self.connection.pool.set_name_description(self.session_uuid,
                                                        pool_ref, desc)
        if "Value" in res:
            self.track_tasks[res['Value']] = pool_ref
        else:
            print res

    def get_external_auth(self, ref):
        if "external_auth_type" in self.all['host'][ref]:
            return [self.all['host'][ref]['external_auth_type'],
                    self.all['host'][ref]['external_auth_service_name'],
                    self.all['host'][ref]['external_auth_configuration']]
        else:
            return ["", "", ""]

    def fill_domain_users(self, ref, list_users):
        try:
            users_logged = self.connection.session.get_all_subject_identifiers(
                self.session_uuid)['Value']
            users = {}
            if self.all['host'][ref]['external_auth_type']:
                list_users.append(("000", "", "-", "Local root account\n("
                                                   "Always granted access)"))
                for user in self.all['subject']:
                    users[self.all['subject'][user]['subject_identifier']] = \
                        self.all['subject'][user]['other_config']
                    roles = []
                    for role in self.all['subject'][user]['roles']:
                        roles.append(self.all['role'][role]['name_label'])

                    users[self.all['subject'][user]['subject_identifier']][
                        'roles'] = roles
                    users[self.all['subject'][user]['subject_identifier']][
                        'ref'] = user
                    if self.all['subject'][user][
                            'subject_identifier'] in users_logged:
                        logged = "Yes"
                    else:
                        logged = "No"

                    list_users.append((
                        user, " ".join(roles), logged,
                        self.all['subject'][user]['other_config'][
                            'subject-gecos'] + "\n" + self.all['subject'][
                            user]['other_config']['subject-name']))
        except KeyError:
            pass

    def has_hardware_script(self, ref):
        error = self.connection.host.call_plugin(self.session_uuid, ref,
                                                 "dmidecode", "test", {})
        return "XENAPI_MISSING_PLUGIN" not in error['ErrorDescription']

    def fill_host_hardware(self, ref):
        hwinfo = self.connection.host.call_plugin(self.session_uuid, ref,
                                                  "dmidecode", "main",
                                                  {})['Value']
        relation = {}
        keys = []
        for line in hwinfo.split("\n"):
            if not line:
                continue
            if line[0] != "\t" and line not in relation:
                relation[line] = []
                key = line
                keys.append(key)
            else:
                if line[0] == "\t":
                    relation[key].append(line)
                else:
                    relation[key].append("\n")

        for ch in self.wine.builder.get_object("hosttablehw").get_children():
            self.wine.builder.get_object("hosttablehw").remove(ch)

        for key in keys:
            self.add_box_hardware(key, relation[key])

    def add_box_hardware(self, title, text):
        vboxframe = gtk.Frame()
        vboxframe.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        vboxchild = gtk.Fixed()
        vboxevent = gtk.EventBox()
        vboxevent.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        vboxevent.add(vboxchild)
        vboxframe.add(vboxevent)
        vboxchildlabel1 = gtk.Label()
        vboxchildlabel1.set_selectable(True)
        vboxchildlabel1.set_markup("<b>" + title + "</b>")
        vboxchild.put(vboxchildlabel1, 5, 5)
        vboxchildlabel2 = gtk.Label()
        vboxchildlabel2.set_selectable(True)
        vboxchildlabel2.set_text('\n'.join(text) + "\n")
        vboxchild.put(vboxchildlabel2, 5, 35)
        self.wine.builder.get_object("hosttablehw").add(vboxframe)
        self.wine.builder.get_object("hosttablehw").show_all()

    def fill_host_network(self, ref, list_ref):
        list_ref.clear()
        for network_key in self.all['network'].keys():
            network = self.all['network'][network_key]

            if network['bridge'] != "xenapi":
                name = network['name_label'].replace('Pool-wide network '
                                                     'associated with eth',
                                                     'Network ')
                desc = network['name_description']
                auto = "no"
                if "automatic" in network['other_config']:
                    if network['other_config']['automatic'] == "true":
                        auto = "Yes"
                    else:
                        auto = "No"
                pifs = [PIF for PIF in self.all['PIF'].values() if
                        PIF['network'] == network_key]

                vlan = "-"
                linkstatus = "-"
                macaddress = "-"
                nic = "-"
                mtu = "-"
                for pif in pifs:
                    if pif['host'] == ref:
                        nic = "NIC " + pif['device'][-1:]
                        if pif:
                            if pif['VLAN'] != "-1":
                                vlan = pif['VLAN']
                            if pif['metrics'] in self.all['PIF_metrics'] and \
                                    self.all['PIF_metrics'][pif['metrics']]['carrier']:  # Link status
                                linkstatus = "Connected"
                            if pif['MAC'] != "fe:ff:ff:ff:ff:ff":
                                macaddress = pif['MAC']
                            if macaddress != "-" and linkstatus == "-":
                                linkstatus = "Disconnected"

                            mtu = pif['MTU']

                # FIXME: not bond networks
                net_tuple = (name, desc, nic, vlan, auto, linkstatus,
                             macaddress, mtu, network_key)
                list_ref.append(net_tuple)

    def fill_host_nics(self, ref, list_ref):
        list_ref.clear()
        for pif_key in self.all['PIF'].keys():
            if self.all['PIF'][pif_key]['host'] == ref:
                if self.all['PIF'][pif_key]['metrics'] != "OpaqueRef:NULL":
                    if self.all['PIF'][pif_key]['metrics'] not in \
                            self.all['PIF_metrics']:
                        continue
                    pif_metric = self.all['PIF_metrics'][self.all['PIF'][pif_key]['metrics']]
                    pif = self.all['PIF'][pif_key]

                    if pif_metric['duplex']:
                        duplex = "full"
                    else:
                        duplex = "half"
                    if pif:
                        if "MAC" in pif:
                            mac = pif['MAC']
                        else:
                            mac = ""
                        connected = "Disconnected"
                        if pif_metric['carrier']:
                            connected = "Connected"
                        if connected == "Connected":
                            speed = pif_metric['speed'] + " mbit/s"
                        else:
                            speed = ""
                        if pif_metric['pci_bus_path'] != "N/A" and pif['physical'] is not False:
                            list_ref.append(("NIC %s" % pif['device'][-1:], mac, connected,
                                             speed, duplex, pif_metric['vendor_name'],
                                             pif_metric['device_name'], pif_metric['pci_bus_path'],
                                             pif_key))
                        else:
                            if pif['bond_master_of']:
                                devices = []
                                for slave in self.all['Bond'][pif['bond_master_of'][0]]['slaves']:
                                    devices.append(self.all['PIF'][slave]['device'][-1:])
                                devices.sort()
                                list_ref.append(("Bond %s" % ('+'.join(devices)), mac, connected,
                                                 speed, duplex, pif_metric['vendor_name'],
                                                 pif_metric['device_name'], pif_metric['pci_bus_path'],
                                                 pif_key))
                            else:
                                pass

                else:
                    pif = self.all['PIF'][pif_key]
                    if "MAC" in pif:
                        mac = pif['MAC']
                    else:
                        mac = ""
                    connected = "Disconnected"
                    if pif['bond_master_of']:
                        devices = []
                        if pif['bond_master_of'][0] in self.all['Bond']:
                            for slave in self.all['Bond'][pif['bond_master_of'][0]]['slaves']:
                                devices.append(self.all['PIF'][slave]['device'][-1:])
                            devices.sort()
                            list_ref.append(("Bond %s" % ('+'.join(devices)),
                                             mac, connected, "-", "-", "-",
                                             "-", "-", pif_key))
                    else:
                        list_ref.append(("NIC %s" % pif['device'][-1:], mac,
                                         connected, "-", "-", "-", "-", "-",
                                         pif_key))
