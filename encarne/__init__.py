#!/bin/env python3
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

    if hasattr(args, 'func'):
        args.func(vars(args))
    else:
        print('Invalid Command. Please check -h')
