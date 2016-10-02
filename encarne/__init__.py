#!/bin/env python3
import sys
import shutil
import argparse

from encarne.client.commands import execute_run
from encarne.client.communication import get_status


def main():
    # Specifying commands
    parser = argparse.ArgumentParser(
        description='Encarne reencoder')
    parser.add_argument(
        'directory', type=str,
        help='Directory that should be explored for video container to be encoded.')

    # Encoding stuff
    parser.add_argument(
        '-c', '--crf', type=int, choices=range(0, 51),
        help='Constant rate factor for ffmpeg.')

    preset_values = ['ultrafast', 'superfast', 'veryfast',
                     'faster', 'fast', 'medium', 'slow', 'slower',
                     'veryslow', 'placebo']
    parser.add_argument(
        '-p', '--preset', type=str, choices=preset_values,
        help='Compression preset for ffmpeg.')

    audio_values = ['aac', 'flac']
    parser.add_argument(
        '-a', '--audio', type=str, choices=audio_values,
        help='Audio encoding for ffmpeg.')

    parser.add_argument(
        '-ba', '--kbitrate-audio', type=str,
        help='Audio encoding bitrate (e.g. 128k or not specified for flac).')

    parser.add_argument(
        '-t', '--threads', type=int,
        help='The threads used for encoding.')

    parser.set_defaults(func=execute_run)
    args = parser.parse_args()

    # Check if mediainfo is available
    mediainfo_exists = shutil.which('mediainfo')
    if not mediainfo_exists:
        print("Mediainfo needs to be installed on this system.")
        sys.exit(1)

    # Check if pueue is available:
    get_status()

    if hasattr(args, 'func'):
        try:
            args.func(vars(args))
        except KeyboardInterrupt:
            print('Keyboard interrupt. Shutting down')
            sys.exit(0)
    else:
        print('Invalid Command. Please check -h')
