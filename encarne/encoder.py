"""Encoding."""
import os
import sys
import time
import glob
import configparser
import humanfriendly

from pueue.client.manipulation import execute_add
from pueue.client.factories import command_factory

from encarne.movie import Movie
from encarne.task import Task
from encarne.logger import Logger
from encarne.db import get_session, create_db
from encarne.media import (
    check_file_size,
    check_duration,
    get_media_encoding,
    get_sha1,
)


class Encoder():
    """Encoder class."""

    def __init__(self, args):
        """Create a new encoder."""
        # Initialize encarne sql
        if not os.path.exists('/var/lib/encarne'):
            os.mkdir('/var/lib/encarne')
        if not os.path.exists('/var/lib/encarne/encarne.db'):
            create_db()
        self.session = get_session()

        self.initialize_directories()
        self.read_config()
        self.format_args(args)

        self.tasks = []
        # Various variables
        self.processed_files = 0

    def initialize_directories(self):
        """Create needed directories."""
        self.directory = None
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
            'threads': '4',
        }

        self.config['default'] = {
            'min-size': '{0}'.format(1024*1024*1024*6),
            'SQL_URI': '/var/lib/encarne/encarne.sql',
            'niceness': '15',
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
            elif key == 'size':
                self.config['default']['min-size'] = str(humanfriendly.parse_size(value))

        # Default if no dir is specified
        if not self.directory:
            self.directory = '.'

        # Get absolute path of directory
        self.directory = os.path.abspath(self.directory)
        Logger.info(f'Searching for files in directory {self.directory}')

        # Check if path is a dir
        if not os.path.isdir(self.directory):
            Logger.warning('A valid directory needs to be specified')
            Logger.warning(self.directory)
            sys.exit(1)

    def run(self):
        """Get all known video files by recursive extension search."""
        extensions = ['mkv', 'mp4', 'avi']
        files = []
        for extension in extensions:
            found = glob.glob(
                os.path.join(self.directory, f'**/*.{extension}'),
                recursive=True)
            files = files + found

        self.create_tasks(files)

        if len(self.tasks) == 0:
            Logger.info('No files for encoding found.')
            sys.exit(0)
        else:
            Logger.info(f'{len(self.tasks)} files found.')

        # Add all tasks to pueue
        for task in self.tasks:
            self.add_task(task)

        # Wait for all tasks
        for task in self.tasks:
            self.wait_for_task(task)
            self.validate_encoded_file(task)

        Logger.info(f'Successfully encoded {self.processed_files} movies. Exiting')

    def create_tasks(self, files):
        """Filter files and check if they are already done or failed in a previous run.

        Ignore previously failed movies (too big, duration differs) and already encoded movies.
        Create a task with all paths and the compiled ffmpeg command.
        """
        for path in files:
            # Get absolute path
            path = os.path.abspath(path)
            mediainfo = get_media_encoding(path)

            task = Task(path, self.config)
            size = os.path.getsize(path)

            # Get movie from db and check for already encoded or failed files.
            task.movie = Movie.get_or_create(self.session, task.origin_file,
                                             task.origin_folder, size)
            if task.movie.encoded or task.movie.failed:
                continue

            # Already encoded
            if '265' in mediainfo or '265' in path:
                task.movie.encoded = True
                self.session.add(task.movie)
                continue
            # File to small for encoding
            elif size < int(self.config['default']['min-size']):
                Logger.debug('File smaller than min-size: {path}')
                continue
            # Unknown encoding
            elif mediainfo == 'unknown':
                Logger.info(f'Failed to get encoding for {path}')

            self.tasks.append(task)

        self.session.commit()

    def add_task(self, task):
        """Schedule and manage encoding of a movie.

        2. The command is added to pueue.
        3. Wait for the task to finish.
        4. Check if the encoding was successful.
        4.1 If it wasn't successful, we delete the encoded file and mark the
            old file as `encarne-failed`.
        4.2 Remove the old file and move the encoded file to the proper location.
        5. Repeat

        """
        # Check if the current command already in the queue.
        status = self.get_newest_status(task.ffmpeg_command)

        # Send the command to pueue for scheduling, if it isn't in the queue yet
        if status is None:
            # In case a previous run failed and pueue has been resetted,
            # we need to check, if the encoded file is still there.
            if os.path.exists(task.temp_path):
                os.remove(task.temp_path)

            # Create a new pueue task
            args = {
                'command': [task.ffmpeg_command],
                'path': task.origin_folder,
            }
            Logger.info(f'Add task pueue:\n {task.ffmpeg_command}')
            execute_add(args, os.path.expanduser('~'))

    def wait_for_task(self, task):
        """Wait for the pueue task to finish."""
        Logger.info(f'Waiting for task {task.origin_file}.')
        waiting = True
        while waiting:
            # Get index of current command and the current status
            status = self.get_newest_status(task.ffmpeg_command)
            # If the command has been removed or failed,
            # remove the already created destination file.
            if status is None or status == 'failed':
                if os.path.exists(task.temp_path):
                    os.remove(task.temp_path)
                waiting = False
            # If the command has finished, stop the loop for further processing
            elif status == 'done':
                waiting = False
            else:
                time.sleep(60)

    def validate_encoded_file(self, task):
        """Validate that the encoded file is not malformed."""
        if os.path.exists(task.temp_path):
            Logger.info("Pueue task completed")
            # Check if the duration of both movies differs.
            copy, delete = check_duration(task.origin_path, task.temp_path, seconds=1)

            # Check if the filesize of the x.265 encoded object is bigger
            # than the original.
            if copy:
                copy, delete = check_file_size(task.origin_path, task.temp_path)

            # Only copy if checks above passed
            if copy:
                # Save new path, size, sha1 and mark as encoded
                task.movie.sha1 = get_sha1(task.temp_path)
                task.movie.size = os.path.getsize(task.temp_path)
                task.movie.encoded = True
                task.movie.name = os.path.basename(task.target_path)

                self.session.add(task.movie)
                self.session.commit()

                # Get original file permissions
                stat = os.stat(task.origin_path)

                # Remove the old file and copy the new one to the proper directory.
                os.remove(task.origin_path)
                os.rename(task.temp_path, task.target_path)
                # Set original file permissions on new file.
                os.chmod(task.target_path, stat.st_mode)
                try:
                    os.chown(task.target_path, stat.st_uid, stat.st_gid)
                except PermissionError:
                    Logger.info("Failed to set ownership for {0}".format(task.target_path))
                    pass
                self.processed_files += 1
                Logger.info("New encoded file is now in place")
            elif delete:
                # Mark as failed and save
                task.movie.failed = True
                self.session.add(task.movie)
                self.session.commit()

                os.remove(task.temp_path)
                Logger.warning("Didn't copy new file, see message above")
        else:
            Logger.error("Pueue task failed in some kind of way.")

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
