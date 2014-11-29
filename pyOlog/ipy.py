from IPython.core.magic import (register_line_magic, register_cell_magic,
                                register_line_cell_magic, Magics, magics_class,
                                line_magic, cell_magic)

from IPython.utils.io import capture_output
from IPython.display import display

from pyOlog import SimpleOlogClient

olog_client = SimpleOlogClient()

@register_line_magic
def logit(line):
  olog_client.log()

@register_line_magic
def grabit(line):
  olog_client.screenshot()

@magics_class
class OlogMagics(Magics):
  @line_magic
  def logcell(self, line):
    with capture_output() as c:
      self.shell.run_cell(line)
    c.show()
    msg = "STDOUT\n======\n\n" + c.stdout + "\n\nSTDERR\n======\n\n" + c.stderr
    olog_client.log(msg)

def load_ipython_extension(ipython):
  push_vars = {'olog'         : olog_client.log,
               'olog_savefig' : olog_client.savefig,
               'olog_grab'    : olog_client.screenshot}
  ipython.push(push_vars) 
  ipython.register_magics(OlogMagics)
del logit, grabit
