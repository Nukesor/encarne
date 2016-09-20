import os


def create_config_dir():
    home = os.path.expanduser('~')
    queueFolder = home+'/.config/encarne'
    if not os.path.exists(queueFolder):
        os.makedirs(queueFolder)
    return queueFolder


def create_log_dir():
    home = os.path.expanduser('~')
    logFolder = home+'/.local/share/encarne'
    if not os.path.exists(logFolder):
        os.makedirs(logFolder)
    return logFolder
