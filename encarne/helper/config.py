import os
import configparser


def create_config_dir():
    """Helper functions for creating a config dir."""
    home = os.path.expanduser('~')
    queueFolder = home+'/.config/encarne'
    if not os.path.exists(queueFolder):
        os.makedirs(queueFolder)
    return queueFolder


def read_config():
    """Get the config file and create it with default values, if it doesn't exist."""
    configFile = create_config_dir() + '/encarne.ini'
    config = configparser.ConfigParser()

    # Try to get config, if this doesn't work a new default config will be created
    if os.path.exists(configFile):
        try:
            config.read(configFile)
            return config
        except:
            print('Error while parsing config file. Deleting old config')

    # Default configuration
    config['encoding'] = {
        'crf': '18',
        'preset': 'slow',
        'audio': 'flac',
        'kbitrate-audio': 'None',
    }

    write_config(config)
    return config


def write_config(config):
    """Write the config file."""
    configFile = create_config_dir() + '/encarne.ini'

    if os.path.exists(configFile):
        os.path.remove(configFile)

    with open(configFile, 'w') as fileDescriptor:
        config.write(fileDescriptor)
