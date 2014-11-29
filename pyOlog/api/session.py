__author__ = 'swilkins'
from ..OlogClient import OlogClient

import keyring
import getpass 

def init_session():
  """Initiate a session and do password caching using keyring"""
  username = getpass.getuser()
  password = keyring.get_password('olog', username)
  if password is None:
    password = getpass.getpass("Olog Password (username = {}) :".format(username))
  client = OlogClient(username = username, password = password)
  return client

session = init_session()
