#!/bin/env python3
import sys
import shutil
import argparse

from encarne.client.commands import execute_run
from encarne.helper.validators import (
    check_audio,
    check_crf,
    check_preset,
)


def main():
    # Specifying commands
    parser = argparse.ArgumentParser(
        description='Encarne reencoder')
    parser.add_argument(
        '-d', '--dir', type=str,
        help='Directory that should be explored for video container to be encoded.')

    # Encoding stuff
    parser.add_argument(
        '-c', '--crf', type=check_crf,
        help='Constant rate factor for ffmpeg.')

    parser.add_argument(
        '-p', '--preset', type=check_preset,
        help='Compression preset for ffmpeg.')

    parser.add_argument(
        '-a', '--audio', type=check_audio,
        help='Audio encoding for ffmpeg.')

    parser.add_argument(
        '-ba', '--kbitrate-audio', type=str,
        help='Audio encoding bitrate (e.g. 128k or not specified for flac).')

    parser.set_defaults(func=execute_run)
    args = parser.parse_args()

    # Check if mediainfo is available
    mediainfo_exists = shutil.which('mediainfo')
    if not mediainfo_exists:
        print("Mediainfo needs to be installed on this system.")
        sys.exit(1)

    if hasattr(args, 'func'):
        try:
            args.func(vars(args))
        except KeyboardInterrupt:
            print('Keyboard interrupt. Shutting down')
            sys.exit(0)
    else:
        print('Invalid Command. Please check -h')
