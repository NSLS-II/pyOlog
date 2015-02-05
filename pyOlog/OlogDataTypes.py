"""
Copyright (c) 2010 Brookhaven National Laboratory
All rights reserved. Use is subject to license terms and conditions.

Created on Jan 10, 2013

@author: shroffk
"""

import os
import mimetypes
import string

from .conf import _conf


class LogEntry(object):
    """A LogEntry consists of some Text description, an owner and an
    associated logbook It can optionally be associated with one or more
    logbooks and contain one or more tags, properties and attachments
    """
    def __init__(self, text=None, owner=None, logbooks=None,
                 tags=None, attachments=None, properties=None,
                 id=None, create_time=None, modify_time=None):
        """ Constructor for log Entry

        :param text: Text of log entry
        :type text: string
        :param owner: Owner of log entry
        :type owner: string
        :param logbooks: Logbooks to add entry to
        :type logbooks: string, list of strings, Logbook object.
        :param tags: Tags to add to log entries
        :type tags: string, list of strings, Tag object.
        :param attachments: attachments to add to the log entry
        :type attachments: list of attachment objects
        :param properties: properties to add to the log entry
        :type properties: list of properties objects
        :param id: numerical id of log entry
        :type id: integer

        Example:

        Simple LogEntry
        >>> LogEntry('test log entry', 'controls',
                     logbooks=[Logbook('commissioning', owner='controls')])

        Comprehensive logEntry
        >>> LogEntry('test log entry', 'controls',
                     logbooks=[Logbook('commissioning', owner='controls')],
                     tags=[Tag('TimingSystem')]
                     properties=[Property('Ticket',
                                 attributes={'Id':'1234',
                                 'URL':'http://trac.nsls2.bnl.gov/trac/1234'}]
                     attachments=[Attachment(open('databrowser.plt'))]
                     )
        """
        if text is not None:
            text = ''.join(c for c in text if c in string.printable)
        else:
            text = ''
        self.text = text.strip()
        self.owner = _conf.get_value('username', owner)

        if self.owner is None:
            raise ValueError("You must specify an owner")

        if logbooks is None:
            logbooks = _conf.get_value('logbooks')
            if logbooks is None:
                raise ValueError("You must specify a logbook")

            self.logbooks = [Logbook(n) for n in logbooks.split(',')]
        else:
            self.logbooks = logbooks

        if tags is None:
            tags = _conf.get_value('tags')
            if tags is not None:
                self.tags = [Tag(n) for n in tags.split(',')]
            else:
                self.tags = []
        else:
            self.tags = tags

        if attachments is not None:
            self.attachments = attachments
        else:
            self.attachments = []

        if properties is not None:
            self.properties = properties
        else:
            self.properties = []

        self.id = id
        self.create_time = create_time
        self.modify_time = modify_time

    def __cmp__(self, *arg, **kwargs):
        if arg[0] is None:
            return 1
        if self._id:
            return cmp((self.id), (arg[0].id))
        else:
            raise ValueError('Invalid LogEntry: id cannot be None')


class Logbook(object):
    """ A Logbook consist of an unique name and an owner,
    logentries can be added to a logbook so long as the user either the owner
    or a member of the owner group
    """

    def __init__(self, name, owner=None, active=True):
        """ Create logbook object

        :param name: Name of logbook
        :type name: string
        :param owner: Owner of logbook
        :type owner: string
        :param active: State of logbook
        :type active: bool

        If the owner is not specified then the default is read from the
        config file.


        For example:
        >> Logbook('commissioning', 'controls')
        """
        self.name = '{}'.format(name).strip()
        self.owner = _conf.get_owner(owner)
        self.active = active

    def __cmp__(self, *arg, **kwargs):
        if arg[0] is None:
            return 1
        return cmp((self.name, self.owner), (arg[0].name, arg[0].owner))


class Tag(object):
    """ A Tag consists of a unique name, it is used to tag log entries
    """

    def __init__(self, name, active=True):
        """
        :param name: Name of tag
        :type name: string
        :param active: The tags active state
        :type active: bool

        For example:
        >> Tag('TimingSystem')
        """
        self.name = "{}".format(name).strip()
        if active:
            self.state = 'Active'
        else:
            self.state = 'Inactive'

    @property
    def active(self):
        if self.state == 'Active':
            return True
        else:
            return False

    @active.setter
    def active(self, value):
        if value:
            self.state = 'Active'
        else:
            self.state = 'Inactive'

    def __cmp__(self, *arg, **kwargs):
        if arg[0] is None:
            return 1
        return cmp((self.name, self.state), (arg[0].name, arg[0].state))


class Attachment(object):
    """ A class representation of an Olog Attachment. An Attachment, is
    a file associated with the log entry. This object contains filename and
    mime-type information about the attachment.
    """
    default_mime_type = 'application/octet-stream'

    def __init__(self, file, filename=None, mime_type=None):
        """ Create Attachment

        :param file: File object or data
        :type file: String, or file object
        :param filename: Filename of attatchment
        :type filename: String
        :param mime_type: Mime-type of attachment
        :type mime_type: String

        For example:

        >> Attachment(file=open('/home/usr/databrowser.plt')
        >> Attachment(file=open('test.jpg','rb')
        >> Attachment(file=string, filename='mydata.png')
        """
        self.file = file
        self.filename = filename
        self.mime_type = mime_type

    def get_file_post(self):
        """Get tuple for makeing http post of attachment

        :returns: Tuple of filename, file object and mimetype
        :rtype: tuple
        """

        if self.filename is None:
            basename = os.path.basename(self.file.name)
        else:
            basename = os.path.basename(self.filename)

        if self.mime_type is None:
            mtype = mimetypes.guess_type(basename)[0]
            if mtype is None:
                mtype = self.default_mime_type
        return (basename, self.file, mtype)


class Property(object):
    """ A class representation of an Olog property. A property consists of
    a unique name and a set of attributes consisting of key value pairs.
    The ket value pairs are represented as a dictionary.
    """
    def __init__(self, name, attributes=None):
        """ Create a property with a unique name and attributes

        :param name: Name of property
        :type name: string
        :param attributes: Attributes of the property as a dict
        :type attributes: dictionary

        For example:

        >>> Property('Ticket', attributes={'Id':'1234',
                     'URL':'http://trac.nsls2.bnl.gov/trac/1234'}
        >>> Property('Scan', attributes={'Number':'run-1234',
                     'script':'scan_20130117.py'}
        """
        self.name = name
        self.attributes = attributes

    @property
    def attribute_names(self):
        return self.attributes.keys()

    def __cmp__(self, *arg, **kwargs):
        if arg[0] is None:
            return 1
        return cmp((self.name, set(self.attributes)),
                   (arg[0].name, set(arg[0].attributes)))
