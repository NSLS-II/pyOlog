import logging
from SimpleOlogClient import SimpleOlogClient

class OlogHandler(logging.Handler):
  def __init__(self, logbooks = None, tags = None):
    logging.Handler.__init__(self)
    self.session = SimpleOlogClient()
    self.logbooks = logbooks
    self.tags = tags
  def emit(self, record):
    if hasattr(record, message):
      self.session.log(record.message, logbooks = logbooks, tags = tags)
    else:
      self.session.log(record.msg, logbooks = logbooks, tags = tags)
