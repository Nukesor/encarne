#!/bin/env python3
import sys
import shutil

from encarne.argument_parser import parser
from encarne.communication import get_status
from encarne.encoder import Encoder


def main():
    args = parser.parse_args()

    # Check if mediainfo is available
    mediainfo_exists = shutil.which('mediainfo')
    if not mediainfo_exists:
        print("Mediainfo needs to be installed on this system.")
        sys.exit(1)

    # Check if pueue is available:
    get_status()

    try:
        encoder = Encoder(vars(args))
        encoder.run()
    except KeyboardInterrupt:
        print('Keyboard interrupt. Shutting down')
        sys.exit(0)
