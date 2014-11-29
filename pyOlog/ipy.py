from IPython.core.magic import (register_line_magic, register_cell_magic,
                                register_line_cell_magic)

from pyOlog.api import SimpleOlogClient


olog_client = SimpleOlogClient()

@register_line_magic
def logit(line):
  olog_client.log()

def load_ipython_extension(ipython):
  push_vars = {'olog'         : olog_client.log,
               'olog_savefig' : olog_client.savefig,
               'olog_grab'    : olog_client.screenshot}
  ipython.push(push_vars) 

del logit
