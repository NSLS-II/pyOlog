from __future__ import (print_function, absolute_import)
__author__ = "swilkins"
"""
A simple API to the Olog client in python
"""

import io
import six
from .OlogClient import OlogClient
from .OlogDataTypes import LogEntry, Logbook, Tag, Attachment, Property


def logentry_to_dict(log):
    rtn = dict()

    lid = log.id
    if not lid:
        return rtn

    rtn['id'] = lid

    def update(name, value):
        if value:
            try:
                iter(value)
            except TypeError:
                pass
            else:
                if any(isinstance(x, (Logbook, Tag)) for x in value):
                    value = [v.name for v in value]
                if any(isinstance(x, Property) for x in value):
                    value = {p.name: {n: p.attributes[n]
                                      for n in p.attribute_names}
                             for p in value}
                else:
                    value = value
            rtn[name] = value

    update('create_time', log.create_time)
    update('modify_time', log.modify_time)
    update('text', log.text)
    update('owner', log.owner)
    update('logbooks', log.logbooks)
    update('tags', log.tags)
    update('attachments', log.attachments)
    update('properties', log.properties)

    return rtn


class SimpleOlogClient(object):
    """
    Client interface to Olog

    This class can be used as a simple interface to the Olog
    for creating and searching for log entries.

    """

    def __init__(self, *args, **kwargs):
        """Initiate a session

        Initiate a session to communicate with the Olog server. the `args`
        and `kwargs` are passed onto the `OlogClient` as the initialization
        parameters.

        See Also
        --------

        OlogClient : Client interface to the Olog

        """
        self.session = OlogClient(*args, **kwargs)

    @property
    def tags(self):
        """Return a list of tags

        Returns a list of the tag names associated with the Olog
        instance.

        Returns
        -------

        list
            Tag names as string
        """
        return [t.name for t in self.session.list_tags()]

    @property
    def logbooks(self):
        """Return logbook names

        Returns a list of logbook names associated with the
        Olog instance.

        Returns
        -------

        list
            Logbook names as string
        """
        return [l.name for l in self.session.list_logbooks()]

    @property
    def properties(self):
        """Return property names

        Returns a list of the property names associated with the Olog
        instance.

        Returns
        -------

        dict
            dictionary with keys as property names and attributes as
            a list of the properties attributes

        """
        return {l.name: l.attribute_names
                for l in self.session.list_properties()}

    def create_logbook(self, logbook, owner=None):
        """Create a logbook

        Create a logbook in the current Olog instance.

        Parameters
        ----------
        logbook : string
            Name of logbook to create
        owner : string, optional
            Owner of logbook (defaults to default from config file)

        """
        logbook = Logbook(logbook, owner)
        return self.session.createLogbook(logbook)

    def create_tag(self, tag, active=True):
        """Create a tag

        Create a tag in the current olog instance.

        Parameters
        ----------
        tag : string
            Name of tag to create
        active : bool, optional
            State of the tag

        """

        tag = Tag(tag, active)
        self.session.createTag(tag)

    def create_property(self, property, keys):
        """Create a property

        Create a property in the current olog instance.

        Parameters
        ----------

        property : string
            Name of property to create
        keys : list of strings
            Keys of the peoperty

        """
        keys_dict = dict()
        [keys_dict.update({k: ''}) for k in keys]
        property = Property(property, keys_dict)
        self.session.createProperty(property)

    def find(self, **kwargs):
        """Find log entries

        Find (search) for log entries based on keyword arguments.

        Parameters
        ----------
        id : int
            Search for logbook with ID id.
        search : string
            Search logbook text for string.
        tag : string
            Find log entries with tags matching tag.
        logbook : string
            Find log entries in logbooks logbook.
        property : string
            Find log entries with a property matching property.
        start : float
            Find log entries created after time start. Time should be a
            float of the number of seconds since the unix Epoch.
        stop : float
            Find log entries created before time stop. Time should be a
            float of the number of seconds since the unix Epoch.

        Returns
        -------
        dictionary
            Dictionary of logbook entries matching seach criteria.

        Examples
        --------
        Search for the log entry with an ID 100::

        >>>soc = SimpleOlogClient()
        >>>result = soc.find(id=100)

        Search for log entries with the log entry matching "Timing" which
        were created in the last hour with a tag matchin "magnets"::

        >>>soc = SimpleOlogClient()
        >>>result = soc.find(string='*Timing*', tag='magnets',
                             start = time.time() - 3600)


        """

        results = self.session.find(**kwargs)
        return [logentry_to_dict(result) for result in results]

    def log(self, text=None, logbooks=None, tags=None, properties=None,
            attachments=None, verify=True, ensure=False):
        """ Create log entry.

        Create a single log entry in the Olog instance.

        Parameters
        ----------
        text : string
            The body of the log entry.
        logbooks : string or list of strings
            The logbooks which to add the log entry to.
        tags : string or list of strings
            The tags to add to the log entry.
        properties : dict of property dicts
            The properties to add to the log entry
        attachments : list of file like objects
            The attachments to add to the log entry
        verify : bool
            Check that properties, tags and logbooks are in the Olog
            instance.
        ensure : bool
            If a property, tag or logbook is not in the Olog then
            create the property, tag or logbook before making the log
            entry. Seting ensure to True will set verify to False.

        Raises
        ------

        ValueError
            If the property, tag or logbook does not exist and ensure is
            True.

        Returns
        -------
        int
            The id of the log entry created.

        """
        log_entry = self._build_entry(text, logbooks, tags, properties,
                                      attachments, verify, ensure)
        return self.session.log(log_entry)

    def update(self, log_id, text=None, logbooks=None, tags=None,
               properties=None, attachments=None, verify=True, ensure=False):
        """Update an existing log entry. This OVERWRITES; it does not append.

        Parameters
        ----------
        log_id : int
            The ID of the log entry to be updated.
        text : string
            The body of the log entry.
        logbooks : string or list of strings
            The logbooks which to add the log entry to.
        tags : string or list of strings
            The tags to add to the log entry.
        properties : dict of property dicts
            The properties to add to the log entry
        attachments : list of file like objects
            The attachments to add to the log entry
        verify : bool
            Check that properties, tags and logbooks are in the Olog
            instance.
        ensure : bool
            If a property, tag or logbook is not in the Olog then
            create the property, tag or logbook before making the log
            entry. Seting ensure to True will set verify to False.

        Raises
        ------

        ValueError
            If the property, tag or logbook does not exist and ensure is
            True.
        """
        log_entry = self._build_entry(text, logbooks, tags, properties,
                                      attachments, verify, ensure)
        return self.session.updateLog(log_id, log_entry)

    def _build_entry(self, text, logbooks, tags, properties, attachments,
                     verify, ensure):
        """
        Common input validation used by methods log and update.

        See docstrings for log or update for details about parameters.
        """
        if ensure:
            verify = False

        if logbooks:
            if isinstance(logbooks, six.string_types):
                logbooks = [logbooks]
        if tags:
            if isinstance(tags, six.string_types):
                tags = [tags]
        if attachments:
            if isinstance(attachments, (Attachment, io.IOBase)):
                attachments = [attachments]

        if logbooks:
            for x in logbooks:
                if x not in self.logbooks:
                    if ensure:
                        self.create_logbook(x)
                    if verify:
                        raise ValueError("Logbook {} does not exist in Olog"
                                         .format(x))

            logbooks = [Logbook(n) for n in logbooks]

        if tags:
            for x in tags:
                if x not in self.tags:
                    if ensure:
                        self.create_tag(x)
                    if verify:
                        raise ValueError("Tag {} does not exist in Olog"
                                         .format(x))

            tags = [Tag(n) for n in tags]

        if properties:
            for x, y in properties.items():
                if x not in self.properties:
                    if ensure:
                        self.create_property(x, y.keys())
                    if verify:
                        raise ValueError("Property {} does not exist in Olog".
                                         format(x))

            properties = [Property(a, b) for a, b in properties.items()]

        toattach = []
        if attachments:
            for a in attachments:
                if isinstance(a, Attachment):
                    toattach.append(a)
                elif isinstance(a, io.IOBase):
                    toattach.append(Attachment(a))
                else:
                    raise ValueError("Attachments must be file objects or \
                                     Olog Attachment objects")

        log_entry = LogEntry(text, logbooks=logbooks,
                             tags=tags, properties=properties,
                             attachments=toattach)
        return log_entry
