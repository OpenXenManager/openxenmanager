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

class oxcSERVERvmsnapshot:
    def take_snapshot(self, ref, snapname):
        res = self.connection.Async.VM.snapshot(self.session_uuid, ref, snapname)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

    def revert_to_snapshot(self, ref, snapref):
        res = self.connection.Async.VM.revert(self.session_uuid, snapref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res


    def delete_snapshot(self, ref, ref_vm):
        for vbd in self.all_vms[ref]['VBDs']:
            if self.all_vbd[vbd]['VDI'] != "OpaqueRef:NULL":
                res = self.connection.VDI.destroy(self.session_uuid, self.all_vbd[vbd]['VDI'])
                if "Value" in res:
                    self.track_tasks[res['Value']] = ref_vm
                    self.track_tasks[res['Value']] = ref
                else:
                    print res
        for vbd in self.all_vms[ref]['VBDs']:
                res = self.connection.VBD.destroy(self.session_uuid, vbd)
                if "Value" in res:
                    self.track_tasks[res['Value']] = ref_vm
                    self.track_tasks[res['Value']] = ref
                else:
                    print res
        res = self.connection.VM.destroy(self.session_uuid, ref)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref_vm
            self.track_tasks[res['Value']] = ref
        else:
            print res
    def create_template_from_snap(self, ref, name):
        res = self.connection.Async.VM.clone(self.session_uuid, ref, name)
        if "Value" in res:
            self.track_tasks[res['Value']] = ref
        else:
            print res

