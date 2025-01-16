# -*- coding: utf-8 -*-
"""
Internal module
Used to read the pyOlog.conf file
example file
cat ~/pyOlog.conf
[DEFAULT]
url=http://localhost:8000/Olog
"""

def __loadConfig():
    import os.path
    import configparser
    dflt={'url':'https://localhost:8181/Olog'}
    cf=configparser.ConfigParser(defaults=dflt)
    cf.read([
        '/etc/pyOlog.conf',
        os.path.expanduser('~/pyOlog.conf'),
        'pyOlog.conf'
    ])
    return cf

_conf=__loadConfig()
