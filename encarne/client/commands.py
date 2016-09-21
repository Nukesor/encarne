import os
import sys
import math
import time
import glob
import shlex
import shutil
import subprocess

from lxml import etree
from datetime import datetime, timedelta

from encarne.helper.config import read_config
from encarne.client.communication import (
    execute_add,
    get_status,
)


def execute_run(args):
    config = read_config()

    args = {key: value for key, value in args.items() if value}
    for key, value in args.items():
        if key == 'directory':
            config['default']['directory'] = value
        # Encoding
        if key == 'crf':
            config['encoding']['crf'] = str(value)
        elif key == 'preset':
            config['encoding']['preset'] = value
        elif key == 'audio':
            config['encoding']['audio'] = value
        elif key == 'audio':
            config['encoding']['kbitrate-audio'] = value

    if not config['default']['directory'] or \
       not os.path.isdir(config['default']['directory']):
        print('A valid directory needs to be specified')
        print(config['default']['directory'])
        sys.exit(1)
    else:
        # Get absolute path of directory
        config['default']['directory'] = os.path.abspath(config['default']['directory'])

    files = find_files(config['default']['directory'])

    processed_files = 0
    for path in files:
        # Get absolute path
        path = os.path.abspath(path)
        # Create media info and get `Writing library` value.
        mediainfo = get_media_encoding(path)
        if 'x265' in mediainfo:
            continue
        processed_files += 1

        # Get directory the movie is in and the name for the temporary
        # new encoded video file.
        directory_path = os.path.dirname(path)
        dest_path = os.path.join(directory_path, 'encarne_temp.mkv')

        # Compile ffmpeg command
        ffmpeg_command = create_ffmpeg_command(config, path, dest_path)

        # Check if the current command already in the queue.
        index, status = get_current_index(ffmpeg_command)

        # Send the command to pueue for scheduling, if it isn't in the queue yet
        if index is None and status is None:
            # In case a previous run failed and pueue has been resetted,
            # we need to check, if the encoded file is still there.
            if os.path.exists(dest_path):
                os.remove(dest_path)
            args = {
                'command': ffmpeg_command,
                'path': directory_path
            }
            print("Add task for '''{}''' to pueue".format(path))
            execute_add(args)
        else:
            print("Task '''{}''' already exists in pueue.".format(path))

        waiting = True
        while waiting:
            # Get index of current command and the current status
            index, status = get_current_index(ffmpeg_command)
            # If the command has been removed or errored,
            # remove the already created destination file
            if (index is None and status is None) or status == 'errored':
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                waiting = False
            # If the command has finished, break the loop for further processing
            elif status == 'done':
                waiting = False

            time.sleep(60)

        if os.path.exists(dest_path):
            print("Pueue task completed")
            copy = True
            # If the destination movie is shorter than a maximum of 20 seconds
            # as the original or has no duration property in mediafile, we drop this.
            origin_duration = get_media_duration(path)
            dest_duration = get_media_duration(dest_path)
            if dest_duration is not None:
                diff = origin_duration - dest_duration
                THRESHOLD = 20
                if math.fabs(diff.total_seconds()) < THRESHOLD:
                    print('Encoded movie is more than {} seconds shorter than original'.format(THRESHOLD))
                    copy = False

            # Check if the filesize of the x.265 encoded object is bigger
            # than the original.
            if copy:
                origin_filesize = os.path.getsize(path)
                dest_filesize = os.path.getsize(dest_path)
                if origin_filesize < dest_filesize:
                    print('Encoded movie is bigger than the original movie')
                    copy = False

            # Only copy if checks above passed
            if copy:
                shutil.move(dest_path, path)
                print("New encoded file is now in place")
            else:
                print("Didn't copy new file, see message above")
        else:
            print("Pueue task failed in some kind of way.")

    if processed_files == 0:
        print('No files for encoding found')


def find_files(path):
    """Get all known video files by recursive extension search."""
    mkv = glob.glob(os.path.join(path, '*.mkv'))
    mp4 = glob.glob(os.path.join(path, '*.mp4'))

    movie_files = mkv + mp4
    return movie_files


def create_ffmpeg_command(config, path, dest_path):
    """Compile an ffmpeg command by known parameters."""
    if config['encoding']['kbitrate-audio'] != 'None':
        audio_bitrate = '-b:a {}'.format('audio_bitrate')
    else:
        audio_bitrate = ''
    ffmpeg_command = 'ffmpeg -i {path} -c:v libx265 -preset {preset} ' \
        '-crf {crf} -c:a {audio} {bitrate} {dest}'.format(
            path=shlex.quote(path),
            dest=shlex.quote(dest_path),
            preset=config['encoding']['preset'],
            crf=config['encoding']['crf'],
            audio=config['encoding']['audio'],
            bitrate=audio_bitrate,
        )
    return ffmpeg_command


def get_media_encoding(path):
    """Execute external mediainfo command and find the video encoding library."""
    process = subprocess.run(
        ['mediainfo', '--Output=XML', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    root = etree.XML(process.stdout)
    writing_library = root.findall('.//track[@type="Video"]/Writing_library')[0].text

    return writing_library


def get_media_duration(path):
    """Execute external mediainfo command and find the video encoding library."""
    process = subprocess.run(
        ['mediainfo', '--Output=XML', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    root = etree.XML(process.stdout)
    try:
        time = root.findall('.//track[@type="General"]/Duration')[0].text
    except IndexError:
        # No duration, we return None
        return None

    date = datetime.strptime("1 h 10 min", "%H h %M min")
    delta = timedelta(hours=date.hour, minutes=date.minute)

    return delta


def get_current_index(command):
    """Get the status and key of the given process in pueue."""
    status = get_status()

    if isinstance(status['data'], dict):
        # Get the status of the latest submitted job.
        smallest_key = None
        for key, value in status['data'].items():
            if value['command'] == command:
                if smallest_key is None or smallest_key < key:
                    smallest_key = key
        if smallest_key is not None:
            return smallest_key, status['data'][key]['status']
    return None, None
