import os
import sys
from encarne.helper.config import read_config


def execute_run(args):
    config = read_config()

    args = {key: value for key, value in args.items() if value}
    for key, value in args.items():
        if key == 'dir':
            config['default']['directory'] = value
        # Encoding
        if key == 'crf':
            config['encoding']['crf'] = value
        elif key == 'preset':
            config['encoding']['preset'] = value
        elif key == 'audio':
            config['encoding']['audio'] = value
        elif key == 'audio':
            config['encoding']['kbitrate-audio'] = value

    if not config['default']['directory'] or \
       not os.path.isdir(config['default']['directory']):
        print('A valid directory needs to be specified')
        sys.exit(1)
    else:
        # Get absolute path of directory
        config['default']['directory'] = os.path.abspath(config['default']['directory'])
