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

        # Change filename to contain 'x265'.
        # Replace it if there is a 'x264' in the filename.
        if 'x264' in self.origin_file:
            self.temp_path = os.path.join(home, self.origin_file.replace('x264', 'x265'))
            self.temp_path = os.path.splitext(self.temp_path)[0] + '.mkv'
        # Add a `-x265.mkv` if there is nothing to replace
        else:
            self.temp_path = os.path.join(home, self.origin_file)
            self.temp_path = os.path.splitext(self.temp_path)[0] + '-x265.mkv'

        self.target_path = os.path.join(
            self.origin_folder,
            os.path.basename(self.temp_path),
        )

    def set_command(self, config):
        """Compile and set the ffmpeg command for pueue."""
        if config['encoding']['kbitrate-audio'] != 'None':
            audio_bitrate = f"-b:a {config['encoding']['kbitrate-audio']}"
        else:
            audio_bitrate = ''

        if config['encoding']['audio'] != 'None':
            audio_codec = f"-map 0:a -c:a {config['encoding']['audio']}"
        else:
            audio_codec = '-map 0:a'

        subtitles = ''

        self.ffmpeg_command = 'nice -n {nice} ffmpeg -i {path} -map 0:v -c:s copy -c:v libx265 -preset {preset} ' \
            '-x265-params crf={crf}:pools=none -threads {threads} {audio} {audio_bitrate} {subtitles} {dest}'.format(
                path=shlex.quote(self.origin_path),
                dest=shlex.quote(self.temp_path),
                nice=config['default']['niceness'],
                preset=config['encoding']['preset'],
                crf=config['encoding']['crf'],
                threads=config['encoding']['threads'],
                audio=audio_codec,
                subtitles=subtitles,
                audio_bitrate=audio_bitrate,
            )
