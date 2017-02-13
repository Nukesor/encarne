import re
import subprocess

from lxml import etree
from datetime import datetime, timedelta


def get_media_encoding(self, path):
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
        self.logger.error('Failed to get media info for {}'.format(path))
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
