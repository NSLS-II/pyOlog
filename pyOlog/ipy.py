from pyOlog.api import SimpleOlogClient

olog_client = SimpleOlogClient()

def load_ipython_extension(ipython):
  push_vars = {'olog'         : olog_client.log,
               'savefig_olog' : olog_client.savefig}
  ipython.push(push_vars) 
