__author__ = "swilkins"
"""
A simple API to the Olog client in python
"""

from .OlogClient import OlogClient
from .OlogDataTypes import LogEntry, Logbook, Tag, Attachment, Property


def logentry_to_dict(log):
    rtn = dict()

    lid = log.getId()
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
                    value = [v.getName() for v in value]
                else:
                    value = value
            rtn[name] = value

    update('create_time', log.getCreateTime())
    update('modify_time', log.getModifyTime())
    update('text', log.getText())
    update('owner', log.getOwner())
    update('logbooks', log.getLogbooks())
    update('tags', log.getTags())
    update('attachments', log.getAttachments())
    update('properties', log.getProperties())

    return rtn


class SimpleOlogClient(object):
    def __init__(self, *args, **kwargs):
        """Initiate a session """
        self.session = OlogClient(*args, **kwargs)

    @property
    def tags(self):
        """Return a list of tag names in the Olog"""
        return [t.getName() for t in self.session.listTags()]

    @property
    def logbooks(self):
        """Return a list of logbooks names in the Olog"""
        return [l.getName() for l in self.session.listLogbooks()]

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
        property = Property(property, keys)
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
            if not isinstance(logbooks, list):
                logbooks = [logbooks]
        if tags:
            if not isinstance(tags, list):
                tags = [tags]
        if attachments:
            if not isinstance(attachments, list):
                attachments = [attachments]

        if logbooks:
            if verify:
                if not any([x in logbooks for x in self.get_logbooks()]):
                    raise ValueError("Logbook does not exits in Olog")
            logbooks = [Logbook(n) for n in logbooks]

        if tags:
            if verify:
                if not any([x in tags for x in self.get_tags()]):
                    raise ValueError("Tag does not exits in Olog")
            tags = [Tag(n) for n in tags]

        toattach = []
        if attachments:
            for a in attachments:
                if isinstance(a, Attachment):
                    toattach.append(a)
                else:
                    toattach.append(Attachment(open(a)))

        log = LogEntry(text, logbooks=logbooks,
                       tags=tags, attachments=toattach)
        self.session.log(log)
