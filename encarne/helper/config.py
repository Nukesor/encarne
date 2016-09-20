import os
import configparser

from encarne.helper.files import create_config_dir


def read_config():
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
    config['default'] = {
        'directory': 'None',
    }

    write_config(config)
    return config


def write_config(config):
    configFile = create_config_dir() + '/encarne.ini'

    if os.path.exists(configFile):
        os.path.remove(configFile)

    with open(configFile, 'w') as fileDescriptor:
        config.write(fileDescriptor)
