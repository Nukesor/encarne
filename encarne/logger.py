"""Logging for encarne."""
import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler


class DirRotatingFileHandler(RotatingFileHandler):
    """Create log dir."""

    def __init__(self, filename, **kwargs):
        """Init file handler."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        RotatingFileHandler.__init__(self, filename, **kwargs)


# Logger init and logger format
Logger = logging.getLogger('')
Logger.setLevel(logging.INFO)
format_str = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Stream handler
channel_handler = logging.StreamHandler(sys.stdout)
channel_handler.setFormatter(format_str)
Logger.addHandler(channel_handler)

# Log file and log dir
home = os.path.expanduser('~')
timestamp = time.strftime('-%Y%m%d-%H%M-')
log_dir = os.path.join(home, '.local/share/encarne')
log_file = os.path.join(log_dir, f'encarne{timestamp}.log')


# File handler
file_handler = DirRotatingFileHandler(log_file, maxBytes=(1048576*100), backupCount=7)
file_handler.setFormatter(format_str)
Logger.addHandler(file_handler)
