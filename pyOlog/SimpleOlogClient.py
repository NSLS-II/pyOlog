__author__ = "swilkins"
"""
A simple API to the Olog client in python
"""

import getpass
import keyring

from .utils import get_text_from_editor
from .OlogClient import OlogClient
from .OlogDataTypes import LogEntry, Logbook, Tag, Attachment

from .conf import _conf

class SimpleOlogClient(object):
  def __init__(self, url = None, username = None, password = None):
    """Initiate a session and do password caching using keyring"""

    # First check config file for defaults


    if username is None:
      if _conf.getValue('username'):
        username = _conf.getValue('username')
      else:
        username = getpass.getuser()

    if password is None:
      if _conf.getValue('password'):
        password = _conf.getValue('password')
      if password is None:
        password = keyring.get_password('olog', username)
      if password is None:
        password = getpass.getpass("Olog Password (username = {}) :".format(username))

    if username and not password:
      raise Exception("Unable to obtain password and authentication requested.")
    self.session = OlogClient(username = username, password = password)

  def getTags(self):
    """Return a list of tag names in the Olog"""
    return [t.getName() for t in self.session.listTags()]

  def getLogbooks(self):
    """Return a list of tag names in the Olog"""
    return [l.getName() for l in self.session.listLogbooks()]

  def log(self, text = None, logbooks = None, tags = None, properties = None,
                attachments = None, verify = True):
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
        if not any([x in logbooks for x in self.getLogbooks()]):
          raise ValueError("Invalid Logbook name (not in Olog)")
      logbooks = [Logbook(n) for n in logbooks]

    if tags:
      if verify:
        if not any([x in tags for x in self.getTags()]):
          raise ValueError("Invalid Tag (not in Olog)")
      tags     = [Tag(n) for n in tags]

    if not text:
      text = get_text_from_editor()

    toattach = []
    if attachments:
      for a in attachments:
        if  isinstance(a, Attachment):
          toattach.append(a)
        else:
          toattach.append(Attachment(open(a)))

    log = LogEntry(text, logbooks = logbooks,
                   tags = tags, attachments = toattach)
    self.session.log(log)

