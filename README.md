OpenXenManager introduction
===========================
OpenXenManager is a full-featured graphical interface to manage Citrix
XenServer / Xen Cloud Platform (XCP) hosts through the network.

OpenXenManager is an open-source multiplatform clone of Citrix XenCenter.
It is written in Python, using pyGTK for its interface.

The homepage for OpenXenManager is at:
https://sourceforge.net/projects/openxenmanager/

Subscribe to the openxenmanager-announce mailing list for important information
and release announcements:
https://lists.sourceforge.net/lists/listinfo/openxenmanager-announce


Running OpenXenManager
======================
To launch OpenXenManager simply run the "openxenmanager" script.

Requirements:
* Python 2.7
* pyGTK 2.16
* ConfigObj
* Raven
* GTK-VNC (Linux only)
 
Debian/Ubuntu Linux package dependencies:
python2.7 python-gtk2 glade python-gtk-vnc python-glade2 python-configobj python-setuptools python-raven

Gentoo Linux package dependencies:
dev-python/pygtk dev-python/configobj net-libs/gtk-vnc dev-lang/python:2.7 dev-python/raven  (remember to set "python" USE flag for gtk-vnc!)

macOS dependencies:  
[brew](http://brew.sh/) install pygtk  
pip install configobj
pip install raven

OpenXenManager runs has been tested to run on Linux or Windows and should work
on MacOSX as well.


Help / bug reports
==================

If you have found a bug, please file a detailed report in our bug tracker:
  https://github.com/OpenXenManager/openxenmanager/issues

<img src="https://sentry-brand.storage.googleapis.com/sentry-logo-black.svg" alt="Sentry Logo" width="200px">

In addition to submitting bug reports, we will be collecting crash data via Sentry.io 
No personally identifying data is collected.

For help you can:

* Visit the forums:
  http://sourceforge.net/projects/openxenmanager/forums

* Send an email in the mailing list:
  https://lists.sourceforge.net/lists/listinfo/openxenmanager-users
  
Developers
==========

- Original Author: Alberto Gonzalez Rodriguez <alberto@pesadilla.org>
- Previous Developer: Cheng Sun <chengsun9@gmail.com>
- Current Developer: Daniel Lintott <daniel.j.lintott@gmail.com>
- Contributors:
  * Lars Hagström (DonOregano) <lars@foldspace.nu>
  * Sol Jerome (solj)
  * Ivan Zderadicka (izderadicka)
  * Jason Nelson (schplat)
