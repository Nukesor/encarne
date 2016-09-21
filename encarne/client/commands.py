import os
import sys
import time
import glob
import shutil
import subprocess
from lxml import etree

from encarne.helper.config import read_config
from encarne.client.communication import (
    execute_add,
    get_status,
)


def execute_run(args):
    config = read_config()

    args = {key: value for key, value in args.items() if value}
    for key, value in args.items():
        if key == 'dir':
            config['default']['directory'] = value
        # Encoding
        if key == 'crf':
            config['encoding']['crf'] = value
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

    for path in files:
        # Get absolute path
        path = os.path.abspath(path)
        # Create media info and get `Writing library` value.
        mediainfo = get_media_info(path)
        if 'x265' in mediainfo:
            continue

        # Get directory the movie is in and the name for the temporary
        # new encoded video file.
        directory_path = os.path.dirname(path)
        dest_path = os.path.join(directory_path, 'encarne_temp.mkv')

        # Compile ffmpeg command and send it to pueue for scheduling
        ffmpeg_command = create_ffmpeg_command(config, path, dest_path)
        args = {
            'command': ffmpeg_command,
            'path': directory_path
        }
        execute_add(args)

        waiting = True
        while waiting:
            # Get index of current command and the current status
            index, status = get_current_index(ffmpeg_command)
            # If the command has been removed or errored,
            # remove the already created destination file
            if (index is None and status is None) or status == 'errored':
                if os.path.exists(dest_path):
                    os.path.remove(dest_path)
                waiting = False
            # If the command has finished, break the loop for further processing
            elif status == 'done':
                waiting = False

            time.sleep(60)

        if os.path.exists(dest_path):
            shutil.move(dest_path, path)


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
            path=path,
            dest=dest_path,
            preset=config['encoding']['preset'],
            crf=config['encoding']['crf'],
            audio=config['encoding']['audio'],
            bitrate=audio_bitrate,
        )
    return ffmpeg_command


def get_media_info(path):
    """Execute external mediainfo command and find the video encoding library."""
    process = subprocess.run(
        ['mediainfo', '--Output=XML', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    root = etree.XML(process.stdout)
    writing_library = root.findall('.//track[@type="Video"]/Writing_library')[0].text

    return writing_library


def get_current_index(command):
    """Get the status and key of the given process in pueue."""
    status = get_status()

    for key, value in status['data'].items():
        if value['command'] == command:
            return key, value['status']
    return None, None
