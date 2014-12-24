'''
Copyright (c) 2010 Brookhaven National Laboratory
All rights reserved. Use is subject to license terms and conditions.

Created on Jan 10, 2013

@author: shroffk
'''
import logging

logger = logging.getLogger(__name__)

KEYRING_NAME = 'olog'
try:
    from keyring import get_password
except ImportError:
    have_keyring = False
    logger.warning("No keyring module found")
else:
    have_keyring = True

from getpass import getpass

import requests

#
# Disable warning for non verified HTTPS requests
#
from requests.packages import urllib3
urllib3.disable_warnings()

from json import JSONEncoder, JSONDecoder
from urllib import urlencode
from collections import OrderedDict

import tempfile

from OlogDataTypes import LogEntry, Logbook, Tag, Property, Attachment
from conf import _conf


class OlogClient(object):
    '''
    classdocs
    '''
    json_header = {'content-type': 'application/json',
                   'accept': 'application/json'}
    logs_resource = '/resources/logs'
    properties_resource = '/resources/properties'
    tags_resource = '/resources/tags'
    logbooks_resource = '/resources/logbooks'
    attachments_resource = '/resources/attachments'

    def __init__(self, url=None, username=None, password=None, ask=True):
        '''
        Initialize OlogClient and configure session

        :param url: The base URL of the Olog glassfish server.
        :param username: The username for authentication.
        :param password: The password for authentication.

        If :param username: is None, then the username will be read
        from the config file. If no :param username: is avaliable then
        the session is opened without authentication.

        If  :param ask: is True, then the olog will try using both
        the keyring module and askpass to get a password.

        '''
        self._url = _conf.getValue('url', url)
        self.verify = False
        username = _conf.getValue('username', username)
        password = _conf.getValue('password', password)

        if username and not password and ask:
            # try methods for a password
            if have_keyring:
                password = get_password(KEYRING_NAME, username)

            # If it is not in the keyring, or we don't have that module
            if not password:
                logger.info("Password not found in keyring")
                password = getpass("Olog Password (username = {}):"
                                   .format(username))

        logger.info("Using base URL %s", self._url)

        if username and password:
            # If we have a valid username and password, setup authentication

            logger.info("Using username %s for authentication.",
                        username)
            self._auth = requests.auth.HTTPBasicAuth(username, password)
        else:

            # Don't use authentication
            logger.info("No authentiation configured.")
            self._auth = None

        self._session = requests.Session()
        self._session.auth = self._auth

    def _get(self, url, **kwargs):
        """Do an http GET request"""
        resp = self._session.get(url, verify=self.verify,
                                 auth=self._auth,
                                 headers=self.json_header,
                                 **kwargs)
        resp.raise_for_status()
        return resp

    def _put(self, url, **kwargs):
        """Do an http put request"""
        resp = self._session.put(url, verify=self.verify,
                                 headers=self.json_header,
                                 auth=self._auth,
                                 **kwargs)
        resp.raise_for_status()
        return resp

    def _post(self, url, **kwargs):
        """Do an http post request"""
        resp = self._session.post(url, verify=self.verify,
                                  headers=self.json_header,
                                  auth=self._auth, **kwargs)
        resp.raise_for_status()
        return resp

    def _delete(self, url, **kwargs):
        """Do an http delete request"""
        resp = self._session.delete(url, verify=self.verify,
                                    headers=self.json_header,
                                    auth=self._auth, **kwargs)
        resp.raise_for_status()
        return resp

    def log(self, log_entry):
        '''
        Create a log entry

        :param log_entry: An instance of LogEntry to add to the Olog

        '''
        resp = self._post(self._url + self.logs_resource,
                          data=LogEntryEncoder().encode(log_entry))
        id = LogEntryDecoder().dictToLogEntry(resp.json()[0]).getId()

        # Handle attachments

        for attachment in log_entry.getAttachments():
            url = "{0}{1}/{2}".format(self._url, self.attachments_resource,
                                      str(id))
            resp = self._post(url, files={'file': attachment.getFilePost()})

    def createLogbook(self, logbook):
        '''
        Create a Logbook

        :param logbook: An instance of Logbook to create in the Olog.
        '''
        url = "{0}{1}/{2}".format(self._url, self.logbooks_resource,
                                  logbook.getName())
        self._put(url, data=LogbookEncoder().encode(logbook))

    def createTag(self, tag):
        '''
        Create a Tag

        :param tag: An instance of Tag to create in the Olog.
        '''
        url = "{0}{1}/{2}".format(self._url, self.tags_resource,
                                  tag.getName())
        self._put(url, data=TagEncoder().encode(tag))

    def createProperty(self, property):
        '''
        Create a Property

        :param property: An instance of Property to create in the Olog.
        '''
        url = "{0}{1}/{2}".format(self._url, self.properties_resource,
                                  property.getName())
        # p = PropertyEncoder().encode(property)
        self._put(url, data=PropertyEncoder().encode(property))

    def find(self, **kwds):
        '''
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
        '''
        # search = '*' + text + '*'
        query_string = "{0}{1}?{2}".format(self._url,
                                           self.logs_resource,
                                           urlencode(OrderedDict(kwds)))
        resp = self._get(query_string)

        logs = []
        for jsonLogEntry in resp.json():
            logs.append(LogEntryDecoder().dictToLogEntry(jsonLogEntry))

        return logs

    def listAttachments(self, logEntryId):
        '''
        Search for attachments on a logentry

        :param logEntryId: The ID of the log entry to list the attachments.
        '''
        url = "{0}{1}/{2}".format(self._url, self.attachments_resource,
                                  str(logEntryId))
        resp = self._get(url)

        attachments = []
        for jsonAttachment in resp.json().pop('attachment'):
            fileName = jsonAttachment.pop('fileName')
            url = "{0}{1}/{2}/{3}".format(self._url, self.attachments_resource,
                                          str(logEntryId), fileName)
            f = self._get(url)
            testFile = tempfile.NamedTemporaryFile(delete=False)
            testFile.name = fileName
            testFile.write(f.content)
            attachments.append(Attachment(file=testFile))
        return attachments

    def listTags(self):
        '''
        List all tags in the Olog.
        '''
        resp = self._get(self._url + self.tags_resource)

        tags = []
        for jsonTag in resp.json().pop('tag'):
            tags.append(TagDecoder().dictToTag(jsonTag))
        return tags

    def listLogbooks(self):
        '''
        List all logbooks in the Olog.
        '''
        resp = self._get(self._url + self.logbooks_resource)

        logbooks = []
        for jsonLogbook in resp.json().pop('logbook'):
            logbooks.append(LogbookDecoder().dictToLogbook(jsonLogbook))
        return logbooks

    def listProperties(self):
        '''
        List all Properties and their attributes in the Olog.
        '''
        resp = self._get(self._url + self.properties_resource)

        properties = []
        for jsonProperty in resp.json().pop('property'):
            properties.append(PropertyDecoder().dictToProperty(jsonProperty))
        return properties

    def delete(self, **kwds):
        '''
        Method to delete a logEntry, logbook, property, tag.

        :param logEntryId: ID of log entry to delete.
        :param logbookName: The name (as a string) of the logbook to delete.
        :param tagName: The name (as a string) of the tag to delete.
        :param propertyName: The name (as a string) of the property to delete.

        Example:

        delete(logEntryId = int)
        >>> delete(logEntryId=1234)

        delete(logbookName = String)
        >>> delete(logbookName = 'logbookName')

        delete(tagName = String)
        >>> delete(tagName = 'myTag')
        # tagName = tag name of the tag to be deleted
        (it will be removed from all logEntries)

        delete(propertyName = String)
        >>> delete(propertyName = 'position')
        # propertyName = property name of property to be deleted
        (it will be removed from all logEntries)
        '''
        if len(kwds) == 1:
            self.__handleSingleDeleteParameter(**kwds)
        else:
            raise ValueError('Can only delete a single Logbook/tag/property')

    def __handleSingleDeleteParameter(self, **kwds):
        if 'logbookName' in kwds:
            url = "{0}{1}/{2}".format(self._url, self.logbooks_resource,
                                      kwds['logbookName'].strip())
            self._delete(url)

        elif 'tagName' in kwds:
            url = "{0}{1}/{2}".format(self._url, self.logbooks_resource,
                                      kwds['tagName'].strip())
            self._delete(url)

        elif 'propertyName' in kwds:
            url = "{0}{1}/{2}".format(self._url, self.logbooks_resource,
                                      kwds['propertyName'].strip())
            data = PropertyEncoder().encode(Property(
                kwds['propertyName'].strip()))
            self._delete(url, data=data)

        elif 'logEntryId' in kwds:
            url = "{0}{1}/{2}".format(self._url, self.logbooks_resource,
                                      kwds['logEntryId'].strip())
            self._delete(url)

        else:
            raise ValueError('Unknown Key')


class PropertyEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Property):
            test = {}
            for key in obj.getAttributes():
                test[str(key)] = str(obj.getAttributeValue(key))
            prop = OrderedDict()
            prop["name"] = obj.getName()
            prop["attributes"] = test
            return prop
        return JSONEncoder.default(self, obj)


class PropertyDecoder(JSONDecoder):

    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.dictToProperty)

    def dictToProperty(self, d):
        if d:
            return Property(name=d.pop('name'), attributes=d.pop('attributes'))


class LogbookEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Logbook):
            return {"name": obj.getName(), "owner": obj.getOwner()}
        return JSONEncoder.default(self, obj)


class LogbookDecoder(JSONDecoder):

    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.dictToLogbook)

    def dictToLogbook(self, d):
        if d:
            return Logbook(name=d.pop('name'), owner=d.pop('owner'))
        else:
            return None


class TagEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Tag):
            return {"state": obj.getState(), "name": obj.getName()}
        return JSONEncoder.default(self, obj)


class TagDecoder(JSONDecoder):

    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.dictToTag)

    def dictToTag(self, d):
        if d:
            return Tag(name=d.pop('name'), state=d.pop('state'))
        else:
            return None


class LogEntryEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, LogEntry):
            logbooks = []
            for logbook in obj.getLogbooks():
                logbooks.append(LogbookEncoder().default(logbook))
            tags = []
            for tag in obj.getTags():
                tags.append(TagEncoder().default(tag))
            properties = []
            for property in obj.getProperties():
                properties.append(PropertyEncoder().default(property))
            return [{"description": obj.getText(),
                     "owner": obj.getOwner(), "level": "Info",
                     "logbooks": logbooks, "tags": tags,
                     "properties": properties}]
        return JSONEncoder.default(self, obj)


class LogEntryDecoder(JSONDecoder):

    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.dictToLogEntry)

    def dictToLogEntry(self, d):
        if d:
            logbooks = [LogbookDecoder().dictToLogbook(logbook)
                        for logbook in d.pop('logbooks')]

            tags = [TagDecoder().dictToTag(tag) for tag in d.pop('tags')]

            properties = [PropertyDecoder().dictToProperty(property)
                          for property in d.pop('properties')]
            return LogEntry(text=d.pop('description'),
                            owner=d.pop('owner'),
                            logbooks=logbooks, tags=tags,
                            properties=properties,
                            id=d.pop('id'),
                            createTime=d.pop('createdDate'),
                            modifyTime=d.pop('modifiedDate'))
        else:
            return None


# class Ssl3HttpAdapter(HTTPAdapter):
#     """"Transport adapter" that allows us to use SSLv3."""
#
#     def init_poolmanager(self, connections, maxsize, block=False):
#         self.poolmanager = PoolManager(num_pools=connections,
#                                        maxsize=maxsize,
#                                        block=block,
#                                        # ssl_version=ssl.PROTOCOL_SSLv3,
#                                        cert_reqs='CERT_REQUIRED',
#                                        ca_certs=certifi.where())
