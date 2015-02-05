#!/usr/bin/python
from __future__ import print_function

import sys

import argparse

from .. import Attachment
from .. import SimpleOlogClient
from .utils import get_screenshot, get_text_from_editor

description = """\
Command line utility for making OLog entries.

Example:
  %(prog)s -l Operations -t Data -u swilkins -a ./image.png

This makes a log entry into the 'Operations' log tagged with the
tag 'Data' from the account of 'swilkins' with an image 'image.png
attached to the log entry. The log text is taken from stdin and can
either be entered on the command line or piped in. Alternatively a
text file can be specified with the '--file' option.

Multiple Tags and Logbooks can be specified after the option on the
command line separated by spaces. For example:

  %(prog)s -t "RF Area" "Bumps"

Wil add the tags 'RF Area' and 'Bumps'

Note : A password is requested on the command line unless the option
'-p' is supplied with a valid password, the password is in the config
file or it can be obtained from the keyring.

Optionally commands will take default from a config file located
in the users home directory ~/.pyOlog.conf This can contain the base
url for the Olog and also the default logbook to use. Administrators
can use the /etc/pyOlog.conf file to specify system wide config.


"""


def olog():
    """Command line utility for making Olog entries"""

    # Parse Command Line Options

    fclass = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(epilog=description, formatter_class=fclass)
    parser.add_argument('-l', '--logbooks', dest='logbooks',
                        help="Logbook Name(s)", nargs='*',
                        default=None)
    parser.add_argument('-t', '--tags', dest='tags',
                        nargs='*', help="OLog Tag Name(s)",
                        default=None)
    parser.add_argument('-u', '--user', dest='username',
                        default=None,
                        help="Username for Olog Access")
    parser.add_argument('-f', '--file', dest='text',
                        type=argparse.FileType('r'),
                        default=None,
                        help="Filename of log entry text.")
    parser.add_argument('--url', dest='url',
                        help="Base URL for Olog Access",
                        default=None)
    parser.add_argument('-a', '--attach', dest='attach',
                        nargs='*',
                        help="filename of attachments")
    parser.add_argument('-p', '--passwd', dest='passwd',
                        help="Password for logging entry",
                        default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-s', '--screenshot', dest='screenshot',
                       help='Take screenshot of whole screen',
                       default=False,
                       action='store_true')
    group.add_argument('-g', '--grap', dest='grab',
                       help='Grab area of screen and add as attatchment.',
                       default=False,
                       action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', action='store_true', dest='verbose',
                       help="Verbose output", default=False)
    group.add_argument('-q', action='store_true', dest='quiet',
                       help="Suppress all output", default=False)

    args = parser.parse_args()

    if args.attach is not None:
        attachments = [Attachment(open(a)) for a in args.attach.split(',')]
    else:
        attachments = []

    # Grab Screenshot

    if args.screenshot or args.grab:
        if not args.quiet and args.grab:
            print("Select area of screen to add to log entry.",
                  file=sys.stderr)
        screenshot = get_screenshot(args.screenshot)
        attachments.append(screenshot)

    # First create the log entry

    if args.text is None:
        text = get_text_from_editor()
    else:
        text = args.text

    c = SimpleOlogClient(args.url, args.username, args.passwd)
    c.log(text, logbooks=args.logbooks, tags=args.tags,
          attachments=attachments)


def main():
    try:
        olog()
    except KeyboardInterrupt:
        print('\nAborted.\n')
        sys.exit()

if __name__ == '__main__':

    main()
