import requests
from bs4 import BeautifulSoup, Tag, NavigableString


DARK_URL = 'http://darklyrics.com'

resp = requests.get(DARK_URL)

# print resp.text

soup = BeautifulSoup(resp.text, 'html.parser')

letter_urls = ['{0}{1}'.format(DARK_URL, x.get('href')) for x in soup.find_all('a', href=True)[3:30]]

print letter_urls

resp_letter = requests.get(letter_urls[0])
# print resp_letter.text
soup_a = BeautifulSoup(resp_letter.text, 'html.parser')
# print soup_a.find_all('a', href=True)
band_urls = sorted([('/{0}'.format(x.get('href')), x.get_text()) for x in soup_a.find_all('a', href=True)
                    if x.get('href').startswith('a/')])
print len(band_urls)

single_band_url = '{0}{1}'.format(DARK_URL, band_urls[666][0])
print single_band_url

r = requests.get(single_band_url)
soup_single = BeautifulSoup(r.text, 'html.parser')
print soup_single


def get_single_album_lyrics(album_url):
    res = requests.get('http://www.darklyrics.com/lyrics/amederia/sometimeswehavewings.html#1')
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
        if isinstance(item, NavigableString) and item != '\n':
            songs[song_title].append(item.strip('\r'))
    result_docs = []
    for song, lyrics_list in songs.iteritems():
        # TODO: parse title to get track number
        song_doc = {'artist': 'GET_ARTIST', 'album': album_title_raw, 'title': song, 'lyrics': ''.join(lyrics_list)}
        result_docs.append(song_doc)

    return result_docs

print(get_single_album_lyrics(''))
