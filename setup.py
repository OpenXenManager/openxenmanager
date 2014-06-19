from setuptools import setup

setup(
    name='openxenmanager',
    version='0.1b1',
    packages=['OXM', 'pygtk_chart'],
    package_dir={'': 'src'},
    url='http://github.com/OpenXenManager/openxenmanager',
    license='GPLv2+',
    author='Daniel Lintott',
    author_email='daniel@serverb.co.uk',
    description='Opensource XenServer/XCP Management GUI',
    requires=['configobj'],
    scripts=['openxenmanager'],
    package_data={'OXM': ['oxc.glade',
                          'oxc.conf',
                          'images/*',
                          'images_map/*']
                  },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ]
)
