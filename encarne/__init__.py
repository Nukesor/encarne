#!/bin/env python3
"""Main file. Encarne entry point."""
import os
import sys
import shutil

from pueue.client.factories import command_factory

from encarne.argument_parser import parser
from encarne.encoder import Encoder


def main():
    """Parse args, check if everything is ok and start encarne."""
    args = parser.parse_args()

    # Check if mediainfo is available
    mediainfo_exists = shutil.which('mediainfo')
    if not mediainfo_exists:
        print("Mediainfo needs to be installed on this system.")
        sys.exit(1)

    # Check if pueue is available:
    command_factory('status')({}, root_dir=os.path.expanduser('~'))

    try:
        if hasattr(args, 'func'):
            args.func(vars(args))
        else:
            encoder = Encoder(vars(args))
            encoder.run()

    except KeyboardInterrupt:
        print('Keyboard interrupt. Shutting down')
        sys.exit(0)
