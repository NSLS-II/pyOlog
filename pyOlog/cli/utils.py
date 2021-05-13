import os
import subprocess
import tempfile

from .. import Attachment

text_message = '''
#
# Please enter the log message using the editor. Lines beginning
# with '#' will be ignored, and an empty message aborts the log
# message from being logged.
#
'''


def save_pyplot_figure(**kwargs):
    """Save a matplotlib figure to an Olog Attachment Object"""
    import matplotlib.pyplot as plt
    import StringIO

    imgdata = StringIO.StringIO()
    plt.savefig(imgdata, format='pdf', **kwargs)
    imgdata.seek(0)

    a = [Attachment(imgdata, 'plot.pdf')]

    imgdata = StringIO.StringIO()
    plt.savefig(imgdata, format='png', dpi=50,
                **kwargs)
    imgdata.seek(0)

    a.append(Attachment(imgdata, 'thumbnail.png'))

    return a


def _get_screenshot(root=False, itype='png'):
    """Open ImageMagick and get screngrab as png."""
    if root:
        opts = '-window root'
    else:
        opts = ''
    image = subprocess.Popen('import {0} {1}:-'.format(opts, itype),
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    stdout, stderr = image.communicate()
    if stderr:
        raise RuntimeError(f"Cannot capture a screenshot. "
                           f"Reason: {stderr.decode()}")
    return stdout


def get_screenshot(root=False, itype='png'):
    img = _get_screenshot(root=root, itype=itype)
    return Attachment(img, 'screenshot.' + itype)


def get_text_from_editor(prepend=None, postpend=None):
    """Open text editor and return text"""
    with tempfile.NamedTemporaryFile(suffix='.tmp', mode='w+t') as f:
        # Write out the file and flush

        message = ''

        if prepend:
            message += '\n\n'
            message += prepend
            message += '\n'

        message += text_message

        if postpend:
            message += postpend
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
        text = '\n'.join(lines)
    return text


def get_pyplot_fig(self, *args, **kwargs):
    """Save a matplotlib figure as an Attachment"""
    import matplotlib.pyplot as plt
    import StringIO

    imgdata = StringIO.StringIO()
    plt.savefig(imgdata, format='png', **kwargs)
    imgdata.seek(0)

    a = Attachment(imgdata, 'plot.png')

    return a
