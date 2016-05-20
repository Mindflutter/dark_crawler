import requests
from bs4 import BeautifulSoup, Tag, NavigableString
from urlparse import urljoin


DARK_URL = 'http://darklyrics.com'

resp = requests.get(DARK_URL)

# print resp.text

soup = BeautifulSoup(resp.text, 'html.parser')

# get list of tuples (URL, prefix)
letter_urls = [(urljoin(DARK_URL, x.get('href')), x.get('href').replace('.html', '').strip('/') + '/') for x in soup.find_all('a')[3:30]]

# print letter_urls


def get_band_urls(letter_url, prefix):
    resp_letter = requests.get(letter_url)
    soup_letter = BeautifulSoup(resp_letter.text, 'html.parser')
    # get list of tuples (partial URL, band name)
    band_urls = sorted([(item.get('href'), item.get_text()) for item in soup_letter.find_all('a', href=True)
                        if item.get('href').startswith(prefix)])
    return band_urls


def get_album_urls(single_band_url):
    res = requests.get('http://darklyrics.com/a/ayreon.html')
    soup_single = BeautifulSoup(res.text, 'html.parser')
    albums = soup_single.findAll('div', {'class': 'album'})
    album_urls = []
    for album_info in albums:
        # url to the first song on album leads to the page with all album songs
        album_urls.append(urljoin('http://darklyrics.com/a/ayreon.html', album_info.find('a').get('href')))
    return album_urls


def get_single_album_lyrics(album_url):
    res = requests.get(album_url)
    parsed_page = BeautifulSoup(res.text, 'html.parser')
    # TODO: parse it further using regex (now looks like u'album: "Sometimes We Have Wings" (2008)')
    album_title_raw = parsed_page('h2')[0].get_text()
    lyrics = parsed_page.findChildren('div', {'class': 'lyrics'})[0]
    songs = {}
    for item in lyrics.contents:
        if isinstance(item, Tag) and item.name == 'h3':
            # FIXME: extract() modifies list on the fly
            song_title = item.extract().get_text()
            songs[song_title] = []
        # Annotations in italics
        if isinstance(item, Tag) and item.name == 'i':
            songs[song_title].append('\n' + item.get_text())
        if isinstance(item, NavigableString) and item != '\n':
            songs[song_title].append(item.strip('\r'))
    result_docs = []
    for song, lyrics_list in songs.iteritems():
        # TODO: parse title to get track number
        song_doc = {'artist': 'GET_ARTIST', 'album': album_title_raw, 'title': song, 'lyrics': ''.join(lyrics_list)}
        result_docs.append(song_doc)

    return result_docs

for i in get_album_urls(''):
    print(get_single_album_lyrics(i))

# print(get_album_urls(''))
#
# for i in letter_urls:
#     print(get_band_urls(i[0], i[1]))

