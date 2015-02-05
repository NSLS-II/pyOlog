import logging
import sys
logger = logging.getLogger("pyOlog")
logger.setLevel(logging.CRITICAL)

handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.CRITICAL)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

from .OlogDataTypes import LogEntry, Logbook, Tag, Property, Attachment
from .OlogClient import OlogClient
from .SimpleOlogClient import SimpleOlogClient
