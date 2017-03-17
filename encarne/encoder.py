import os
import sys
import time
import glob
import shlex
import logging
import configparser

from logging.handlers import RotatingFileHandler

from encarne.media import (
    check_file_size,
    check_duration,
    get_media_encoding,
)
from encarne.communication import (
    add_to_pueue,
    get_newest_status,
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

        self.config['default'] = {
            'min-size': '{}'.format(1024*1024*1024*6),
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
        """The heart of the encoder.

        At first, we get all files that should be encoded.
        Next we start to process all files:

        1. A ffmpeg command is created, which places the temporary file into ~/
        2. The command is added to pueue.
        3. Wait for the task to finish.
        4. Check if the encoding was successful.
        4.1 If it wasn't successful, we delete the encoded file and mark the
            old file as `encarne-failed`.
        4.2 Remove the old file and move the encoded file to the proper location.
        5. Repeat

        """

        files = self.find_files()

        if len(files) == 0:
            self.logger.info('No files for encoding found.')
            sys.exit(0)

        for origin_path in files:
            # Get the directory which contains the movie and the name for
            # the new encoded video file.
            origin_folder = os.path.dirname(origin_path)
            origin_file = os.path.basename(origin_path)
            home = os.path.expanduser('~')

            # Change filename to contain 'x265'.
            # Replace it if there is a 'x264' in the filename.
            if 'x264' in origin_file:
                temp_path = os.path.join(home, origin_file.replace('x264', 'x265'))
                temp_path = os.path.splitext(temp_path)[0] + '.mkv'
            # Add a `-x265.mkv` if there is nothing to replace
            else:
                temp_path = os.path.join(home, origin_file)
                temp_path = os.path.splitext(temp_path)[0] + '-x265.mkv'

            encoded_file = os.path.basename(temp_path)
            encoded_path = os.path.join(origin_folder, encoded_file)

            # Compile ffmpeg command
            ffmpeg_command = self.create_ffmpeg_command(origin_path, temp_path)

            # Check if the current command already in the queue.
            status = get_newest_status(ffmpeg_command)

            # Send the command to pueue for scheduling, if it isn't in the queue yet
            if status is None:
                # In case a previous run failed and pueue has been resetted,
                # we need to check, if the encoded file is still there.
                if os.path.exists(temp_path):
                    os.remove(temp_path)

                # Create a new pueue task
                args = {
                    'command': ffmpeg_command,
                    'path': origin_folder
                }
                self.logger.info("Add task pueue:\n {}".format(ffmpeg_command))
                add_to_pueue(args)
            else:
                self.logger.info("Task already exists in pueue: \n{}".format(ffmpeg_command))

            # Wait for the task to finish
            waiting = True
            while waiting:
                # Get index of current command and the current status
                status = get_newest_status(ffmpeg_command)
                # If the command has been removed or failed,
                # remove the already created destination file.
                if status is None or status == 'failed':
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    waiting = False
                # If the command has finished, stop the loop for further processing
                elif status == 'done':
                    waiting = False
                else:
                    time.sleep(60)

            if os.path.exists(temp_path):
                self.logger.info("Pueue task completed")
                copy = True

                # Check if the duration of both movies differs.
                copy, error = check_duration(origin_path, temp_path, seconds=1)
                if not copy:
                    self.logger.error(error)

                # Check if the filesize of the x.265 encoded object is bigger
                # than the original.
                if copy:
                    copy, message = check_file_size(origin_path, temp_path)
                    if not copy:
                        self.logger.error(message)
                    else:
                        self.logger.info(message)

                # Only copy if checks above passed
                if copy:
                    # Remove the old file and copy the new one to the proper directory.
                    os.remove(origin_path)
                    os.rename(temp_path, encoded_path)
                    os.chmod(encoded_path, 0o644)
                    self.processed_files += 1
                    self.logger.info("New encoded file is now in place")
                else:
                    # Remove the encoded file and mark the old one as failed.
                    failed_path = '{}-encarne-failed{}'.format(
                        os.path.splitext(origin_path)[0],
                        os.path.splitext(origin_path)[1]
                    )
                    os.rename(origin_path, failed_path)
                    os.remove(temp_path)
                    self.logger.warning("Didn't copy new file, see message above")
            else:
                self.logger.error("Pueue task failed in some kind of way.")

        self.logger.info('Successfully encoded {} movies. Exiting'.format(self.processed_files))

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
            elif 'x265' in mediainfo or 'x265' in path:
                continue
            # File to small for encoding
            elif size < int(self.config['default']['min-size']):
                self.logger.info('File smaller than min-size: {}'.format(path))
                continue
            # Unknown encoding
            elif mediainfo == 'unknown':
                self.logger.info('Failed to get encoding for {}'.format(path))

            filtered_files.append(path)

        return filtered_files

    def create_ffmpeg_command(self, path, dest_path):
        """Compile an ffmpeg command with parameters from config."""

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
