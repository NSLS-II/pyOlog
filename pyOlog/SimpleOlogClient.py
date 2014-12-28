__author__ = "swilkins"
"""
A simple API to the Olog client in python
"""

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
    def __init__(self, *args, **kwargs):
        """Initiate a session """
        self.session = OlogClient(*args, **kwargs)

    @property
    def tags(self):
        """Return a list of tag names in the Olog"""
        return [t.name for t in self.session.list_tags()]

    @property
    def logbooks(self):
        """Return a list of logbooks names in the Olog"""
        return [l.name for l in self.session.list_logbooks()]

    @property
    def properties(self):
        """Return a list of propertys in the Olog"""
        return [(l.name, l.attribute_names)
                for l in self.session.list_properties()]

    def create_logbook(self, logbook, owner=None):
        """Create a logbook

        :param logbook: Name of logbook to create
        :param owner: Owner of logbook (defaults to default from config file)
        """
        logbook = Logbook(logbook, owner)
        self.session.createLogbook(logbook)

    def create_tag(self, tag, active=True):
        """Create a tag

        :param tag: Name of tag to create
        :param active: State of tag
        """

        tag = Tag(tag, active)
        self.session.createTag(tag)

    def create_property(self, property, keys):
        """Create a property

        :param property: Name of property
        :param keys: Name of keys associated with the property.
        """
        keys_dict = dict()
        [keys_dict.update({k: ''}) for k in keys]
        property = Property(property, keys_dict)
        self.session.createProperty(property)

    def find(self, **kwargs):
        """Find log entries which match kwargs

        Search for logEntries based on one or many search criteria
        >> find(search='*Timing*')
        find logentries with the text Timing in the description

        >> find(tag='magnets')
        find log entries with the a tag named 'magnets'

        >> find(logbook='controls')
        find log entries in the logbook named 'controls'

        >> find(property='context')
        find log entires with property named 'context'

        >> find(start=str(time.time() - 3600)
        find the log entries made in the last hour
        >> find(start=123243434, end=123244434)
        find all the log entries made between the epoc times 123243434
        and 123244434

        Searching using multiple criteria
        >>find(logbook='contorls', tag='magnets')
        find all the log entries in logbook 'controls' AND with tag
        named 'magnets'
        """

        results = self.session.find(**kwargs)
        return [logentry_to_dict(result) for result in results]

    def log(self, text=None, logbooks=None, tags=None, properties=None,
            attachments=None, verify=True):
        """
        Create olog entry.

        :param str text: String of the olog entry to make.
        :param logbooks: Logbooks to make entry into.
        :type logbooks: None, List or string
        :param tags:Tags to apply to logbook entry.
        :type tags: None, List or string

        """

        if logbooks:
            if isinstance(logbooks, basestring):
                logbooks = [logbooks]
        if tags:
            if isinstance(tags, basestring):
                tags = [tags]
        if attachments:
            if isinstance(attachments, (Attachment, file)):
                attachments = [attachments]

        if logbooks:
            if verify:
                if not any([x in logbooks for x in self.logbooks]):
                    raise ValueError("Logbook does not exits in Olog")
            logbooks = [Logbook(n) for n in logbooks]

        if tags:
            if verify:
                if not any([x in tags for x in self.tags]):
                    raise ValueError("Tag does not exits in Olog")
            tags = [Tag(n) for n in tags]

        if properties:
            properties = [Property(a, b) for a, b in properties]

        toattach = []
        if attachments:
            for a in attachments:
                if isinstance(a, Attachment):
                    toattach.append(a)
                elif isinstance(a, file):
                    toattach.append(Attachment(a))
                else:
                    raise ValueError("Attachments must be file objects or \
                                     Olog Attachment objects")

        log = LogEntry(text, logbooks=logbooks,
                       tags=tags, properties=properties,
                       attachments=toattach)

        return self.session.log(log)
