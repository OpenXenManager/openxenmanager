from setuptools import setup
import sys
import os
from glob import glob

sys.path.append('./src')


def generate_data_files(prefix, tree, file_filter=None):
    """
    Walk the filesystem starting at "prefix" + "tree", producing a list of files
    suitable for the data_files option to setup(). The prefix will be omitted
    from the path given to setup(). For example, if you have

        C:\Python26\Lib\site-packages\gtk-2.0\runtime\etc\...

    ...and you want your "dist\" dir to contain "etc\..." as a subdirectory,
    invoke the function as

        generate_data_files(
            r"C:\Python26\Lib\site-packages\gtk-2.0\runtime",
            r"etc")

    If, instead, you want it to contain "runtime\etc\..." use:

        generate_data_files(
            r"C:\Python26\Lib\site-packages\gtk-2.0",
            r"runtime\etc")

    Empty directories are omitted.

    file_filter(root, fl) is an optional function called with a containing
    directory and filename of each file. If it returns False, the file is
    omitted from the results.
    """
    gen_data_files = []
    for root, dirs, files in os.walk(os.path.join(prefix, tree)):
        to_dir = os.path.relpath(root, prefix)

        if file_filter is not None:
            file_iter = (fl for fl in files if file_filter(root, fl))
        else:
            file_iter = files

        gen_data_files.append((to_dir, [os.path.join(root, fl) for fl in file_iter]))

    non_empties = [(to, fro) for (to, fro) in gen_data_files if fro]

    return non_empties

try:
    import py2exe
except ImportError:
    raise RuntimeError('Cannot import py2exe')

try:
    import gtk
except ImportError:
    raise ImportError('Cannot import gtk module')

GTK_RUNTIME_DIR = os.path.join(os.path.split(os.path.dirname(gtk.__file__))[0], 'runtime')
assert os.path.exists(GTK_RUNTIME_DIR), 'Cannot find GTK Runtime Data'

GTK_THEME_DEFAULT = os.path.join('share', 'themes', 'Default')
GTK_THEME_WINDOWS = os.path.join('share', 'themes', 'MS-Windows')
GTK_GTKRC_DIR = os.path.join('etc', 'gtk-2.0')
GTK_GTKRC = 'gtkrc'
GTK_WIMP_DIR = os.path.join('lib', 'gtk-2.0', '2.10.0', 'engines')
GTK_WIMP_DLL = 'libwimp.dll'
GTK_ICONS = os.path.join("share", "icons")

data_files = [('', glob('src\OXM\oxc.glade')),
              ('', glob('src\OXM\oxc.conf')),
              ('images', glob(r'src\OXM\images\*')),
              ('images_map', glob(r'src\OXM\images_map\*')),
              ('', glob('vncviewer.exe')),  # TODO: Don't ship vncviewer with oxm... install it, and use that!
              ('data', glob('src\pygtk_chart\data\tango.color'))]
data_files += generate_data_files(GTK_RUNTIME_DIR, GTK_THEME_DEFAULT)
data_files += generate_data_files(GTK_RUNTIME_DIR, GTK_THEME_WINDOWS)
data_files += generate_data_files(GTK_RUNTIME_DIR, GTK_WIMP_DIR)

setup(windows=[{'script': 'oxm.pyw'}],
      zipfile=None,
      data_files=data_files,
      options={'py2exe': {
          'optimize': 1,
          'packages': ['OXM', 'pygtk_chart'],
          'includes': 'cairo, pango, pangocairo, atk, gobject, gio'}
      })