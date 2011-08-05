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
import re
import gtk

class oxcWindowStorage:
    """
    Class to manage "storage" elements
    """
    reattach_lun = None
    def on_rescanisos_clicked(self, widget, data=None):
        self.xc_servers[self.selected_host].rescan_isos(self.selected_ref)

    def on_treerepairstorage_cursor_changed(self, widget, data=None):
        widget.get_selection().unselect_all()

    def on_acceptnewstgreattachnfs_clicked(self, widget, data=None):
        """
        Function called when you press accept on "reattach window storage" (nfs)
        """
        name = self.builder.get_object("txtnewstgnfsname").get_text()
        host, path = self.builder.get_object("txtnewstgnfspath").get_text().split(":", 2)
        options = self.builder.get_object("txtnewstgnfsoptions").get_text()
        create = self.builder.get_object("radiocreatenewsr").get_active()
        ref = None
        treereattachnewstgnfs = self.builder.get_object("treereattachnewstgnfs")
        listreattachnewstgnfs = self.builder.get_object("listreattachnewstgnfs")
        selection = treereattachnewstgnfs.get_selection()
        if selection.get_selected()[1]:
            iter = selection.get_selected()[1]
            uuid = listreattachnewstgnfs.get_value(iter, 0)
        self.xc_servers[self.selected_host].reattach_nfs_vhd(self.selected_ref, name, host, path, options, create, uuid)
        # Hide confirmation window
        self.builder.get_object("newstgreattachnfs").hide()
        # Hide new storage window
        self.builder.get_object("newstorage").hide()

    def on_acceptnewstgreattachaoe_clicked(self, widget, data=None):
        """
        Function called when you press accept on "reattach window storage" (aoe)
        """
        name = self.builder.get_object("txtnewstgaoename").get_text()
        path = self.builder.get_object("txtnewstgaoepath").get_text()
        create = self.builder.get_object("radiocreatenewaoe").get_active()
        ref = None
        treereattachnewstgnfs = self.builder.get_object("treereattachnewstgaoe")
        listreattachnewstgnfs = self.builder.get_object("listreattachnewstgaoe")
        selection = treereattachnewstgnfs.get_selection()
        if selection.get_selected()[1]:
            iter = selection.get_selected()[1]
            uuid = listreattachnewstgnfs.get_value(iter, 0)
        self.xc_servers[self.selected_host].reattach_aoe(self.selected_ref, name, path, create, uuid)
        # Hide confirmation window
        self.builder.get_object("newstgreattachaoe").hide()
        # Hide new storage window
        self.builder.get_object("newstorage").hide()

    def on_treehbalun_cursor_changed(self, widget, data=None):
        listhbalun =  self.builder.get_object("listhbalun")
        selection = widget.get_selection()
        if selection.get_selected()[1]:
            iter = selection.get_selected()[1]
            if listhbalun.get_value(iter, 1):
                uuid = listhbalun.get_value(iter, 2)
                self.builder.get_object("finishnewstorage").set_sensitive(True)
            else:
                self.builder.get_object("finishnewstorage").set_sensitive(False)
        else:
            self.builder.get_object("finishnewstorage").set_sensitive(False)
    def on_cancelnewstgreattachnfs_clicked(self, widget, data=None):
        """
        Function called when you press cancel on "reattach window storage" (nfs)
        """
        # Hide confirmation window
        self.builder.get_object("newstgreattachnfs").hide()
    def on_cancelnewstgreattachaoe_clicked(self, widget, data=None):
        """
        Function called when you press cancel on "reattach window storage" (aoe)
        """
        # Hide confirmation window
        self.builder.get_object("newstgreattachaoe").hide()
    def on_finishnewstorage_clicked(self, widget, data=None):
        """
        Function called when you press "Finish" on new storage wizard
        """
        page = self.builder.get_object("tabboxnewstorage").get_current_page()
        if page == 1:
            # NFS VHD
            name = self.builder.get_object("txtnewstgnfsname").get_text()
            host, path = self.builder.get_object("txtnewstgnfspath").get_text().split(":", 2)
            options = self.builder.get_object("txtnewstgnfsoptions").get_text()
            create = self.builder.get_object("radiocreatenewsr").get_active()
            if not create:
                labels = self.builder.get_object("newstgreattachnfs").get_children()[0].get_children()[0].get_children()[1].get_children()
                treereattachnewstgnfs = self.builder.get_object("treereattachnewstgnfs")
                listreattachnewstgnfs = self.builder.get_object("listreattachnewstgnfs")
                selection = treereattachnewstgnfs.get_selection()
                if selection.get_selected()[1]:
                    iter = selection.get_selected()[1]
                    uuid = listreattachnewstgnfs.get_value(iter, 0)
                    labels[0].set_text(labels[0].get_text().replace("{0}", uuid))
                    self.builder.get_object("newstgreattachnfs").show()
            else:
                self.xc_servers[self.selected_host].create_nfs_vhd(self.selected_ref, name, host, path, options, create)
                self.builder.get_object("newstorage").hide()
        elif page == 2:
            # iSCSI
            name = self.builder.get_object("txtiscsiname").get_text()
            host = self.builder.get_object("txtiscsitarget").get_text()
            port = self.builder.get_object("txtiscsiport").get_text()
            chapuser = None
            chapsecret = None
            if self.builder.get_object("checkscsichap").get_active():
                chapuser = self.builder.get_object("txtiscsichapuser").get_text()
                chapsecret = self.builder.get_object("txtiscsichapsecret").get_text()

            combotargetiqn = self.builder.get_object("combotargetiqn")
            listtargetiqn = self.builder.get_object("listtargetiqn")
            combotargetlun = self.builder.get_object("combotargetlun")
            listtargetlun = self.builder.get_object("listtargetlun")
            targetiqn = listtargetiqn.get_value(combotargetiqn.get_active_iter(), 0)
            targetlun = listtargetlun.get_value(combotargetlun.get_active_iter(), 0)
            self.reattach_lun = self.xc_servers[self.selected_host].check_iscsi(self.selected_ref, name, host, port, targetlun, targetiqn, chapuser, chapsecret)
            if self.reattach_lun: 
                # If create_iscsi return an uuid.. then ask confirmation for reattach, format or cancel
                self.builder.get_object("reattachformatiscsidisk").show()
            else:
                # If not, only ask for format or cancel
                self.builder.get_object("formatiscsidisk").show()
        elif page == 3:
            # Hardware HBA
            treehbalun = self.builder.get_object("treehbalun")
            listhbalun = self.builder.get_object("listhbalun")
            selection = treehbalun.get_selection()
            if selection.get_selected()[1]:
                iter = selection.get_selected()[1]
                text = listhbalun.get_value(iter, 0)
                uuid = listhbalun.get_value(iter, 2)
                path = listhbalun.get_value(iter, 3)
                option = self.xc_servers[self.selected_host].check_hardware_hba(self.selected_ref, uuid, text)
                if option[0] == 0:
                    # Ok, do you want format it?
                    self.builder.get_object("formatdisklun").show()
                elif option[0] == 1:
                    # Sorry, detach first
                    self.builder.get_object("detachhbalun").show()
                    label = self.builder.get_object("detachhbalun").get_children()[0].get_children()[0].get_children()[1].get_children()[0]
                    label.set_text(label.get_text().replace("{0}", option[1]).replace("{1}", option[2]))
                elif option[0] == 2:
                    # Do you want reattach?
                    self.builder.get_object("reattachhbalun").show()
                    label = self.builder.get_object("reattachhbalun").get_children()[0].get_children()[0].get_children()[1].get_children()[0]
                    label.set_text(label.get_text().replace("{0}", option[1]))
                elif option[0] == 3:
                    # Do you want reattach or format?
                    self.builder.get_object("reattachformathbalun").show()
                    label = self.builder.get_object("reattachformathbalun").get_children()[0].get_children()[0].get_children()[1].get_children()[0]
                    label.set_text(label.get_text().replace("{0}", option[1]))
    
        elif page == 4:
            # CIFS ISO
            name = self.builder.get_object("txtnewstgcifsname").get_text()
            sharename = self.builder.get_object("txtnewstgcifspath").get_text()
            options = self.builder.get_object("txtnewstgcifsoptions").get_text()
            if self.builder.get_object("checknewstgcifslogin").get_active():
                username = self.builder.get_object("txtnewstgcifsusername").get_text()
                password = self.builder.get_object("txtnewstgcifspassword").get_text()
            else:
                username = ""
                password = ""
            # Check if is a reattach or a new attach
            if self.reattach_storage:
                 # reattach_nfs_iso returns 0 if iso library was attached correctly
                if self.xc_servers[self.selected_host].reattach_cifs_iso(self.selected_ref, name, \
                        sharename, options, username,password) == 0:
                        # hide the window
                        self.builder.get_object("newstorage").hide()
            else:
                # create_cifs_iso returns 0 if iso library was attached correctly
                if self.xc_servers[self.selected_host].create_cifs_iso(self.selected_ref, name, \
                        sharename, options, username,password) == 0:
                    # hide the window
                    self.builder.get_object("newstorage").hide()
            pass
        elif page == 5:
            # NFS ISO
            name = self.builder.get_object("txtnewstgnfsisoname").get_text()
            sharename = self.builder.get_object("txtnewstgnfsisopath").get_text()
            options = self.builder.get_object("txtnewstgnfsisooptions").get_text()
            # Check if is a reattach or a new attach
            if self.reattach_storage:
                # reattach_nfs_iso returns 0 if iso library was attached correctly

                if self.xc_servers[self.selected_host].reattach_nfs_iso(self.selected_ref, name, sharename, options) == 0:
                    # hide the window
                    self.builder.get_object("newstorage").hide()
            else:
                # create_nfs_iso returns 0 if iso library was attached correctly
                if self.xc_servers[self.selected_host].create_nfs_iso(self.selected_ref, name, sharename, options) == 0:
                    # hide the window
                    self.builder.get_object("newstorage").hide()
        if page == 6:
            # Experimental AOE 
            name = self.builder.get_object("txtnewstgaoename").get_text()
            path = self.builder.get_object("txtnewstgaoepath").get_text()
            create = self.builder.get_object("radiocreatenewaoe").get_active()
            if not create:
                labels = self.builder.get_object("newstgreattachaoe").get_children()[0].get_children()[0].get_children()[1].get_children()
                treereattachnewstgnfs = self.builder.get_object("treereattachnewstgaoe")
                listreattachnewstgnfs = self.builder.get_object("listreattachnewstgaoe")
                selection = treereattachnewstgnfs.get_selection()
                if selection.get_selected()[1]:
                    iter = selection.get_selected()[1]
                    uuid = listreattachnewstgnfs.get_value(iter, 0)
                    labels[0].set_text(labels[0].get_text().replace("{0}", uuid))
                    self.builder.get_object("newstgreattachaoe").show()
            else:
                self.xc_servers[self.selected_host].create_aoe(self.selected_ref, name, path, create)
                self.builder.get_object("newstorage").hide()

    def on_cancelformatdisklun_clicked(self, widget, data=None):
        """
        Function called when you cancel format disk confirmation (hba) 
        """
        self.builder.get_object("formatdisklun").hide()
    def on_accepformatdisklun_clicked(self, widget, data=None):
        """
        Function called when you accept format disk confirmation (hba) 
        and function called when you choose Format button on reattach/format
        disk confirmation (hba) 
        """
        treehbalun = self.builder.get_object("treehbalun")
        listhbalun = self.builder.get_object("listhbalun")
        selection = treehbalun.get_selection()
        if selection.get_selected()[1]:
            iter = selection.get_selected()[1]
            text = listhbalun.get_value(iter, 0)
            uuid = listhbalun.get_value(iter, 2)
            path = listhbalun.get_value(iter, 3)
            name = self.builder.get_object("txthbaname").get_text()
            option = self.xc_servers[self.selected_host].format_hardware_hba(self.selected_ref, uuid, name, path)

        self.builder.get_object("formatdisklun").hide()
        self.builder.get_object("newstorage").hide()
    def on_acceptdetachhbalun_clicked(self, widget, data=None):
        """
        Function called when you accept information dialog informing you must detach the SR
        """
        self.builder.get_object("detachhbalun").hide()
    def on_cancelreattachhbalun_clicked(self, widget, data=None):
        """
        Function called when you cancel reattach disk confirmation (hba) 
        """
        self.builder.get_object("reattachhbalun").hide()
    def on_acceptreattachhbalun_clicked(self, widget, data=None):
        """
        Function called when you accept reattach disk confirmation (hba) 
        """
        treehbalun = self.builder.get_object("treehbalun")
        listhbalun = self.builder.get_object("listhbalun")
        selection = treehbalun.get_selection()
        option = 1
        if selection.get_selected()[1]:
            iter = selection.get_selected()[1]
            text = listhbalun.get_value(iter, 0)
            uuid = listhbalun.get_value(iter, 2)
            path = listhbalun.get_value(iter, 3)
            name = self.builder.get_object("txthbaname").get_text()
            option = self.xc_servers[self.selected_host].reattach_hardware_hba(self.selected_ref, uuid, name, path)
        self.builder.get_object("reattachhbalun").hide()
        if option == 0:
            self.builder.get_object("newstorage").hide()
    def on_acceptareattachformathbalun_clicked(self, widget, data=None):
        """
        Function called when you press reattach button reattach/format disk confirmation (hba) 
        """
        treehbalun = self.builder.get_object("treehbalun")
        listhbalun = self.builder.get_object("listhbalun")
        selection = treehbalun.get_selection()
        option = 1
        if selection.get_selected()[1]:
            iter = selection.get_selected()[1]
            text = listhbalun.get_value(iter, 0)
            uuid = listhbalun.get_value(iter, 2)
            path = listhbalun.get_value(iter, 3)
            name = self.builder.get_object("txthbaname").get_text()
            option = self.xc_servers[self.selected_host].reattach_and_introduce_hardware_hba(self.selected_ref, uuid, name, path)
        self.builder.get_object("reattachformathbalun").hide()
        if option == 0:
            self.builder.get_object("newstorage").hide()
    def on_cancelreattachformathbalun_clicked(self, widget, data=None):
        """
        Function called when you cancel reattach/format disk confirmation (hba) 
        """
        self.builder.get_object("reattachformathbalun").hide()

    def on_acceptformatiscsidisk_clicked(self, widget, data=None):
        """
        Function called when you accept "format" scsi lun confirmation dialog
        """
        name = self.builder.get_object("txtiscsiname").get_text()
        host = self.builder.get_object("txtiscsitarget").get_text()
        port = self.builder.get_object("txtiscsiport").get_text()
        chapuser = None
        chapsecret = None
        if self.builder.get_object("checkscsichap").get_active():
            chapuser = self.builder.get_object("txtiscsichapuser").get_text()
            chapsecret = self.builder.get_object("txtiscsichapsecret").get_text()

        combotargetiqn = self.builder.get_object("combotargetiqn")
        listtargetiqn = self.builder.get_object("listtargetiqn")
        combotargetlun = self.builder.get_object("combotargetlun")
        listtargetlun = self.builder.get_object("listtargetlun")
        targetiqn = listtargetiqn.get_value(combotargetiqn.get_active_iter(), 0)
        targetlun = listtargetlun.get_value(combotargetlun.get_active_iter(), 0)
        # Create formating the SCSI lun
        self.xc_servers[self.selected_host].create_iscsi(self.selected_ref, name, host, port, targetlun, targetiqn, chapuser, chapsecret)
        # Hide the dialog
        self.builder.get_object("formatiscsidisk").hide()
        self.builder.get_object("reattachformatiscsidisk").hide()
        # hide the window
        self.builder.get_object("newstorage").hide()

    def on_reattachscsidisk_clicked(self, widget, data=None):
        """
        Function called when you choose "reattach" scsi lun confirmation dialog
        """
        name = self.builder.get_object("txtiscsiname").get_text()
        host = self.builder.get_object("txtiscsitarget").get_text()
        port = self.builder.get_object("txtiscsiport").get_text()
        chapuser = None
        chapsecret = None
        if self.builder.get_object("checkscsichap").get_active():
            chapuser = self.builder.get_object("txtiscsichapuser").get_text()
            chapsecret = self.builder.get_object("txtiscsichapsecret").get_text()

        combotargetiqn = self.builder.get_object("combotargetiqn")
        listtargetiqn = self.builder.get_object("listtargetiqn")
        combotargetlun = self.builder.get_object("combotargetlun")
        listtargetlun = self.builder.get_object("listtargetlun")
        targetiqn = listtargetiqn.get_value(combotargetiqn.get_active_iter(), 0)
        targetlun = listtargetlun.get_value(combotargetlun.get_active_iter(), 0)
        # Reattach the SCSI lun
        self.xc_servers[self.selected_host].reattach_iscsi(self.selected_ref, name, host, port, targetlun, targetiqn, chapuser, chapsecret, self.reattach_lun)

        # Hide the dialog
        self.builder.get_object("reattachformatiscsidisk").hide()
        # hide the window
        self.builder.get_object("newstorage").hide()

    def on_cancelformatiscsidisk_clicked(self, widget, data=None):
        """
        Function called when you cancel "format" scsi lun confirmation dialog
        """
        # Hide the dialog
        self.builder.get_object("formatiscsidisk").hide()
    def on_cancelreattachscsidisk_clicked(self, widget, data=None):
        """
        Function called when you cancel "reattach format" scsi lun confirmation dialog
        """
        # Hide the dialog
        self.builder.get_object("reattachformatiscsidisk").hide()
    def on_nextnewstorage_clicked(self, widget, data=None):
        """
        Function called when you press "Next" on new storage wizard
        """
        mapping = {
                    "radionewstgnfsvhd" : 1,  
                    "radionewstgiscsi" : 2,
                    "radionewstghwhba" : 3,
                    "radionewstgcifs" : 4, 
                    "radionewstgnfsiso": 5,
                    "radionewstgaoe": 6
                  }
        for radio in mapping:
            if self.builder.get_object(radio).get_active():
                # Set the correct tab for selected storage type
                self.builder.get_object("tabboxnewstorage").set_current_page(mapping[radio])
        # Empty previous text/set default texts
        self.builder.get_object("txtnewstgnfsname").set_text("NFS virtual disk storage")
        self.builder.get_object("txtnewstgnfspath").set_text("")
        self.builder.get_object("txtnewstgnfsoptions").set_text("")
        self.builder.get_object("listreattachnewstgnfs").clear()

        self.builder.get_object("txtiscsiname").set_text("iSCSI virtual disk storage")
        self.builder.get_object("txtiscsitarget").set_text("")
        self.builder.get_object("txtiscsiport").set_text("3260")
        self.builder.get_object("txtiscsichapuser").set_text("")
        self.builder.get_object("txtiscsichapsecret").set_text("")
        self.builder.get_object("listtargetiqn").clear()
        self.builder.get_object("listtargetlun").clear()

        self.builder.get_object("txtnewstgcifsname").set_text("CIFS ISO library")
        self.builder.get_object("txtnewstgcifspath").set_text("")
        self.builder.get_object("txtnewstgcifsusername").set_text("")
        self.builder.get_object("txtnewstgcifspassword").set_text("")
        self.builder.get_object("txtnewstgcifsoptions").set_text("")

        self.builder.get_object("txtnewstgnfsisoname").set_text("NFS ISO library")
        self.builder.get_object("txtnewstgnfsisopath").set_text("")
        self.builder.get_object("txtnewstgnfsisooptions").set_text("")

        self.builder.get_object("txtnewstgnfspath").grab_focus()
        self.builder.get_object("txtiscsitarget").grab_focus()
        # Disable Next button
        widget.set_sensitive(False)
        # Enable Previous button
        self.builder.get_object("previousnewstorage").set_sensitive(True)

        # if Hardware HBA is selected..
        if self.builder.get_object("radionewstghwhba").get_active():
            listhbalun = self.builder.get_object("listhbalun")
            if self.xc_servers[self.selected_host].fill_hw_hba(self.selected_ref, listhbalun) == 1:
                # no LUNs found
                self.builder.get_object("tabboxnewstorage").set_current_page(0)

            

    def on_cancelnewstorage_clicked(self, widget, data=None):
        """
        Function called when you press "Cancel" on new storage wizard
        """
        self.builder.get_object("newstorage").hide()
    def on_previousnewstorage_clicked(self, widget, data=None):
        """
        Function called when you press "Previous" on new storage wizard
        """
        self.builder.get_object("tabboxnewstorage").set_current_page(0)
        # Disable Previous button
        widget.set_sensitive(False)
        # Enable Next button
        self.builder.get_object("nextnewstorage").set_sensitive(True)
    def on_radioreattachsr_toggled(self, widget, data=None):
        """
        Function called when you choose "Reattach an existing SR" radio on new storage (nfs)
        """
        # Enable tree with possible attach storage if radio is selected
        self.builder.get_object("treereattachnewstgnfs").set_sensitive(widget.get_active())
    def on_btnewstgsnfsscan_clicked(self, widget, data=None):
        """
        Function called when you press on "Scan" button on new storage (nfs)
        """
        host, path = self.builder.get_object("txtnewstgnfspath").get_text().split(":", 2)
        options = self.builder.get_object("txtnewstgnfsoptions").get_text()
        listreattachnewstgnfs = self.builder.get_object("listreattachnewstgnfs")
        # Scan for NFS on selected host and path
        result = self.xc_servers[self.selected_host].scan_nfs_vhd(self.selected_ref, listreattachnewstgnfs, host, path, options)
        if result == 1:
            # Connection OK, but not exists previous SR
            self.builder.get_object("treereattachnewstgnfs").set_sensitive(False)
            self.builder.get_object("radioreattachsr").set_sensitive(False)
            self.builder.get_object("finishnewstorage").set_sensitive(True)
        elif result == 2:
            # Connection OK and exists previous SR
            self.builder.get_object("radioreattachsr").set_sensitive(True)
            self.builder.get_object("finishnewstorage").set_sensitive(True)
            self.builder.get_object("treereattachnewstgnfs").set_sensitive(True)
            # Select the first as default
            treereattachnewstgnfs = self.builder.get_object("treereattachnewstgnfs")
            treereattachnewstgnfs.set_cursor((0,), treereattachnewstgnfs.get_column(0))
            treereattachnewstgnfs.get_selection().select_path((0, 0))

        else:
            # Connection ERROR
            self.builder.get_object("treereattachnewstgnfs").set_sensitive(False)
            self.builder.get_object("radioreattachsr").set_sensitive(False)
            self.builder.get_object("finishnewstorage").set_sensitive(False)
    def on_btnewstgsaoescan_clicked(self, widget, data=None):
        """
        Function called when you press on "Scan" button on new storage (aoe)
        """
        path = self.builder.get_object("txtnewstgaoepath").get_text()
        listreattachnewstgaoe = self.builder.get_object("listreattachnewstgaoe")
        # Scan for AOE on selected device 
        result = self.xc_servers[self.selected_host].scan_aoe(self.selected_ref, listreattachnewstgaoe, path)
        if result == 1:
            # Connection OK, but not exists previous SR
            self.builder.get_object("treereattachnewstgaoe").set_sensitive(False)
            self.builder.get_object("radioreattachaoe").set_sensitive(False)
            self.builder.get_object("finishnewstorage").set_sensitive(True)
        elif result == 2:
            # Connection OK and exists previous SR
            self.builder.get_object("treereattachnewstgaoe").set_sensitive(True)
            self.builder.get_object("radioreattachaoe").set_sensitive(True)
            self.builder.get_object("finishnewstorage").set_sensitive(True)
            # Select the first as default
            treereattachnewstgaoe = self.builder.get_object("treereattachnewstgaoe")
            treereattachnewstgaoe.set_cursor((0,), treereattachnewstgaoe.get_column(0))
            treereattachnewstgaoe.get_selection().select_path((0, 0))

        else:
            # Connection ERROR
            self.builder.get_object("treereattachnewstgaoe").set_sensitive(False)
            self.builder.get_object("radioreattachaoe").set_sensitive(False)
            self.builder.get_object("finishnewstorage").set_sensitive(False)

    def on_txtnewstgcifspath_changed(self, widget, data=None):
        """
        Function called when you change text on "Share Name" on new storage (cifs iso)
        """
        X = "\\\\(\S+)\\\\(\S+)"
        c = re.compile(X).search(widget.get_text())
        self.builder.get_object("finishnewstorage").set_sensitive(c != None)

    def on_txtnewstgnfsisopath_changed(self, widget, data=None):
        """
        Function called when you change text on "Share Name" on new storage (nfs iso)
        """
        X = "(\S+):\/(\S+)"
        c = re.compile(X).search(widget.get_text())
        self.builder.get_object("finishnewstorage").set_sensitive(c != None)

    def on_txtnewstgnfspath_changed(self, widget, data=None):
        """
        Function called when you change text on "Share Name" on new storage (nfs)
        """
        X = "(\S+):\/(\S+)"
        c = re.compile(X).search(widget.get_text())
        self.builder.get_object("btnewstgsnfsscan").set_sensitive(c != None)
    def on_btdiscoveriqns_clicked(self, widget, data=None):
        """
        Function called when you press on "Discover IQNs" button on new storage (scsi)
        """
        target = self.builder.get_object("txtiscsitarget").get_text()
        iscsiport = self.builder.get_object("txtiscsiport").get_text()
        if self.builder.get_object("checkscsichap").get_active():
            user = self.builder.get_object("txtiscsichapuser").get_text()
            password = self.builder.get_object("txtiscsichapsecret").get_text()
        else:
            user = None
            password = None
        combotargetiqn = self.builder.get_object("combotargetiqn")
        listtargetiqn = self.builder.get_object("listtargetiqn")
        # fill_iscsi_target_iqn fills the combo with possible iqn targets and return True if something was found
        if self.xc_servers[self.selected_host].fill_iscsi_target_iqn(self.selected_ref, listtargetiqn, \
                target, iscsiport, user, password):
            # Set the first as default
            combotargetiqn.set_active(0) 
            self.builder.get_object("btdiscoverluns").set_sensitive(True)
        else:
            self.builder.get_object("btdiscoverluns").set_sensitive(False)
    def on_btdiscoverluns_clicked(self, widget, data=None):
        """
        Function called when you press on "Discover LUNs" button on new storage (scsi)
        """
        target = self.builder.get_object("txtiscsitarget").get_text()
        iscsiport = self.builder.get_object("txtiscsiport").get_text()
        if self.builder.get_object("checkscsichap").get_active():
            user = self.builder.get_object("txtiscsichapuser").get_text()
            password = self.builder.get_object("txtiscsichapsecret").get_text()
        else:
            user = None
            password = None
        combotargetiqn = self.builder.get_object("combotargetiqn")
        listtargetiqn = self.builder.get_object("listtargetiqn")
        combotargetlun = self.builder.get_object("combotargetlun")
        listtargetlun = self.builder.get_object("listtargetlun")
        targetiqn = listtargetiqn.get_value(combotargetiqn.get_active_iter(), 0)
        # fill_iscsi_target_lun fills the combo with possible luns and return True if something was found
        if self.xc_servers[self.selected_host].fill_iscsi_target_lun(self.selected_ref, listtargetlun, \
                target, targetiqn, iscsiport, user, password):
            # Set the first as default
            # TODO: detect if uuid is in use
            combotargetlun.set_active(0) 
            self.builder.get_object("finishnewstorage").set_sensitive(True)
        else:
            self.builder.get_object("finishnewstorage").set_sensitive(False)

    def on_checkscsichap_toggled(self, widget, data=None):
        """
        Function called when you check "Use CHAP" on new storage (scsi)
        """
        # Hide if is unchecked
        self.builder.get_object("framechap").set_sensitive(widget.get_active())
    def on_txtiscsitarget_changed(self, widget, data=None):
        """
        Function called when text changed on "target host" on "new storage" (iscsi)
        """
        # Disable or enabled "Discover IQNs" button
        self.builder.get_object("btdiscoveriqns").set_sensitive(len(widget.get_text()) > 0)
    def on_btstgnewdisk_activate(self, widget, data=None):
        """"
        Function called when you press "new disk" on storage
        """
        vmaddnewdisk = self.builder.get_object("vmaddnewdisk")
        # Set default name and empty description
        self.builder.get_object("vmaddnewdisk_name").set_text("New virtual disk on " + self.selected_name)
        self.builder.get_object("vmaddnewdisk_desc").set_text("")
        listnewvmdisk1 = self.builder.get_object("listnewvmdisk1")
        # Fill the possible disks list
        defsr = self.xc_servers[self.selected_host].fill_listnewvmdisk(listnewvmdisk1, self.selected_host)
        treenewvmstorage1 = self.builder.get_object("treenewvmdisk1")
        # Select the first by default
        treenewvmstorage1.set_cursor((defsr,), treenewvmstorage1.get_column(0))
        treenewvmstorage1.get_selection().select_path((defsr, 0))
        # Set as default "5 Gb" size
        self.builder.get_object("disksize2").set_value(float(5))
        # Show the "add new disk" window
        vmaddnewdisk.show()
    def on_radionewstgnfsvhd_group_changed(self, widget, data=None):
        """
        Function called when you select a type the storage on "new storage" window
        """
        if widget.get_active():
            texts = {
                    "radionewstgnfsvhd" : "NFS servers are a common form of shared filesystem infrastructure, and can be used as a storage repository substrate for virtual disks.\n\nAs NFS storage repositories are shared, the virtual disks stored in them allow VMs to be started on any server in a resource pool and to be migrated between them using XenMotion.\n\nWhen you configure an NFS storage repository, you simply provide the hostname or IP address of the NFS server and the path to a directory that will be used to contain the storage repository. The NFS server must be configured to export the specified path to all servers in the pool",
                    "radionewstgiscsi" : "Shared Logical Volume Manager (LVM) support is available using either iSCSI or Fibre Channel access to a shared LUN.\n\nUsing the LVM-based shared SR provides the same performance benefits as unshared LVM for local disk storage, however in the shared context, iSCSI or Fibre Channel-based SRs enable VM agility -- VMs may be started on any server in a pool and migrated between them.",
                    "radionewstghwhba" : "XenServer Hosts support Fibre Channel (FC) storage area networks (SANs) through Emulex or QLogic host bus adapters (HBAs).\n\nAll FC configuration required to expose a FC LUN to the host must be completed manually, including storage devices, network devices, and the HBA within the XenServer host.\n\nOnce all FC configuration is complete the HBA will expose a SCSI device backed by the FC LUN to the host. The SCSI device can then be used to access to the FC LUN as if it were a locally attached SCSI device.",
                    "radionewstgnetapp" : "Main developer of openxenmanager hasn't NetApp and hasn't Essentials",
                    "radionewstgdell" : "Main developer of openxenmanager hasn't Dell EqualLogic and hasn't Essentials",
                    "radionewstgcifs" :  "Select this option if you have a library of VM installation ISO images available as a Windows File Sharing share that you wish to attach to your host or pool.",
                    "radionewstgnfsiso": "Select this option if you have a library of VM installation ISO images available as a NFS share that you wish to attach to your host or pool.",
                    "radionewstgaoe": "ATA over Ethernet (AoE) is a network protocol designed for simple, high-performance access of SATA storage devices over Ethernet networks. It gives the possibility to build SANs with low-cost, standard technologies."
            }
            name = gtk.Buildable.get_name(widget)
            # Set the info text
            self.builder.get_object("newstorageinfo").set_text(texts[name])

            if name != "radionewstgnetapp" and name != "radionewstgdell":
                # Enable buton for others
                self.builder.get_object("nextnewstorage").set_sensitive(True)
            else:
                # Disable next button on unsupported new storage types
                self.builder.get_object("nextnewstorage").set_sensitive(False)
    def on_btstgremove_activate(self, widget, data=None):
        """"
        Function called when you press "remove disk" on storage
        """
        is_a_snapshot = self.xc_servers[self.selected_host].all_vdi[self.selected_vdi_ref]['is_a_snapshot']
        if is_a_snapshot:
            # If is a snapshot, show different text
            self.builder.get_object("dialogdeletevdi").set_title("Delete entire snapshot")
            self.builder.get_object("dialogdeletevdi").set_markup("Deleting a single snapshot disk is not allowed. This action will delete the entire snapshot, and any other disks attache. This operation cannot be undone. Dou wish continue?")
        else:
            # else show the confirmation text
            self.builder.get_object("dialogdeletevdi").set_title("Delete Virtual Disk")
            self.builder.get_object("dialogdeletevdi").set_markup("This will delete this virtual disk permanently destroying the data on it. Continue?")
        # Show the confirmation dialog
        self.builder.get_object("dialogdeletevdi").show()
    def on_treestg_button_press_event(self, widget, event):
        """"
        Function called when you select a storage on "tree storage" tree
        """
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = widget.get_path_at_pos(x, y)
        if pthinfo is not None:
           path, col, cellx, celly = pthinfo
           widget.grab_focus()
           widget.set_cursor( path, col, 0)
           iter = self.builder.get_object("liststg").get_iter(path)
           self.selected_vdi_ref = self.builder.get_object("liststg").get_value(iter, 0)
           operations = self.xc_servers[self.selected_host].all_vdi[self.selected_vdi_ref]['allowed_operations']
           # If have "destroy" option in "allowed_operations"
           if operations.count("destroy"):
               # Enable button
               self.builder.get_object("btstgremove").set_sensitive(True)
           else:
               # Else disable it
               self.builder.get_object("btstgproperties").set_sensitive(True)
           is_snapshot = self.xc_servers[self.selected_host].all_vdi[self.selected_vdi_ref]['is_a_snapshot']
           # If not is a snapshot, enable "properties" button
           self.builder.get_object("btstgproperties").set_sensitive(not is_snapshot)
    def on_dialogdeletevdi_cancel_activate(self, widget, data=None):
        """
        Function called when you cancel "dialog delete" 
        """
        self.builder.get_object("dialogdeletevdi").hide()
    def on_dialogdeletevdi_accept_activate(self, widget, data=None):
        """
        Function called when you accept "dialog delete" 
        """
        vdi = self.xc_servers[self.selected_host].all_vdi[self.selected_vdi_ref]
        if vdi['is_a_snapshot']:
            # If is a snapshot, destroy entire snapshot
            for vbd_ref in vdi['VBDs']:
                ref = self.xc_servers[self.selected_host].all_vbd[vbd_ref]["VM"]
                self.xc_servers[self.selected_host].destroy_vm(ref, True, False)
        else:
            if len(vdi['VBDs']):
                vm_ref = self.xc_servers[self.selected_host].all_vbd[vdi['VBDs'][0]]['VM']                                         
            else:
                vm_ref = None
            # Else only delete select virtual disk
            self.xc_servers[self.selected_host].delete_vdi(self.selected_vdi_ref, vm_ref)
        # Hide the dialog
        self.builder.get_object("dialogdeletevdi").hide()
