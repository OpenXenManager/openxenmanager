#
# Taken from https://github.com/GNS3/gns3-gui/blob/master/gns3/crash_report.py
#
# Copyright (C) 2014 GNS3 Technologies Inc.
# Copyright (C) 2015 Daniel Lintott <daniel@serverb.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import platform
import struct

try:
    import raven
    RAVEN_AVAILABLE = True
except ImportError:
    # raven is not installed with deb package in order to simplify packaging
    RAVEN_AVAILABLE = False

from .version import __version__

import logging
log = logging.getLogger(__name__)


class CrashReport:

    """
    Report crash to a third party service
    """

    DSN = "sync+https://e59b1dfe6c2e48a4a115cad7012f5e5e:b00d1730c16f4c84a13" \
          "3d7661209718e@sentry.serverb.co.uk/2"
    if hasattr(sys, "frozen"):
        cacert = os.path.join(os.getcwd(), "cacert.pem")
        if os.path.isfile(cacert):
            DSN += "?ca_certs={}".format(cacert)
        else:
            log.warning("The SSL certificate bundle file '{}' could not "
                        "be found".format(cacert))
    _instance = None

    def __init__(self):
        self._client = None

    def capture_exception(self, exception, value, tb):
        if not RAVEN_AVAILABLE:
            return
        report_errors = True
        if report_errors:
            if self._client is None:
                self._client = raven.Client(CrashReport.DSN,
                                            release=__version__)
            self._client.tags_context({
                "os:name": platform.system(),
                "os:release": platform.release(),
                "os:win_32": " ".join(platform.win32_ver()),
                "os:mac": "{} {}".format(platform.mac_ver()[0],
                                         platform.mac_ver()[2]),
                "os:linux": " ".join(platform.linux_distribution()),
                "python:version": "{}.{}.{}".format(sys.version_info[0],
                                                    sys.version_info[1],
                                                    sys.version_info[2]),
                "python:bit": struct.calcsize("P") * 8,
                "python:encoding": sys.getdefaultencoding(),
                "python:frozen": "{}".format(hasattr(sys, "frozen"))
            })
            try:
                report = self._client.captureException((exception, value, tb))
            except Exception as e:
                log.error("Can't send crash report to Sentry: {}".format(e))
                return
            log.info("Crash report sent with event ID: {}".format(
                self._client.get_ident(report)))

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = CrashReport()
        return cls._instance
