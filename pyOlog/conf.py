# -*- coding: utf-8 -*-
"""
Configuration module used to set defaults for pyOlog to connect to the Olog.

Default locations are searched for a config file.
An example file is listed below:

[DEFAULT]
url=http://localhost:8000/Olog
username=swilkins
logbooks=Commissioning
tags=pyOlog
"""

import os
import os.path
import logging
import getpass

logger = logging.getLogger(__name__)


class Config(object):
    defaults = {'url': 'http://localhost:8181/Olog',
                'username': getpass.getuser()}
    conf_files = ['/etc/pyOlog.conf',
                  os.path.expanduser('~/pyOlog.conf'),
                  os.path.expanduser('~/.pyOlog.conf'),
                  os.path.expanduser('~/.pyologrc'),
                  'pyOlog.conf']

    def __init__(self, conf='DEFAULT'):
        """Initialise config object"""
        self.heading = conf

        from six.moves import configparser
        self.cf = configparser.SafeConfigParser(defaults=self.defaults)
        files = self.cf.read(self.conf_files)

        for f in files:
            logger.info("Read config file %s", f)

    def get_value(self, arg, value=None):
        '''
        Get a default from the config file.

        :param arg: Parameter to return
        :param value: Value to check for.

        This method will return the default value from the config. If
        :param value: is not None then this will always return :param value:.
        If :param value: is None then the config is searched for an entry
        :param arg:. If no config is avaliable then None is returned.

        :returns: Config value or None.
        '''
        if value is None:
            if self.cf.has_option(self.heading, arg):
                return self.cf.get(self.heading, arg)
            else:
                return None
        else:
            return value

    def get_username(self, value=None):
        """Get the username to be used"""
        if value is None:
            if self.cf.has_option(self.heading, 'username'):
                return self.cf.get(self.heading, 'username')
            else:
                return getpass.getuser()
        else:
            return value

    def get_owner(self, value=None):
        """Get the owner for tags, logbooks and properties to be used"""
        if value is None:
            if self.cf.has_option(self.heading, 'default owner'):
                return self.cf.get(self.heading, 'default owner')
            else:
                return self.get_username()
        else:
            return value

_conf = Config()
