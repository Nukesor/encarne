# Encarne

This is a project for automatic `h.265` encoding of all video containers in a specified directory.

Every single file that isn't encoded with `x265` yet will be encoded using `x265` one by one.
We use `pueue` for scheduling and process handling.
Another requirement is `mediainfo`. A program we need to determine the used encoding for any video container.


Default parameters for `ffmpeg` encoding:

    # Default configuration
    'crf': '18',
    'preset': 'slow',
    'audio': 'flac',
    'kbitrate-audio': 'None',

All parameters are adjustable using the command line. Just use `-h` for more information.

A configuration file is created in `/home/$USER/.config/encarne` after the first start.


Copyright &copy; 2016 Arne Beer ([@Nukesor](https://github.com/Nukesor))
