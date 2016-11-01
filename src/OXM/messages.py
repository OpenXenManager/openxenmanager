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
# USA.
#
# -----------------------------------------------------------------------
"""
Messages for use in OpenXenManager
"""

_messages = {
    'PBD_PLUG_FAILED_ON_SERVER_START':
        ["Failed to attach storage on server boot",
         "A storage repository could not be attached when \nserver '%s' "
         "started.\n You may be able to fix this using the 'Repair Storage'\n"
         "option in the Storage menu."],
    'HOST_SYNC_DATA_FAILED':
        ["XenServer statistics synchronization failed",
         "%s. There was a temporary failure synchronizing performance "
         "statistics across the\npool, probably because one or more servers "
         "were offline. Another\nsynchronization attempt will be "
         "made later."],
    'host_alert_fs_usage':
        ["File System On %s Full",
         "Disk usage for the %s on server '%s' has reached %0.2f%%. "
         "XenServer's\nperformance will be critically affected  if this disk "
         "becomes full.\nLog files or other non-essential (user created) "
         "files should be removed."],
    'alert_cpu_usage':
        ["CPU Usage Alarm",
         "CPU usage on VM '%s' has been on average %0.2f%% for the last %d "
         "seconds.\nThis alarm is set to be triggered when CPU usage is more "
         "than %0.1f%%"],
    'VM_SHUTDOWN':
        ["VM shutdown", "VM '%s' has shut down."],
    'VM_STARTED':
        ["VM started", "VM '%s' has started."],
    'VM_REBOOTED':
        ["VM rebooted", "VM '%s' has rebooted."],
    'VM_SUSPENDED':
        ["VM suspended", "VM '%s' has suspended."],
    'VM_RESUMEND':
        ["VM resumed", "VM '%s' has resumed."],
    'restartHost':
        ["After applying this update, all servers must be restarted.", ""],
    'restartHVM':
        ["After applying this update, all Linux VMs must be restarted.", ""],
    'restartPV':
        ["After applying this update, all Windows VMs must be restarted.", ""],
    'restartXAPI':
        ["After applying this update, all VMs must be restarted.", ""],
}


def get_msg(msg_key):
    """
    Return a dict containing the header and detail for the specified msg_key
    :param msg_key: Key of message to return
    :return: Message dictionary containing header and detail
    """
    if msg_key in _messages:
        msg = {'header': _messages[msg_key][0],
               'detail': _messages[msg_key][1]}
    else:
        msg = False

    return msg
