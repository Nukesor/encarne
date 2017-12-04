import re
import os
import math
import subprocess

from lxml import etree
from datetime import datetime, timedelta


def check_duration(origin, temp, seconds=1):
    """Check if the duration is bigger than a specific amount."""
    # If the destination movie is shorter than a maximum of 1 seconds as the
    # original or has no duration property in mediainfo, the task will be dropped.
    origin_duration = get_media_duration(origin)
    duration = get_media_duration(temp)

    # If we can't get the duration the user needs to check manually.
    if origin_duration is None:
        return False, False, f'Unknown time format for {origin}. Please compare them by hand.'
    if duration is None:
        return False, False, f'Unknown time format for {temp}. Please compare them by hand.'

    diff = origin_duration - duration
    THRESHOLD = 2
    if math.fabs(diff.total_seconds()) > THRESHOLD:
        return False, True, f'Encoded movie is more than {THRESHOLD} shorter/longer than original.'
    return True, False, "Success"


def check_file_size(origin, temp):
    origin_filesize = os.path.getsize(origin)
    filesize = os.path.getsize(temp)
    if origin_filesize < filesize:
        return False, 'Encoded movie is bigger than the original movie'
    else:
        difference = origin_filesize - filesize
        mebibyte = int(difference/1024/1024)
        return True, f'The new movie is {mebibyte} MIB smaller than the old one'


def get_media_encoding(path):
    """Execute external mediainfo command and find the video encoding library."""
    try:
        process = subprocess.run(
            ['mediainfo', '--Output=XML', path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        root = etree.XML(process.stdout)
        writing_library = root.findall('.//track[@type="Video"]/Writing_library')[0].text
    except:
        writing_library = 'unknown'

    return writing_library


def get_media_duration(path):
    """Execute external mediainfo command and find the video encoding library."""
    process = subprocess.run(
        ['mediainfo', '--Output=XML', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    root = etree.XML(process.stdout)
    try:
        duration = root.findall('.//track[@type="General"]/Duration')[0].text
    except IndexError:
        # No duration, we return None
        return None

    # Newer mediainfo version, duration already is in seconds.
    match = re.match(r'\d+\.\d+', duration)
    if match:
        return timedelta(seconds=int(match[0]))

    if not match:
        match = re.match(r'\d{0,2} h \d{0,2} min \d{0,2} s', duration)
        if match:
            date = datetime.strptime(duration, '%H h %M min %S s')
    if not match:
        match = re.match(r'\d{0,2} h \d{0,2} min', duration)
        if match:
            date = datetime.strptime(duration, '%H h %M min')
    if not match:
        match = re.match(r'\d{0,2} min \d{0,2} s', duration)
        if match:
            date = datetime.strptime(duration, '%M min %S s')
    if not match:
        return None

    delta = timedelta(
        hours=date.hour,
        minutes=date.minute,
        seconds=date.second,
    )

    return delta
