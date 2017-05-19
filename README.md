# Encarne

This is a project for automatic `h.265` encoding of all video containers in a specified directory.

Every single file that isn't encoded with `x265` yet will be encoded using `x265` one by one.
We use `pueue` for scheduling and process handling.
Another requirement is `mediainfo`. A program we need to determine the used encoding for any video container.

## Installation:

**encarne**:  
There are three different ways to install pueue.

1. Use an Arch Linux AUR package manager i.e Yaourt: `yaourt -S encarne-git` . This will deploy the service file automatically.
2. Install by using pip: `pip install encarne`.
3. Clone the repository and execute `python setup.py install`.


**Mediainfo**:  
You need to install `mediainfo` to use encarne.

**Pueue**:  
Pueue will be installed together with encarne, but you need to start the Pueue daemon. Execute `pueue --daemon` for this.


## Configuration

Default parameters for `ffmpeg` encoding:

    # Default configuration
    ['encoding']
    crf = 18
    preset = slow
    audio = flac
    kbitrate-audio None

    [default]
    min-size = 6442450944

All parameters are adjustable using the command line. Just use `-h` for more information.

A configuration file is created in `/home/$USER/.config/encarne` after the first start.


Copyright &copy; 2016 Arne Beer ([@Nukesor](https://github.com/Nukesor))
