""" Various helper functions. """
import re
import logging


def parse_album_raw(album_title_raw):
    """ Parse raw album title into a sensible title and year.
    Args:
        album_title_raw (str): raw album info string.
    Returns:
        tuple (str, int): (album, year).
    """
    match = re.match('.*"(.*?)" \((\d+)', album_title_raw)
    if match:
        album = match.group(1)
        year = int(match.group(2))
    else:
        album = album_title_raw
        year = 0
    return album, year


def parse_track_title(track_title_raw):
    """ Parse raw track title into a sensible track number and title.
    Args:
        track_title_raw (str): raw track info string.
    Returns:
        tuple (int, str): (number, title).
    """
    match = re.match('(\d+)\. (.*)', track_title_raw)
    if match:
        track_number = int(match.group(1))
        track_title = match.group(2)
    else:
        track_number = 0
        track_title = track_title_raw
    return track_number, track_title


def try_n_pass(func):
    """ Decorator for catching and logging a possible exception within a function
    that might cause a process to crash.
    Returns:
        Function result if no exception was caught. None otherwise.
    """
    def wrapped(*args, **kwargs):
        logging.basicConfig(filename='decorator_exceptions.log',
                            format='%(asctime)s %(name)s %(levelname)s %(message)s')
        log = logging.getLogger(func.__name__)
        try:
            result = func(*args, **kwargs)
        except Exception as error:
            log.error("Exception caught in method: {0}".format(error))
            result = None
        return result
    return wrapped
