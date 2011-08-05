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
#!/usr/bin/env python
from xva import Xva
from threading import Thread
import gtk
class ProgressBarOXC:
    widget = None
    widget2 = None
    def __init__(self, widget, widget2):
        self.widget = widget
        self.widget2 = widget2
        self.widget.show()
    def update_amount(self, new_amount = None):
        value = "%.2f" % new_amount
        if float(value) > 1: 
            value=1
        self.widget.set_fraction(float(value))
    def update_text(self, text= None):
        self.widget.set_text(text)
    def finish(self):
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU) 
        self.widget2.set_image(image)
        self.widget2.set_label("Close")

class oxcWindowTools:
    """
    Class to manage OXC Tools
    """
    def on_cancelmigratetool_clicked(self, widget, data=None):
        """
        Cancel button pressed on migrate tool
        """
        self.builder.get_object("migratetool").hide()
    def on_acceptmigratetool_clicked(self, widget, data=None):
        """
        Accept button pressed on migrate tool
        """
        machine = Xva(classProgressBar=ProgressBarOXC(self.builder.get_object("progressmigrate"),
                                        self.builder.get_object("cancelmigratetool")))
        if not self.builder.get_object("fileossxenconfig").get_filename() and \
           not self.builder.get_object("fileadddisk").get_filename():
            return
        if self.builder.get_object("fileossxenconfig").get_filename():
            print self.builder.get_object("fileossxenconfig").get_filename()
            params = {}
            execfile(options.config,params)
            if "name" in params: machine.set_name( params['name'] )
            if "vpus" in params: machine.set_vcpus( params['vcpus'] )
            if "kernel" in params:
                if params['kernel'].endswith("hvmloader"):
                    machine.is_hvm()
                else:
                    print "Kernels that are loaded from the Dom0 aren't supported. Use pygrub"
                    sys.exit(255)
            else:
                machine.is_pv()

            if "disk" in params and len(params['disk']) != 0:

                for disk in params['disk']:

                    (path, device, mode) = disk.split(",")
                    path_split = path.split(":")
                    path_split.reverse()
                    machine.add_disk(path_split[0])
                    
     
            else:
     
               print "You need at least 1 Disk, Exiting"
               sys.exit(254)

            

            if "memory" in params:
                try:
                    memory = int(params['memory'] )
                    machine.set_memory( memory * 1024 * 1024)
                except:
                    print "Could parse memory, setting to 256M"
                    machine.set_memory(268435456)
                    
            if "apic" in params and params['apic'] == 0:
                machine.set_apic(False)
            if "acpi" in params and params['acpi'] == 0:
                machine.set_acpi(False)
            if "nx" in params and params['nx'] == 1:
                machine.set_nx(options.nx)
            if "pae" in params and params['pae'] == 0:
                machine.set_pae(False)
        else:
            # Set VM name
            machine.set_name(self.builder.get_object("txtmigratename").get_text())
            # Set VM vcpus
            machine.set_vcpus(self.builder.get_object("spinmigratevcpus").get_text())
            # Set VM ACPI
            machine.set_acpi(self.builder.get_object("checkmigrateacpi").get_active())
            # Set VM ACIP
            machine.set_apic(self.builder.get_object("checkmigrateapic").get_active())
            # Set VM Viridian
            machine.set_viridian(self.builder.get_object("checkmigrateviridian").get_active())
            # Set VM PAE
            machine.set_pae(self.builder.get_object("checkmigratepae").get_active())
            # Set VM NX
            machine.set_nx(self.builder.get_object("checkmigratenx").get_active())
            # Set VM Memory
            memory = int(self.builder.get_object("spinmigratemem").get_text())*1024*1024
            machine.set_memory(memory)
            # Add disk
            machine.add_disk(self.builder.get_object("fileadddisk").get_filename())
            if self.builder.get_object("radiomigratehvm").get_active():
                machine.is_hvm()
            else:
                machine.is_pv()
        sparse = self.builder.get_object("checkmigratesparse").get_active()

        # Save
        import sys
        #sys.stdout = labelStream(self.builder.get_object("lblmigrateprogress"))
        if self.builder.get_object("checkmigrateoutputxva").get_active():
            # If save to xva file..
            filename = self.builder.get_object("txtoutputxva").get_text()
            Thread(target=machine.save_as, kwargs={"filename":filename, "sparse":sparse}).start()
        else:
            # Else export to server..
            server = self.xc_servers[self.selected_host].host
            username = self.xc_servers[self.selected_host].user
            password = self.xc_servers[self.selected_host].password
            ssl = self.xc_servers[self.selected_host].ssl
            Thread(target=machine.save_as, kwargs={"server":server, "username":username,
                               "password":password, "ssl":ssl,  "sparse":sparse}).start()

        widget.set_sensitive(False)
        #self.builder.get_object("migratetool").hide()

    def on_helpmigratetool_clicked(self, widget, data=None):
        """
        Help button pressed on migrate tool
        """
        self.builder.get_object("migratetoolhelp").show()
    def on_closemigratetoolhelp_clicked(self, widget, data=None):
        """
        Closebutton pressed on migrate tool help
        """
        self.builder.get_object("migratetoolhelp").hide()

    def on_btoutputxva_clicked(self, widget, data=None):
        """
        Function called when you press "choose xva file"
        """
        # Show file chooser
        self.builder.get_object("fileoutputxva").show()
    def on_acceptfileoutputxva_clicked(self, widget, data=None):
        """
        Function called when you accept output xva file chooser
        """
        filename = self.builder.get_object("fileoutputxva").get_filename()
        self.builder.get_object("txtoutputxva").set_text(filename)
        self.builder.get_object("fileoutputxva").hide()
    def on_cancelfileoutputxva_clicked(self, widget, data=None):
        """
        Function called when you accept output xva file chooser
        """
        self.builder.get_object("fileoutputxva").hide()


