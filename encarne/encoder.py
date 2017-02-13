import os
import sys
import math
import time
import glob
import shlex
import logging
import configparser

from logging.handlers import RotatingFileHandler

from encarne.media import get_media_encoding, get_media_duration
from encarne.communication import (
    add,
    get_status,
)


class Encoder():
    def __init__(self, args):
        # Set up all directories needed by encarne
        self.initialize_directories()
        self.initialize_logging()
        self.read_config()
        self.format_args(args)

        # Various variables
        self.processed_files = 0

    def initialize_directories(self):
        """Helper functions for creating a needed dir."""
        # Create logging directory and get log file path
        home = os.path.expanduser('~')
        log_dir = os.path.join(home, '.local/share/encarne')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        timestamp = time.strftime('-%Y%m%d-%H%M-')
        self.log_file = os.path.join(log_dir, 'encarne{}.log'.format(timestamp))

        # Create config directory
        config_dir = os.path.join(home, '.config/encarne')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        self.config_file = os.path.join(config_dir, 'encarne.ini')

    def initialize_logging(self):
        self.logger = logging.getLogger('')
        self.logger.setLevel(logging.DEBUG)
        format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        channel_handler = logging.StreamHandler(sys.stdout)
        channel_handler.setFormatter(format)
        self.logger.addHandler(channel_handler)

        file_handler = RotatingFileHandler(self.log_file, maxBytes=(1048576*100), backupCount=7)
        file_handler.setFormatter(format)
        self.logger.addHandler(file_handler)

    def read_config(self):
        """Get the config file and create it with default values, if it doesn't exist."""
        self.config = configparser.ConfigParser()

        # Try to get config, if this doesn't work a new default config will be created
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
                return
            except:
                self.logger.info('Error while parsing config file. Deleting old config')

        # Default configuration
        self.config['encoding'] = {
            'crf': '18',
            'preset': 'slow',
            'audio': 'flac',
            'kbitrate-audio': 'None',
            'threads': '0'
        }

        self.write_config()

    def write_config(self):
        """Write the config file."""
        if os.path.exists(self.config_file):
            os.path.remove(self.config_file)

        with open(self.config_file, 'w') as file_descriptor:
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
            self.logger.warning('A valid directory needs to be specified')
            self.logger.warning(self.directory)
            sys.exit(1)

        # Get absolute path of directory
        self.directory = os.path.abspath(self.directory)

    def run(self):
        """Check the specified directory for movies to be encoded."""

        files = self.find_files()

        if len(files) == 0:
            self.logger.info('No files for encoding found.')
            sys.exit(1)

        for path in files:

            # Get directory the movie is in and the name for new encoded video file.
            dest_folder = os.path.dirname(path)
            # Change filename to contain 'x265'.
            # Replace it if there is a 'x264' in the filename.
            dest_file = os.path.basename(path)
            home = os.path.expanduser('~')
            if 'x264' in dest_file:
                dest_file = dest_file.replace('x264', 'x265')
                temp_path = os.path.join(home, dest_file)
                temp_path = os.path.splitext(temp_path)[0] + '.mkv'
            # Add a `-x265.mkv` if there is nothing to replace
            else:
                temp_path = os.path.join(home, dest_file)
                temp_path = os.path.splitext(temp_path)[0] + '-x265.mkv'
            dest_file = os.path.basename(temp_path)
            dest_path = os.path.join(dest_folder, dest_file)

            # Compile ffmpeg command
            ffmpeg_command = self.create_ffmpeg_command(path, temp_path)

            # Check if the current command already in the queue.
            index, status = self.get_current_index(ffmpeg_command)

            # Send the command to pueue for scheduling, if it isn't in the queue yet
            if index is None and status is None:
                # In case a previous run failed and pueue has been resetted,
                # we need to check, if the encoded file is still there.
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                args = {
                    'command': ffmpeg_command,
                    'path': dest_folder
                }
                self.logger.info("Add task pueue:\n {}".format(ffmpeg_command))
                add(args)
            else:
                self.logger.info("Task already exists in pueue: \n{}".format(ffmpeg_command))

            waiting = True
            while waiting:
                # Get index of current command and the current status
                index, status = self.get_current_index(ffmpeg_command)
                # If the command has been removed or errored,
                # remove the already created destination file
                if (index is None and status is None) or status == 'errored':
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    waiting = False
                # If the command has finished, break the loop for further processing
                elif status == 'done':
                    waiting = False

                time.sleep(60)

            if os.path.exists(temp_path):
                self.logger.info("Pueue task completed")
                copy = True
                # If the destination movie is shorter than a maximum of 1 seconds
                # as the original or has no duration property in mediafmkvile, we drop this.
                origin_duration = get_media_duration(path)
                duration = get_media_duration(temp_path)
                if duration is not None:
                    diff = origin_duration - duration
                    THRESHOLD = 2
                    if math.fabs(diff.total_seconds()) > THRESHOLD:
                        self.logger.warning('Encoded movie is more than {} shorter/longer than original.'.format(THRESHOLD))
                        copy = False
                else:
                    self.logger.error("No known time format: {}".format(time))

                # Check if the filesize of the x.265 encoded object is bigger
                # than the original.
                if copy:
                    origin_filesize = os.path.getsize(path)
                    filesize = os.path.getsize(temp_path)
                    if origin_filesize < filesize:
                        self.logger.warning('Encoded movie is bigger than the original movie')
                        copy = False
                    else:
                        difference = origin_filesize - filesize
                        mebibyte = int(difference/1024/1024)
                        self.logger.info('The new movie is {} MIB smaller than the old one'.format(mebibyte))

                # Only copy if checks above passed
                if copy:
                    os.remove(path)
                    os.rename(temp_path, dest_path)
                    self.processed_files += 1
                    self.logger.info("New encoded file is now in place")
                else:
                    # Remove the encoded file and mark the old one as failed.
                    failed_path = '{}-encarne-failed{}'.format(
                        os.path.splitext(path)[0],
                        os.path.splitext(path)[1]
                    )
                    os.rename(path, failed_path)
                    os.remove(temp_path)
                    self.logger.warning("Didn't copy new file, see message above")
            else:
                self.logger.error("Pueue task failed in some kind of way.")

        self.logger.info('{} movies successfully encoded. Exiting'.format(self.processed_files))

    def find_files(self):
        """Get all known video files by recursive extension search."""
        extensions = ['mkv', 'mp4', 'avi']
        files = []
        for extension in extensions:
            found = glob.glob(
                os.path.join(self.directory, '**/*.{}'.format(extension)),
                recursive=True)
            files = files + found

        files = self.filter_files(files)
        return files

    def filter_files(self, files):
        """Filter files and check if they are already done or failed in a previous run."""

        filtered_files = []
        for path in files:
            # Get absolute path
            path = os.path.abspath(path)
            # Create media info and get `Writing library` value.
            mediainfo = get_media_encoding(path)
            if 'x265' in mediainfo:
                continue
            # In case we reencoded it and it failed, we ignore this file
            if 'encarne-failed' in path:
                continue
            filtered_files.append(path)

        return filtered_files

    def create_ffmpeg_command(self, path, dest_path):
        """Compile an ffmpeg command by known parameters."""
        if self.config['encoding']['kbitrate-audio'] != 'None':
            audio_bitrate = '-b:a {}'.format('audio_bitrate')
        else:
            audio_bitrate = ''
        ffmpeg_command = 'ffmpeg -i {path} -c:v libx265 -preset {preset} ' \
            '-x265-params crf={crf}:pools=none -threads {threads} -c:a {audio} {bitrate} {dest}'.format(
                path=shlex.quote(path),
                dest=shlex.quote(dest_path),
                preset=self.config['encoding']['preset'],
                crf=self.config['encoding']['crf'],
                threads=self.config['encoding']['threads'],
                audio=self.config['encoding']['audio'],
                bitrate=audio_bitrate,
            )
        return ffmpeg_command

    def get_current_index(command):
        """Get the status and key of the given process in pueue."""
        status = get_status()

        if isinstance(status['data'], dict):
            # Get the status of the latest submitted job.
            highest_key = None
            for key, value in status['data'].items():
                if value['command'] == command:
                    if highest_key is None or highest_key < key:
                        highest_key = key
            if highest_key is not None:
                return highest_key, status['data'][highest_key]['status']
        return None, None
