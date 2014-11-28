'''
Copyright (c) 2010 Brookhaven National Laboratory
All rights reserved. Use is subject to license terms and conditions.

Created on Jan 10, 2013

@author: shroffk
'''
import logging, sys
fmt = logging.Formatter("%(asctime)-15s [%(name)5s:%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(fmt)
logger.addHandler(handler)

from getpass import getpass

import requests
from requests.adapters import HTTPAdapter
from requests import auth

import json
from json import JSONEncoder, JSONDecoder

from urllib import urlencode
from urllib3.poolmanager import PoolManager

from collections import OrderedDict

import tempfile
import ssl 

from OlogDataTypes import LogEntry, Logbook, Tag, Property, Attachment
from _conf import _conf

try:
  import keyring
except ImportError:
  have_keyring = False
else:
  have_keyring = True


class OlogClient(object):
    '''
    classdocs
    '''
    __jsonheader = {'content-type':'application/json', 'accept':'application/json'}
    __logsResource = '/resources/logs' 
    __propertiesResource = '/resources/properties'
    __tagsResource = '/resources/tags'
    __logbooksResource = '/resources/logbooks'
    __attachmentResource = '/resources/attachments'

    def __init__(self, url=None, username=None, password=None, interactive = True):
        '''
        Initialize OlogClient and configure session

        :param url: The base URL of the Olog glassfish server.
        :param username: The username for authentication.
        :param password: The password for authentication.
        :param interactive: If true then if no password is found, ask for it on th
          console
        
        If :param username: is None, then the username will be read from the config
        file. If no :param username: is avaliable then the session is opened without
        authentication. 

        If :param password: is None then the password will be read from the config file
        if this is not set, then if the keyring package is avaliable it will be read 
        from the gnome keyring. Failing that, if interactive is true, it will be asked
        for on the command line.
        '''

        self.__url = self.__getDefaultConfig('url', url)
        self.__username = self.__getDefaultConfig('username', username)
        self.__password = self.__getDefaultConfig('password', password)
        
        logger.info("Using base URL %s", self.__url)

        if self.__username and not self.__password:
          # Try to get password from keyring
          if have_keyring:
            logger.info("Checking keyring for username %s", self.__username)
            self.__password = keyring.get_password('olog', self.__username)
            if self.__password:
              logger.info("Password obtained from keyring.")
            else:
              logger.info("No password in keyring.")
          else:
            logger.info("No keyring avaliable")
          # If this did not work (no passwd or no keyring)
          if self.__password is None and interactive:
            self.__password = getpass('Olog Password for {}:'.format(self.__username))
        if self.__username and self.__password:
            logger.info("Using username %s for authentication.", self.__username)
            self.__auth = auth.HTTPBasicAuth(self.__username, self.__password)
        else:
            logger.info("No authentiation configured.")
            self.__auth = None
        
        self.__session = requests.Session()
        self.__session.mount('https://', Ssl3HttpAdapter())
        self.__session.get(self.__url + self.__tagsResource, verify=False, headers=self.__jsonheader).raise_for_status()
    
    def __getDefaultConfig(self, arg, value):
        '''
        If Value is None, this will try to find the value in one of the configuration files
        '''
        if value == None and _conf.has_option('DEFAULT', arg):
            return _conf.get('DEFAULT', arg)
        else:
            return value
    
    def log(self, logEntry):
        '''
        Create a log entry

        :param logEntry: An instance of LogEntry to add to the Olog

        '''
        resp = self.__session.post(self.__url + self.__logsResource,
                     data=LogEntryEncoder().encode(logEntry),
                     verify=False,
                     headers=self.__jsonheader,
                     auth=self.__auth)
        resp.raise_for_status()
        id = LogEntryDecoder().dictToLogEntry(resp.json()[0]).getId()
        '''Attachments'''
        for attachment in logEntry.getAttachments():
            resp = self.__session.post(self.__url + self.__attachmentResource +'/'+ str(id),
                                  verify=False,
                                  auth=self.__auth,
                                  files={'file': attachment.getFilePost()}
                                  )
            resp.raise_for_status()
            
            
    
    def createLogbook(self, logbook):
        '''
        Create a Logbook

        :param logbook: An instance of Logbook to create in the Olog.
        '''
        self.__session.put(self.__url + self.__logbooksResource + '/' + logbook.getName(),
                     data=LogbookEncoder().encode(logbook),
                     verify=False,
                     headers=self.__jsonheader,
                     auth=self.__auth).raise_for_status()
        
        
    def createTag(self, tag):
        '''
        Create a Tag

        :param tag: An instance of Tag to create in the Olog.
        '''
        url = self.__url + self.__tagsResource + '/' + tag.getName()
        self.__session.put(url,
                     data=TagEncoder().encode(tag),
                     verify=False,
                     headers=self.__jsonheader,
                     auth=self.__auth).raise_for_status()
        
    def createProperty(self, property):
        '''
        Create a Property

        :param property: An instance of Property to create in the Olog.
        '''
        url = self.__url + self.__propertiesResource + '/' + property.getName()
        p = PropertyEncoder().encode(property)
        self.__session.put(url,
                     data=PropertyEncoder().encode(property),
                     verify=False,
                     headers=self.__jsonheader,
                     auth=self.__auth).raise_for_status()
        
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
        find all the log entries made between the epoc times 123243434 and 123244434
        
        Searching using multiple criteria
        >>find(logbook='contorls', tag='magnets')
        find all the log entries in logbook 'controls' AND with tag named 'magnets'
        '''
        #search = '*' + text + '*'
        query_string = self.__url + self.__logsResource + '?' + urlencode(OrderedDict(kwds))
        resp = self.__session.get(query_string,
                            verify=False,
                            headers=self.__jsonheader,
                            auth=self.__auth
                            )
        resp.raise_for_status()
        logs = []
        for jsonLogEntry in resp.json():            
            logs.append(LogEntryDecoder().dictToLogEntry(jsonLogEntry))
        return logs
    
    def listAttachments(self, logEntryId):
        '''
        Search for attachments on a logentry

        :param logEntryId: The ID of the log entry to list the attachments.
        '''
        resp = self.__session.get(self.__url+self.__attachmentResource+'/'+str(logEntryId),
                         verify=False,
                         headers=self.__jsonheader)
        resp.raise_for_status()
        attachments = []
        for jsonAttachment in resp.json().pop('attachment'):
            fileName = jsonAttachment.pop('fileName')
            f = self.__session.get(self.__url+
                             self.__attachmentResource+'/'+
                             str(logEntryId)+'/'+
                             fileName,
                             verify=False)
            testFile = tempfile.NamedTemporaryFile(delete=False)
            testFile.name = fileName
            testFile.write(f.content)
            attachments.append(Attachment(file=testFile))
        return attachments           
    
    def listTags(self):
        '''
        List all tags in the Olog.
        '''
        resp = self.__session.get(self.__url + self.__tagsResource,
                            verify=False,
                            headers=self.__jsonheader,
                            auth=self.__auth)
        resp.raise_for_status()
        tags = []
        for jsonTag in resp.json().pop('tag'):
            tags.append(TagDecoder().dictToTag(jsonTag))
        return tags
    
    def listLogbooks(self):
        '''
        List all logbooks in the Olog.
        '''
        resp = self.__session.get(self.__url + self.__logbooksResource,
                            verify=False,
                            headers=self.__jsonheader,
                            auth=self.__auth)
        resp.raise_for_status()
        logbooks = []
        for jsonLogbook in resp.json().pop('logbook'):
            logbooks.append(LogbookDecoder().dictToLogbook(jsonLogbook))
        return logbooks
    
    def listProperties(self):
        '''
        List all Properties and their attributes in the Olog.
        '''
        resp = self.__session.get(self.__url + self.__propertiesResource,
                            verify=False,
                            headers=self.__jsonheader,
                            auth=self.__auth)
        resp.raise_for_status()
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
        # tagName = tag name of the tag to be deleted (it will be removed from all logEntries)
        
        delete(propertyName = String)
        >>> delete(propertyName = 'position')
        # propertyName = property name of property to be deleted (it will be removed from all logEntries)
        '''
        if len(kwds) == 1:
            self.__handleSingleDeleteParameter(**kwds)
        else:
            raise Exception, 'incorrect usage: Delete a single Logbook/tag/property'
        
        
    def __handleSingleDeleteParameter(self, **kwds):
        if 'logbookName' in kwds:
            self.__session.delete(self.__url + self.__logbooksResource + '/' + kwds['logbookName'].strip(),
                        verify=False,
                        headers=self.__jsonheader,
                        auth=self.__auth).raise_for_status()
            pass
        elif 'tagName' in kwds:
            self.__session.delete(self.__url + self.__tagsResource + '/' + kwds['tagName'].strip(),
                        verify=False,
                        headers=self.__jsonheader,
                        auth=self.__auth).raise_for_status()
            pass
        elif 'propertyName' in kwds:               
            self.__session.delete(self.__url + self.__propertiesResource + '/' + kwds['propertyName'].strip(),
                            data=PropertyEncoder().encode(Property(kwds['propertyName'].strip(), attributes={})),
                            verify=False,
                            headers=self.__jsonheader,
                            auth=self.__auth).raise_for_status()
            pass
        elif 'logEntryId' in kwds:
            self.__session.delete(self.__url + self.__logsResource + '/' + str(kwds['logEntryId']).strip(),
                            verify=False,
                            headers=self.__jsonheader,
                            auth=self.__auth).raise_for_status()
            pass
        else:
            raise Exception, ' unkown key, use logEntryId, logbookName, tagName or propertyName'

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
        return json.JSONEncoder.default(self, obj)

class PropertyDecoder(JSONDecoder):
    
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dictToProperty)
        
    def dictToProperty(self, d):
        if d:
            return Property(name=d.pop('name'), attributes=d.pop('attributes'))
    
class LogbookEncoder(JSONEncoder):
    
    def default(self, obj):
        if isinstance(obj, Logbook):
            return {"name":obj.getName(), "owner":obj.getOwner()}
        return json.JSONEncoder.default(self, obj)

class LogbookDecoder(JSONDecoder):
    
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dictToLogbook)
        
    def dictToLogbook(self, d):
        if d:
            return Logbook(name=d.pop('name'), owner=d.pop('owner'))
        else:
            return None
        
class TagEncoder(JSONEncoder):
       
    def default(self, obj):
        if isinstance(obj, Tag):
            return {"state": obj.getState(), "name": obj.getName()}
        return json.JSONEncoder.default(self, obj)
                
class TagDecoder(JSONDecoder):
    
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dictToTag)
        
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
            return [{"description":obj.getText(),
                   "owner":obj.getOwner(),
                   "level":"Info",
                   "logbooks":logbooks,
                   "tags":tags,
                   "properties":properties}]
        return json.JSONEncoder.default(self, obj)

class LogEntryDecoder(JSONDecoder):
    
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dictToLogEntry)
        
    def dictToLogEntry(self, d):
        if d:
            return LogEntry(text=d.pop('description'),
                            owner=d.pop('owner'),
                            logbooks=[LogbookDecoder().dictToLogbook(logbook) for logbook in d.pop('logbooks')],
                            tags=[TagDecoder().dictToTag(tag) for tag in d.pop('tags')],
                            properties=[PropertyDecoder().dictToProperty(property) for property in d.pop('properties')],
                            id=d.pop('id'),
                            createTime=d.pop('createdDate'),
                            modifyTime=d.pop('modifiedDate'))
        else:
            return None


class Ssl3HttpAdapter(HTTPAdapter):
    """"Transport adapter" that allows us to use SSLv3."""

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_SSLv3)
