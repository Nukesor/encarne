"""Encoding."""
import os
import sys
import time
import glob
import shlex
import configparser

from pueue.client.manipulation import execute_add
from pueue.client.factories import command_factory

from encarne.logger import Logger
from encarne.media import (
    check_file_size,
    check_duration,
    get_media_encoding,
)


class Encoder():
    """Encoder class."""

    def __init__(self, args):
        """Create a new encoder."""
        self.initialize_directories()
        self.read_config()
        self.format_args(args)

        self.origin_path = None
        self.temp_path = None
        self.target_path = None
        self.ffmpeg_command = None

        # Various variables
        self.processed_files = 0

    def initialize_directories(self):
        """Create needed directories."""
        home = os.path.expanduser('~')
        log_dir = os.path.join(home, '.local/share/encarne')
        config_dir = os.path.join(home, '.config/encarne')

        # Create log dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create config directory
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        self.config_path = os.path.join(config_dir, 'encarne.ini')

    def read_config(self):
        """Get the config file or create it with default values."""
        self.config = configparser.ConfigParser()

        # Try to get config, if this doesn't work a new default config will be created
        if os.path.exists(self.config_path):
            try:
                self.config.read(self.config_path)
                return
            except BaseException:
                Logger.info('Error while parsing config file. Deleting old config')

        # Default configuration
        self.config['encoding'] = {
            'crf': '18',
            'preset': 'slow',
            'audio': 'None',
            'kbitrate-audio': 'None',
            'threads': '0',
        }

        self.config['default'] = {
            'min-size': '{0}'.format(1024*1024*1024*6),
        }

        self.write_config()

    def write_config(self):
        """Write the config file."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        with open(self.config_path, 'w') as file_descriptor:
            self.config.write(file_descriptor)

    def format_args(self, args):
        """Check arguments and format them to be compatible with `self.config`."""
        args = {key: value for key, value in args.items() if value}
        for key, value in args.items():
            if key == 'directory':
                self.directory = value
            # Encoding
            if key == 'crf':
                self.config['encoding']['crf'] = str(value)
            elif key == 'preset':
                self.config['encoding']['preset'] = value
            elif key == 'audio':
                self.config['encoding']['audio'] = value
            elif key == 'audio':
                self.config['encoding']['kbitrate-audio'] = value
            elif key == 'threads':
                self.config['encoding']['threads'] = str(value)

        if not self.directory or not os.path.isdir(self.directory):
            Logger.warning('A valid directory needs to be specified')
            Logger.warning(self.directory)
            sys.exit(1)

        # Get absolute path of directory
        self.directory = os.path.abspath(self.directory)

    def run(self):
        """Get all known video files by recursive extension search."""
        extensions = ['mkv', 'mp4', 'avi']
        files = []
        for extension in extensions:
            found = glob.glob(
                os.path.join(self.directory, f'**/*.{extension}'),
                recursive=True)
            files = files + found

        files = self.filter_files(files)

        if len(files) == 0:
            Logger.info('No files for encoding found.')
            sys.exit(0)
        else:
            Logger.info(f'{len(files)} files found.')

        for path in files:
            self.origin_path = path
            self.add_to_peue()
            self.wait_for_task()
            self.validate_encoded_file()

        Logger.info(f'Successfully encoded {self.processed_files} movies. Exiting')

    def add_to_peue(self):
        """Schedule and manage encoding of a movie.

        Get all files that should be encoded and process them:

        1. A ffmpeg command is created, which places the temporary file into ~/
        2. The command is added to pueue.
        3. Wait for the task to finish.
        4. Check if the encoding was successful.
        4.1 If it wasn't successful, we delete the encoded file and mark the
            old file as `encarne-failed`.
        4.2 Remove the old file and move the encoded file to the proper location.
        5. Repeat

        """
        # Get the directory which contains the movie and the name for
        # the new encoded video file.
        origin_folder = os.path.dirname(self.origin_path)
        origin_file = os.path.basename(self.origin_path)
        home = os.path.expanduser('~')

        # Change filename to contain 'x265'.
        # Replace it if there is a 'x264' in the filename.
        if 'x264' in origin_file:
            self.temp_path = os.path.join(home, origin_file.replace('x264', 'x265'))
            self.temp_path = os.path.splitext(self.temp_path)[0] + '.mkv'
        # Add a `-x265.mkv` if there is nothing to replace
        else:
            self.temp_path = os.path.join(home, origin_file)
            self.temp_path = os.path.splitext(self.temp_path)[0] + '-x265.mkv'

        self.target_path = os.path.join(origin_folder, os.path.basename(self.temp_path))

        # Compile ffmpeg command
        self.set_ffmpeg_command(self.origin_path, self.temp_path)

        # Check if the current command already in the queue.
        status = self.get_newest_status(self.ffmpeg_command)

        # Send the command to pueue for scheduling, if it isn't in the queue yet
        if status is None:
            # In case a previous run failed and pueue has been resetted,
            # we need to check, if the encoded file is still there.
            if os.path.exists(self.temp_path):
                os.remove(self.temp_path)

            # Create a new pueue task
            args = {
                'command': [self.ffmpeg_command],
                'path': origin_folder,
            }
            Logger.info(f'Add task pueue:\n {self.ffmpeg_command}')
            execute_add(args, os.path.expanduser('~'))
        else:
            Logger.info(f'Task already exists in pueue: \n{self.ffmpeg_command}')

    def wait_for_task(self):
        """Wait for the pueue task to finish."""
        # Wait for the task to finish
        waiting = True
        while waiting:
            # Get index of current command and the current status
            status = self.get_newest_status(self.ffmpeg_command)
            # If the command has been removed or failed,
            # remove the already created destination file.
            if status is None or status == 'failed':
                if os.path.exists(self.temp_path):
                    os.remove(self.temp_path)
                waiting = False
            # If the command has finished, stop the loop for further processing
            elif status == 'done':
                waiting = False
            else:
                time.sleep(60)

    def validate_encoded_file(self):
        """Validate that the encoded file is not malformed."""
        if os.path.exists(self.temp_path):
            Logger.info("Pueue task completed")
            # Check if the duration of both movies differs.
            copy, delete = check_duration(self.origin_path, self.temp_path, seconds=1)

            # Check if the filesize of the x.265 encoded object is bigger
            # than the original.
            if copy:
                copy, delete = check_file_size(self.origin_path, self.temp_path)

            # Only copy if checks above passed
            if copy:
                # Remove the old file and copy the new one to the proper directory.
                os.remove(self.origin_path)
                os.rename(self.temp_path, self.target_path)
                os.chmod(self.target_path, 0o644)
                self.processed_files += 1
                Logger.info("New encoded file is now in place")
            elif delete:
                # Remove the encoded file and mark the old one as failed.
                failed_path = '{0}-encarne-failed{1}'.format(
                    os.path.splitext(self.origin_path)[0],
                    os.path.splitext(self.origin_path)[1],
                )
                os.rename(self.origin_path, failed_path)
                os.remove(self.temp_path)
                Logger.warning("Didn't copy new file, see message above")
        else:
            Logger.error("Pueue task failed in some kind of way.")

    def filter_files(self, files):
        """Filter files and check if they are already done or failed in a previous run.

        A file will be filtered, if it already has x265 encoding or if there is
        `encarne-failed` in the name of the file. This happens if a previous encoding task
        failes in any way (encoded file is bigger/longer, ffmpeg failed).
        """
        filtered_files = []
        for path in files:
            # Get absolute path
            path = os.path.abspath(path)
            # In case we reencoded it and it failed, we ignore this file
            mediainfo = get_media_encoding(path)
            size = os.path.getsize(path)
            # Encoding failed in previous run
            if 'encarne-failed' in path:
                continue
            # Already encoded
            elif '265' in mediainfo or '265' in path:
                continue
            # File to small for encoding
            elif size < int(self.config['default']['min-size']):
                Logger.debug('File smaller than min-size: {path}')
                continue
            # Unknown encoding
            elif mediainfo == 'unknown':
                Logger.info(f'Failed to get encoding for {path}')

            filtered_files.append(path)

        return filtered_files

    def set_ffmpeg_command(self, path, dest_path):
        """Compile an ffmpeg command with parameters from config."""
        if self.config['encoding']['kbitrate-audio'] != 'None':
            audio_bitrate = f"-b:a {self.config['encoding']['kbitrate-audio']}"
        else:
            audio_bitrate = ''

        if self.config['encoding']['audio'] != 'None':
            audio_codec = f"-map 0:a -c:a {self.config['encoding']['audio']}"
        else:
            audio_codec = '-map 0:a'

        subtitles = ''

        self.ffmpeg_command = 'ffmpeg -i {path} -map 0:v -c:v libx265 -preset {preset} ' \
            '-x265-params crf={crf}:pools=none -threads {threads} {audio} {audio_bitrate} {subtitles} {dest}'.format(
                path=shlex.quote(path),
                dest=shlex.quote(dest_path),
                preset=self.config['encoding']['preset'],
                crf=self.config['encoding']['crf'],
                threads=self.config['encoding']['threads'],
                audio=audio_codec,
                subtitles=subtitles,
                audio_bitrate=audio_bitrate,
            )

    def get_newest_status(self, command):
        """Get the status and key of the given process in pueue."""
        status = command_factory('status')({}, root_dir=os.path.expanduser('~'))

        if isinstance(status['data'], dict):
            # Get the status of the latest submitted job, with this command.
            highest_key = None
            for key, value in status['data'].items():
                if value['command'] == command:
                    if highest_key is None or highest_key < key:
                        highest_key = key
            if highest_key is not None:
                return status['data'][highest_key]['status']
        return None
