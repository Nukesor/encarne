"""Representation of a task."""
import os
import shlex


class Task():
    """Representation of a task."""

    def __init__(self, path, config):
        """Create a new task."""
        self.origin_path = path
        self.origin_folder = os.path.dirname(path)
        self.origin_file = os.path.basename(path)

        self.set_encoding_paths()
        self.set_command(config)

    def set_encoding_paths(self):
        """Get the temp dir for encoding and the name for the new encoded video file."""
        home = os.path.expanduser('~')

        # Remove any x264 from file_name
        cleand_name = self.origin_file.replace('-x264', '').replace('_x264', '').replace('x264', '')
        self.temp_path = os.path.join(home, cleand_name)
        self.temp_path = os.path.splitext(self.temp_path)[0] + '.mkv'

        self.target_path = os.path.join(
            self.origin_folder,
            os.path.basename(self.temp_path),
        )

    def set_command(self, config):
        """Compile and set the ffmpeg command for pueue."""
        audio_codec = ''
        if config['encoding']['audio'] != 'None':
            audio_codec = f"-map 0:a -c:a {config['encoding']['audio']}"

        if audio_codec != '':
            if config['encoding']['kbitrate-audio'] != 'None':
                audio_codec += f" -b:a {config['encoding']['kbitrate-audio']}"

        self.ffmpeg_command = 'nice -n {nice} ffmpeg -i {path} -map 0 -c copy {audio} -c:v libx265 -preset {preset} ' \
            '-x265-params crf={crf}:pools=none -threads {threads} {dest}'.format(
                path=shlex.quote(self.origin_path),
                dest=shlex.quote(self.temp_path),
                nice=config['default']['niceness'],
                preset=config['encoding']['preset'],
                crf=config['encoding']['crf'],
                threads=config['encoding']['threads'],
                audio=audio_codec,
            )
