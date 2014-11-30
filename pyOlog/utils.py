import os
import subprocess
import tempfile

from OlogDataTypes import Attachment

text_message = '''
#
# Please enter the log message using the editor. Lines beginning
# with '#' will be ignored, and an empty message aborts the log
# message from being logged.
#
'''

def get_screenshot(root = False, itype = 'png'):
  """Open ImageMagick and get screngrab as png."""
  if root:
    opts = '-window root'
  else:
    opts = ''
  image = subprocess.Popen('import {0} {1}:-'.format(opts,itype),
                           shell = True, 
                           stdout = subprocess.PIPE)
  img = image.communicate()[0]

  return Attachment(img, 'screenshot.' + itype)

def get_text_from_editor(additional_text = None):
  """Open text editor and return text"""
  with tempfile.NamedTemporaryFile(suffix='.tmp') as f:
    # Write out the file and flush
    message = text_message
    if not additional_text: 
      message += ''
    else:
      message += additional_text
    f.write(message)
    f.flush()

    # Now open editor to edit file
    editor = os.environ.get('EDITOR', 'vim')
    subprocess.call([editor, f.name])

    # Read file back in
    f.seek(0)
    text = f.read()

    # Strip off any lines that start with whitespace and a '#'
    lines = [n for n in text.splitlines() if not n.lstrip().startswith('#')]
    text = ''.join(lines)
  return text

def get_pyplot_fig(self, *args, **kwargs):
  """Save a matplotlib figure as an Attachment"""
  import matplotlib.pyplot as plt
  import StringIO

  imgdata = StringIO.StringIO()
  plt.savefig(imgdata, format = 'png', **kwargs)
  imgdata.seek(0)

  a = Attachment(imgdata, 'plot.png')

  return a

