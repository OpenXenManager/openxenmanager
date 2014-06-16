from setuptools import setup

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
