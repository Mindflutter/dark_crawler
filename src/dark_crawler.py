import requests
import time
import logging
import yaml
from bs4 import BeautifulSoup, Tag, NavigableString
from urlparse import urljoin
from elasticsearch import Elasticsearch

from helpers import parse_album_raw, parse_track_title, try_n_pass


class DarkCrawler(object):

    def __init__(self, config):
        self.dark_url = config['dark_url']
        logging.basicConfig(filename=config['logfile'], format='%(asctime)s %(name)s %(levelname)s %(message)s',
                            level=logging.INFO)
        self.logger = logging.getLogger('DARK_CRAWLER')
        # lower the noisiness
        logging.getLogger("elasticsearch").setLevel(logging.WARNING)

        self.session = requests.Session()
        self.es_client = Elasticsearch([{'host': config['elasticsearch_host'], 'port': config['elasticsearch_port']}])
        self.index = config['index']
        self.doc_type = config['doc_type']

    def get_letter_urls(self):
        resp = self.session.get(self.dark_url)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # get list of tuples (URL, prefix)
        return [(urljoin(self.dark_url, x.get('href')), x.get('href').replace('.html', '').strip('/') + '/')
                for x in soup.find_all('a')[3:30]]

    def get_band_urls(self, letter_url, prefix):
        resp_letter = self.session.get(letter_url)
        soup_letter = BeautifulSoup(resp_letter.text, 'html.parser')
        # get list of tuples (partial URL, band name)
        return sorted([(urljoin(self.dark_url, item.get('href')), item.get_text())
                       for item in soup_letter.find_all('a', href=True)
                       if item.get('href').startswith(prefix)])

    def get_album_urls(self, single_band_url):
        res = self.session.get(single_band_url)
        soup_single = BeautifulSoup(res.text, 'html.parser')
        albums = soup_single.findAll('div', {'class': 'album'})
        album_urls = []
        for album_info in albums:
            # url to the first song on album leads to the page with all album songs
            album_urls.append(urljoin(single_band_url, album_info.find('a').get('href')))
        return album_urls

    @try_n_pass
    def get_single_album_lyrics(self, album_url, artist):
        res = self.session.get(album_url)
        parsed_page = BeautifulSoup(res.text, 'html.parser')
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
        album, year = parse_album_raw(album_title_raw)
        for song, lyrics_list in songs.iteritems():
            track_number, track_title = parse_track_title(song)
            song_doc = {'artist': artist.encode('latin1'), 'album': album.encode('latin1'),
                        'year': year, 'track_number': track_number, 'track_title': track_title.encode('latin1'),
                        'lyrics': ''.join(lyrics_list).encode('latin1')}
            result_docs.append(song_doc)
        return result_docs

    def process(self):
        letter_urls = self.get_letter_urls()
        for letter_url in letter_urls:
            band_urls = self.get_band_urls(letter_url[0], letter_url[1])
            for band_url in band_urls:
                self.logger.info('Processing band {0}'.format(band_url[1].encode('latin1')))
                album_urls = self.get_album_urls(band_url[0])
                for album_url in album_urls:
                    self.logger.info('Indexing album {0}'.format(album_url))
                    docs = self.get_single_album_lyrics(album_url, band_url[1])
                    if docs:
                        for doc in docs:
                            try:
                                self.es_client.index(index=self.index, doc_type=self.doc_type, body=doc)
                            except Exception as error:
                                self.logger.error('Indexing error {0} for document {1}'.format(error, doc))
                                continue
                        time.sleep(5)
                    else:
                        self.logger.error('Parsing lyrics for album {0} failed'.format(album_url))


def main():
    with open('../resources/dark_crawler.yml') as conf_file:
        config = yaml.safe_load(conf_file)

    dark_crawler = DarkCrawler(config)
    dark_crawler.process()


if __name__ == '__main__':
    main()
