"""Mediainfo related code."""
import os
import math
import subprocess

from lxml import etree
from datetime import datetime, timedelta

from encarne.logger import Logger


def check_duration(origin, temp, seconds=1):
    """Check if the duration is bigger than a specific amount."""
    # If the destination movie is shorter than a maximum of 1 seconds as the
    # original or has no duration property in mediainfo, the task will be dropped.
    origin_duration = get_media_duration(origin)
    duration = get_media_duration(temp)

    # If we can't get the duration the user needs to check manually.
    if origin_duration is None:
        Logger.info(f'Unknown time format for {origin}, compare them by hand.')
        return False, False,
    if duration is None:
        Logger.info(f'Unknown time format for {temp}, compare them by hand.')
        return False, False

    diff = origin_duration - duration
    THRESHOLD = 1
    if math.fabs(diff.total_seconds()) > THRESHOLD:
        Logger.info(f'Length differs more than {THRESHOLD} seconds.')
        return False, True
    return True, False


def check_file_size(origin, temp):
    """Compare the file size of original and re encoded file."""
    origin_filesize = os.path.getsize(origin)
    filesize = os.path.getsize(temp)
    if origin_filesize < filesize:
        Logger.info('Encoded movie is bigger than the original movie')
        return False, True
    else:
        difference = origin_filesize - filesize
        mebibyte = int(difference/1024/1024)
        Logger.info(f'The new movie is {mebibyte} MIB smaller than the old one')
        return True, False


def get_media_encoding(path):
    """Execute external mediainfo command and find the video encoding library."""
    try:
        process = subprocess.run(
            ['mediainfo', '--Output=XML', path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        root = etree.XML(process.stdout)
        writing_library = root.findall('.//track[@type="Video"]/Writing_library')[0].text
    except BaseException:
        writing_library = 'unknown'

    return writing_library


def get_media_duration(path):
    """Execute external mediainfo command and find the video encoding library."""
    process = subprocess.run(
        ['mediainfo', '--Output=PBCore2', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    root = etree.XML(process.stdout)
    try:
        duration = root.find(
            ".//ns:instantiationDuration",
            namespaces={'ns': 'http://www.pbcore.org/PBCore/PBCoreNamespace.html'},
        ).text
    except IndexError:
        Logger.info(f'Could not find duration for {path}')
        return None

    try:
        duration = duration.split('.')[0]
        date = datetime.strptime(duration, '%H:%M:%S')
    except BaseException:
        Logger.info(f'Unkown duration: {duration}')
        return None

    delta = timedelta(
        hours=date.hour,
        minutes=date.minute,
        seconds=date.second,
    )

    return delta
