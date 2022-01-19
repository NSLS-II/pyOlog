'''
Copyright (c) 2010 Brookhaven National Laboratory
All rights reserved. Use is subject to license terms and conditions.
Created on Jan 10, 2013
@author: shroffk
'''
from __future__ import (print_function, absolute_import)
import logging

logger = logging.getLogger(__name__)

KEYRING_NAME = 'olog'
try:
    import keyring
except ImportError:
    keyring = None
    logger.warning("No keyring module found")
    have_keyring = False
else:
    have_keyring = True

from getpass import getpass

import requests
from requests.packages import urllib3
# Disable warning for non verified HTTPS requests
urllib3.disable_warnings()

from json import JSONEncoder, JSONDecoder
from collections import OrderedDict
import json

from .OlogDataTypes import LogEntry, Logbook, Tag, Property, Attachment
from .conf import _conf



class OlogClient(object):
    json_header = {'content-type': 'application/json',
                   'accept': 'application/json'}
    logs_resource = '/resources/logs'
    properties_resource = '/resources/properties'
    tags_resource = '/resources/tags'
    logbooks_resource = '/resources/logbooks'
    attachments_resource = '/resources/attachments'

    def __init__(self, url=None, username=None, password=None, ask=True, old_olog_api=None):
        '''
        Initialize OlogClient and configure session
        :param url: The base URL of the Olog glassfish server.
        :param username: The username for authentication.
        :param password: The password for authentication.
        :param old_olog_api: Use the old olog api.
        If :param username: is None, then the username will be read
        from the config file. If no :param username: is avaliable then
        the session is opened without authentication.
        If  :param ask: is True, then the olog will try using both
        the keyring module and askpass to get a password.
        If :param old_olog_api: is None, then it will be read from the
        config file. Set to the string "True" or "true" in the config 
        file, any other values will be interpreted as False.
        '''
        self._url = _conf.get_value('url', url)
        self.verify = False
        username = _conf.get_username(username)
        password = _conf.get_value('password', password)
        self._old_olog_api = _conf.get_value('old_olog_api', old_olog_api)
        self._old_olog_api = (self._old_olog_api == True 
                              or self._old_olog_api == 'True' 
                              or self._old_olog_api == 'true')

        if username and not password and ask:
            # try methods for a password
            if keyring:
                password = keyring.get_password(KEYRING_NAME, username)

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
            _auth = (username, password)
        else:

            # Don't use authentication
            logger.info("No authentiation configured.")
            _auth = None

        self._session = requests.Session()
        self._session.auth = _auth
        # self._session.headers.update(self.json_header)
        self._session.verify = self.verify

    def _get(self, url, timeout=(4.2, 30), **kwargs):
        """Do an http GET request"""
        logger.debug("HTTP GET to %s", self._url + url)
        kwargs.update({'headers': self.json_header})
        resp = self._session.get(self._url + url, timeout=timeout, stream=False, **kwargs)
        resp.raise_for_status()
        return resp

    def _put(self, url,timeout=(4.2, 30), **kwargs):
        """Do an http put request"""
        logger.debug("HTTP PUT to %s", self._url + url)
        kwargs.update({'headers': self.json_header})
        resp = self._session.put(self._url + url, timeout=timeout, stream=False, **kwargs)
        resp.raise_for_status()
        return resp

    def _post(self, url, timeout=(4.2, 30), json=True, **kwargs):
        """Do an http post request"""
        logger.debug("HTTP POST to %s", self._url + url)
        if json:
            kwargs.update({'headers': self.json_header})
        resp = self._session.post(self._url + url, timeout=timeout, stream=False, **kwargs)
        resp.raise_for_status()
        return resp

    def _delete(self, url, **kwargs):
        """Do an http delete request"""
        logger.debug("HTTP DELETE to %s", self._url + url)
        kwargs.update({'headers': self.json_header})
        resp = self._session.delete(self._url + url, **kwargs)
        resp.raise_for_status()
        return resp

    def log(self, log_entry):
        '''
        Create a log entry
        :param log_entry: An instance of LogEntry to add to the Olog
        '''
        resp = self._post(self.logs_resource,
                          data=LogEntryEncoder().encode(log_entry))
        if self._old_olog_api:
            id = LogEntryDecoder().dictToLogEntry(resp.json()[0]).id
        else:
            id = LogEntryDecoder().dictToLogEntry(resp.json()['log'][0]).id


        # Handle attachments

        for attachment in log_entry.attachments:
            url = "{0}/{1}".format(self.attachments_resource, id)
            resp = self._post(url, json=False,
                              files={'file': attachment.get_file_post()})

        return id

    def updateLog(self, logId, log_entry):
        '''
        Update a log entry

        :param logId: The id of the log to be updated/modified
        :param log_entry: An instance of the modified version of the LogEntry
        '''
        url = "{0}/{1}".format(self.logs_resource, str(logId))
        resp = self._post(url, data=json.dumps(json.loads(LogEntryEncoder().encode(log_entry))[0]))

        '''Attachments'''
        for attachment in log_entry.attachments:
            url = "{0}/{1}".format(self.attachments_resource, str(logId))
            resp = self._post(url,
                              json=False,
                              files={'file': attachment.get_file_post()})

    def createLogbook(self, logbook):
        '''
        Create a Logbook
        :param logbook: An instance of Logbook to create in the Olog.
        '''
        url = "/".join((self.logbooks_resource, logbook.name))
        self._put(url, data=LogbookEncoder().encode(logbook))

    def createTag(self, tag):
        '''
        Create a Tag
        :param tag: An instance of Tag to create in the Olog.
        '''
        url = "/".join((self.tags_resource, tag.name))
        self._put(url, data=TagEncoder().encode(tag))

    def createProperty(self, property):
        '''
        Create a Property
        :param property: An instance of Property to create in the Olog.
        '''
        url = "/".join((self.properties_resource, property.name))
        p = PropertyEncoder().encode(property)
        self._put(url, data=p)

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
        >> find(start=time.time() - 3600)
        find the log entries made in the last hour
        >> find(start=123243434, end=123244434)
        find all the log entries made between the epoc times 123243434
        and 123244434
        Searching using multiple criteria
        >>find(logbook='contorls', tag='magnets')
        find all the log entries in logbook 'controls' AND with tag
        named 'magnets'
        '''
        resp = self._get(self.logs_resource, params=OrderedDict(kwds))

        logs = []
        for json_log_entry in resp.json():
            logs.append(LogEntryDecoder().dictToLogEntry(json_log_entry))

        return logs

    def list_attachments(self, log_entry_id):
        '''
        Search for attachments on a logentry
        :param log_entry_id: The ID of the log entry to list the attachments.
        '''
        url = "{0}/{1}".format(self.attachments_resource, log_entry_id)
        resp = self._get(url)

        attachments = []
        for jsonAttachment in resp.json().pop('attachment'):
            filename = jsonAttachment.pop('filename')
            url = "{0}/{1}/{2}".format(self.attachments_resource, log_entry_id,
                                       filename)
            f = self._get(url)
            attachments.append(Attachment(file=f.content, filename=filename))

        return attachments

    def list_tags(self):
        '''
        List all tags in the Olog.
        '''
        resp = self._get(self.tags_resource)

        tags = []
        for jsonTag in resp.json().pop('tag'):
            tags.append(TagDecoder().dictToTag(jsonTag))
        return tags

    def list_logbooks(self):
        '''
        List all logbooks in the Olog.
        '''
        resp = self._get(self.logbooks_resource)

        logbooks = []
        for jsonLogbook in resp.json().pop('logbook'):
            logbooks.append(LogbookDecoder().dictToLogbook(jsonLogbook))
        return logbooks

    def list_properties(self):
        '''
        List all Properties and their attributes in the Olog.
        '''
        resp = self._get(self.properties_resource)

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
            url = "/".join((self.logbooks_resource,
                           kwds['logbookName'].strip()))
            self._delete(url)

        elif 'tagName' in kwds:
            url = "/".join((self.tags_resource,
                           kwds['tagName'].strip()))
            self._delete(url)

        elif 'propertyName' in kwds:
            url = "/".join((self.properties_resource,
                           kwds['propertyName'].strip()))
            data = PropertyEncoder().encode(Property(
                kwds['propertyName'].strip()))
            self._delete(url, data=data)

        elif 'logEntryId' in kwds:
            url = "/".join((self.logs_resource,
                           str(kwds['logEntryId'])))
            self._delete(url)

        else:
            raise ValueError('Unknown Key')


class PropertyEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Property):
            attributes = dict()
            for key, value in obj.attributes.items():
                attributes[str(key)] = value
            prop = OrderedDict()
            prop["name"] = obj.name
            prop["attributes"] = attributes
            return prop
        return JSONEncoder.default(self, obj)


class PropertyDecoder(JSONDecoder):
    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.dictToProperty)

    def dictToProperty(self, d):
        if d:
            return Property(name=d.pop('name'),
                            attributes=d.pop('attributes'),
                            )


class LogbookEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Logbook):
            return {"name": obj.name, "owner": obj.owner}
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
            return {"state": obj.state, "name": obj.name}
        return JSONEncoder.default(self, obj)


class TagDecoder(JSONDecoder):
    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.dictToTag)

    def dictToTag(self, d):
        if d:
            t = Tag(name=d.pop('name'))
            t.state = d.pop('state')
            return t
        else:
            return None


class LogEntryEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, LogEntry):
            logbooks = []
            for logbook in obj.logbooks:
                logbooks.append(LogbookEncoder().default(logbook))
            tags = []
            for tag in obj.tags:
                tags.append(TagEncoder().default(tag))
            properties = []
            for property in obj.properties:
                properties.append(PropertyEncoder().default(property))
            return [{"description": obj.text,
                     "owner": obj.owner, "level": "Info",
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
                            create_time=d.pop('createdDate'),
                            modify_time=d.pop('modifiedDate'))
        else:
            return None
