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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# -----------------------------------------------------------------------

import os
import sys


def we_are_frozen():
    if hasattr(sys, 'frozen') and sys.frozen in ('windows_exe', 'console_exe'):
        return hasattr(sys, 'frozen')


def module_path():
    encoding = sys.getfilesystemencoding()
    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, encoding))
    return os.path.dirname(unicode(__file__, encoding))


def image_path(image_file):
    return os.path.join(module_path(), 'images', image_file)


def bytes_to_gb(num_bytes):
    num_bytes = float(num_bytes)
    gigabytes = num_bytes / 1073741824
    return gigabytes