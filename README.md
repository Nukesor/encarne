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
`Pueue` will be installed together with encarne, but you need to start the `Pueue` daemon once with `pueue --daemon`. A systemctl service is installed for `Pueue` if you use an AUR package manager. Start it with `systemctl --user start pueue`.


## Configuration

Default parameters for `ffmpeg` encoding:

    # Default configuration
    ['encoding']
    crf = 18
    preset = slow
    audio = None
    kbitrate-audio = None
    threads: 4,

    [default]
    min-size = 6442450944
    niceness = 15

All parameters are adjustable using the command line. Just use `-h` for more information.

A configuration file is created in `/home/$USER/.config/encarne` after the first start.


## Misc

All movies are now hashed with sha1.
If you move a movie to another location and run `encarne` again, it will recognize the movie and update the path in it's DB.

Type `encarne stat` to show how much space you already saved (Non existent files aren't counted).
Type `encarne clean` to clean movies which do no longer exist in the file system.

# Migration
In `1.4.0` the sha1 hash is introduced. As there is no migration system there yet, you need to run the migration once manually:

        > sqlite3 /var/lib/encarne
        --> ALTER TABLE movie ADD sha1 VARCHAR(40);


Copyright &copy; 2016 Arne Beer ([@Nukesor](https://github.com/Nukesor))
