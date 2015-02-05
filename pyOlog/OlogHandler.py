import logging
from SimpleOlogClient import SimpleOlogClient


class OlogHandler(logging.Handler):

    def __init__(self, logbooks=None, tags=None):
        """Initialize the ologhandler

        :param logbooks: list of strings of logbooks to add messages to
        :param tags: list of strings of tags to add to all messages
        """
        super(OlogHandler, self).__init__()
        self.session = SimpleOlogClient()
        self.logbooks = logbooks
        self.tags = tags

    def emit(self, record):
        try:
            msg = self.format(record)
            self.session.log(msg,
                             logbooks=self.logbooks,
                             tags=self.tags)
        except:
            self.handleError(record)
