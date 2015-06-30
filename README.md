IMPORTANT INFORMATION!
======================
I have setup and integrated Sentry into OpenXenManager. Sentry will 
automatically capture and upload all crashes that occur within OXM.

I will be providing an option to disable this via the options, but it would be 
very useful for me to have this information to help find bugs that are lurking 
deep within OXM.

All that is needed is to install the raven package via pip, which handles the 
processing of the crash reports.

Thankyou!

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
* GTK-VNC (Linux only)
 
Linux package dependencies:
python2.7 python-gtk2 glade python-gtk-vnc python-glade2 python-configobj

OpenXenManager runs has been tested to run on Linux or Windows and should work
on MacOSX as well.


Help / bug reports
==================

If you have found a bug, please file a detailed report in our bug tracker:
  https://github.com/OpenXenManager/openxenmanager/issues

For help you can:

* Visit the forums:
  http://sourceforge.net/projects/openxenmanager/forums

* Send an email in the mailing list:
  https://lists.sourceforge.net/lists/listinfo/openxenmanager-users
  
Developers
==========

- Original Author: Alberto Gonzalez Rodriguez <alberto@pesadilla.org>
- Previous Developer: Cheng Sun <chengsun9@gmail.com>
- Current Developer: Daniel Lintott <daniel@serverb.co.uk>
- Contributors:
  * Lars Hagström (DonOregano) <lars@foldspace.nu>
  * Sol Jerome (solj)
  * Ivan Zderadicka (izderadicka)
  * Jason Nelson (schplat)
