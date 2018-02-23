"""Argument parsing."""
import argparse
from encarne.stats import show_stats


# Specifying commands
parser = argparse.ArgumentParser(
    description='Encarne reencoder')
parser.add_argument(
    '-d', '--directory', type=str,
    help='Directory that should be explored for video container to be encoded.')

parser.add_argument(
    '-s', '--size', type=str,
    help='Specify minimun encoding file size (11GB, 100MB, ...).')

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

audio_values = ['aac', 'flac', 'None']
parser.add_argument(
    '-a', '--audio', type=str, choices=audio_values,
    help='Audio encoding for ffmpeg.')

parser.add_argument(
    '-ba', '--kbitrate-audio', type=str,
    help='Audio encoding bitrate (e.g. 128k or not specified for flac).')

parser.add_argument(
    '-t', '--threads', type=int,
    help='The threads used for encoding.')


# Initialize supbparser
subparsers = parser.add_subparsers(
    title='Subcommands', description='Various client')


# Status
stat_subcommand = subparsers.add_parser(
    'stat', help='Show some statistics.',
)
stat_subcommand.set_defaults(func=show_stats)
