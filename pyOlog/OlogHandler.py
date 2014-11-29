import logging
from SimpleOlogClient import SimpleOlogClient

class OlogHandler(logging.Handler):
  def __init__(self, logbooks = None, tags = None):
    logging.Handler.__init__(self)
    self.session = SimpleOlogClient()
    self.logbooks = logbooks
    self.tags = tags
  def emit(self, record):
    # ToDo add log level to olog
    try:
      msg = self.format(record)
      self.session.log(msg,
                       logbooks = self.logbooks, 
                       tags = self.tags)
    except:
      self.handleError(record)
