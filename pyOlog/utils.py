import os
import subprocess
import tempfile

from OlogDataTypes import Attachment

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

def get_text_from_editor():
  """Open text editor and return text"""
  with tempfile.NamedTemporaryFile(suffix='.tmp') as f:
    editor = os.environ.get('EDITOR', 'vim')
    subprocess.call([editor, f.name])
    text = f.read()
  return text
