import logging
from pyOlog.OlogHandler import OlogHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

olog = OlogHandler()
olog.setLevel(logging.DEBUG)
olog.setFormatter(formatter)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

logger.addHandler(olog)
logger.addHandler(ch)

def main():
  logger.debug('Debug message')
  logger.info('Info Message')
  logger.warn('Warn Message')
  logger.error('Error Message')
  logger.critical('Critical Message')

if __name__ == "__main__":
  main()
