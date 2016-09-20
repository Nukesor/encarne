import argparse


def check_crf(value):
    ivalue = int(value)
    if value < 0 or value > 51:
        raise argparse.ArgumentTypeError("Crf has to be between 0 and 51")
    return str(ivalue)


def check_preset(value):
    value = str(value).lower()
    valid_values = ['ultrafast', 'superfast', 'veryfast',
                    'faster', 'fast', 'medium', 'slow', 'slower',
                    'veryslow', 'placebo']
    if value not in valid_values:
        raise argparse.ArgumentTypeError("The preset has to be one of: {}".format(valid_values))
    return value


def check_audio(value):
    value = str(value).lower()
    valid_values = ['aac', 'flac']
    if value not in valid_values:
        raise argparse.ArgumentTypeError("Only those audio encodings are currently allowed: {}".format(valid_values))
    return value
