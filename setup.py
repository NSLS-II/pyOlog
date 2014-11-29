'''
Copyright (c) 2010 Brookhaven National Laboratory
All rights reserved. Use is subject to license terms and conditions.

Created on Jan 10, 2013

@author: shroffk
'''

try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup


setup(name='pyOlog',
      version='0.2.0',
      description='Python Olog Client Lib',
      author='Kunal Shroff',
      author_email='shroffk@bnl.gov',
      packages=['pyOlog'],
      requires=['requests (>=2.0.0)', 'urllib3 (>=1.7.1)'],
      scripts=['scripts/olog.py'],
      entry_points = {
        'console_scripts': [
          'olog = olog:main']
      }
     )
