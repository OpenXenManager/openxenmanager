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
from __future__ import print_function
import traceback
import time
import datetime
import os
import gtk
import sys
from OXM.window import oxcWindow
from OXM.version import __version__
from OXM.crash_report import CrashReport

# FIXME: rather pathetic fix for Ubuntu to show menus -  GTK3 migration should
# fix this
os.environ['UBUNTU_MENUPROXY'] = '0'
sys.path.append('./src')


def main():
    """
    Entry point for OpenXenManager
    """
    exception_file_path = "exceptions.log"

    def exception_hook(exception, value, tb):
        if exception == KeyboardInterrupt:
            sys.exit(0)

        lines = traceback.format_exception(exception, value, tb)
        print("****** Exception detected, traceback information saved in "
              "{} ******".format(exception_file_path))
        print("".join(lines))
        try:
            curdate = time.strftime("%d %b %Y %H:%M:%S")
            logfile = open(exception_file_path, "a")
            logfile.write("=== OpenXenManager {} traceback on {} ===\n".format(
                __version__, curdate))
            logfile.write("".join(lines))
            logfile.close()
        except OSError as e:
            print("Could not save traceback to {}: {}".format(
                os.path.normpath(exception_file_path), e))

        if not sys.stdout.isatty():
            # if stdout is not a tty (redirected to the console view),
            # then print the exception on stderr too.
            print("".join(lines), file=sys.stderr)

        # TODO: Add crash reporter
        CrashReport.instance().capture_exception(exception, value, tb)

    sys.excepthook = exception_hook

    current_year = datetime.date.today().year
    print("OpenXenManager version {}".format(__version__))
    print("Copyright (c) 2009-{} OpenXenManager Development Team".format(
        current_year))

    mainwindow = oxcWindow()
    gtk.main()


def install_thread_excepthook():
    """
    Workaround for sys.excepthook thread bug
    (https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470).
    Call once from __main__ before creating any threads.
    If using psyco, call psyco.cannotcompile(threading.Thread.run)
    since this replaces a new-style class method.
    """
    import threading
    run_old = threading.Thread.run

    def run(*args, **kwargs):
        try:
            run_old(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            sys.excepthook(*sys.exc_info())
    threading.Thread.run = run

if __name__ == "__main__":
    install_thread_excepthook()
    main()
