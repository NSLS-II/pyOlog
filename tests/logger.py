import logging
from pyOlog.ologhandler import OlogHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

olog = OlogHandler()
olog.setLevel(logging.DEBUG)

logger.addHandler(olog)

def main():
  logger.debug('Debug message')
  logger.info('Info Message')
  logger.warn('Warn Message')
  logger.error('Error Message')
  logger.critical('Critical Message')

if __name__ == "__main__":
  main()
