import re


def parse_album_raw(album_title_raw):
    match = re.match('.*"(.*?)" \((\d+)', album_title_raw)
    if match:
        album = match.group(1)
        year = int(match.group(2))
    else:
        album = album_title_raw
        year = 0
    return album, year


def parse_track_title(track_title_raw):
    match = re.match('(\d+)\. (.*)', track_title_raw)
    if match:
        track_number = int(match.group(1))
        track_title = match.group(2)
    else:
        track_number = 0
        track_title = track_title_raw
    return track_number, track_title


def try_n_pass(func):
    def wrapped(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception:
            # TODO: log what failed
            result = None
        return result
    return wrapped
