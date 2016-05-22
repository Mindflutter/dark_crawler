import re


def parse_album_raw(album_title_raw):
    match = re.match('.*"(.*?)" \((\d+)', album_title_raw)
    if match:
        album = match.group(1)
        year = match.group(2)
    else:
        album = album_title_raw
        year = ''
    return album, year
