# Encarne

Encarne is a tool for automatic `h.265` encoding of all video containers in a specified directory.

Every container, which isn't encoded with `x265` will be reencoded using `x265` one by one.
`pueue` is used for scheduling and process handling.
Another requirement is `mediainfo`, which is needed to determine various attributes of video containers.

## Features:

- Automatic conversion of all movies/series in a directory
- Easy configurable ffmpeg command
- Configurable encoder thread count
- Niceness to not slow down other processes on your server
- Database to remember failed movies and to measure overall storage savings
- Schedule management with pueue

## Installation:

**encarne**:  
There are three different ways to install pueue.

1. An arch linux AUR package manager e.g `yaourt`: `yaourt -S encarne-git` . This will deploy the service file automatically.
2. Pip: `pip install encarne`.
3. Clone the repository and execute `python setup.py install`.

**Database**:
If you don't use an AUR package manager for installation you need to create the directory `/var/lib/encarne` and grant permissions for your user.

**Mediainfo**:  
You need to install `mediainfo` to use encarne.

**Pueue**:  
`Pueue` will be installed together with encarne, but you need to start the `Pueue` daemon once with `pueue --daemon`.


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


## Stats

Type `encarne stat` to show how much space you already saved.


Copyright &copy; 2016 Arne Beer ([@Nukesor](https://github.com/Nukesor))
