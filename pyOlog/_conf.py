# -*- coding: utf-8 -*-
"""
Internal module

Used to read the pyOlog.conf file

example file
cat ~/pyOlog.conf
[DEFAULT]
url=http://localhost:8000/Olog
"""

import os.path
import logging

logger = logging.getLogger(__name__)

defaults   = {'url' : 'http://localhost:8181/Olog'}
conf_files = ['/etc/pyOlog.conf',
              os.path.expanduser('~/pyOlog.conf'),
              os.path.expanduser('~/.pyOlog.conf'),
              'pyOlog.conf']

def __loadConfig():
    import ConfigParser
    cf=ConfigParser.SafeConfigParser(defaults=defaults)
    files = cf.read(conf_files)
    for f in files: 
        logger.info("Read config file %s", f)
    return cf

_conf=__loadConfig()
