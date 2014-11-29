from OlogDataTypes import Attachment
import subprocess

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
