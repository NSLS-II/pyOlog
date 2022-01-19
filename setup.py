'''
Copyright (c) 2010 Brookhaven National Laboratory
All rights reserved. Use is subject to license terms and conditions.

Created on Jan 10, 2013

@author: shroffk
'''

from setuptools import setup

setup(name='pyOlog',
      version='4.5.0',
      description='Python Olog Client Lib',
      author='Kunal Shroff',
      author_email='shroffk@bnl.gov',
      packages=['pyOlog', 'pyOlog.cli'],
      requires=['requests (>=2.0.0)', 'urllib3 (>=1.7.1)'],
      entry_points={'console_scripts': [
                    'olog = pyOlog.cli:main'],
                    'gui_scripts': [
                    'ologgui = pyOlog.gui:main']}
      )
