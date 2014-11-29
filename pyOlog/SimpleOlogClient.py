__author__ = "swilkins"
"""
A simple API to the Olog client in python
"""

import os
from tempfile import NamedTemporaryFile
from subprocess import call

import getpass
import keyring

from .utils import get_screenshot
from .OlogClient import OlogClient
from .OlogDataTypes import LogEntry, Logbook, Tag, Attachment

class SimpleOlogClient(object):
  def __init__(self, url = None, username = None, password = None):
    """Initiate a session and do password caching using keyring"""
    if username is None:
      username = getpass.getuser()
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

  def screenshot(self, *args, **kwargs):
    """Make a screenshot of an area and add a log entry"""
    sha = get_screenshot()
    if 'attachments' in kwargs:
      if isinstance(kwargs['attachments'], list):
        kwargs['attachments'].append(sha)
      else:
        kwargs['attachments'] = [kwargs['attachments'], sha]
    else:
      kwargs['attachments'] = [sha]
    self.log(*args, **kwargs)

  def savefig(self, *args, **kwargs):
    """Save a matplotlib figure to the logbook"""
    import matplotlib.pyplot as plt
    import StringIO
    
    imgdata = StringIO.StringIO()
    plt.savefig(imgdata, format = 'png', **kwargs)
    imgdata.seek(0)

    a = Attachment(imgdata, 'plot.png')

    if 'attachments' in kwargs:
      if isinstance(kwargs['attachments'], list):
        kwargs['attachments'] += [a]
      else:
        kwargs['attachments'] = [kwargs['attachments'], a]
    else:
      kwargs['attachments'] = [a]
    
    self.log(*args, **kwargs)

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
      with NamedTemporaryFile(suffix='.tmp') as tempfile:
        editor = os.environ.get('EDITOR', 'vim')
        call([editor, tempfile.name])
        text = tempfile.read()

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

