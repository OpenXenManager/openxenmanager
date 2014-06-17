from setuptools import setup
import sys
from glob import glob

sys.path.append('./src')
# FIXME: This almost works... If only I could work how install all the required modules in windows!
if sys.platform.startswith('win'):  # Windows
    try:
        import py2exe
    except ImportError:
        raise RuntimeError('Cannot import py2exe')

    data_files = [('OXM', glob('src\OXM\oxc.glade')),
                  ('OXM', glob('src\OXM\oxc.conf')),
                  ('OXM/images', glob(r'src\OXM\images\*')),
                  ('OXM/images_map', glob(r'src\OXM\images_map\*')),
                  ('OXM', glob('vncviewer.exe'))]

    setup(windows=[{'script': 'oxm.pyw'}],
          zipfile=None,
          data_files=data_files,
          options={'py2exe': {
              'dll_excludes': ['MSVCP90.dll', 'POWRPROF.dll', 'MSWSOCK.dll'],
              'optimize': 1,
              'packages': ['OXM', 'pygtk_chart']}
          })


else:  # Not Windows
    setup(
        name='openxenmanager',
        version='0.1.0-dev1',
        packages=['OXM', 'pygtk_chart'],
        package_dir={'': 'src'},
        url='http://github.com/OpenXenManager/openxenmanager',
        license='GPL-2+',
        author='Daniel Lintott',
        author_email='daniel@serverb.co.uk',
        description='Opensource XenServer/XCP Management GUI',
        requires=['configobj'],
        scripts=['openxenmanager'],
        package_data={'OXM': ['oxc.glade',
                              'oxc.conf',
                              'images/*',
                              'images_map/*']
                      }
    )
