import requests
import time
import logging
import yaml
import os
from bs4 import BeautifulSoup, Tag, NavigableString
from urlparse import urljoin
from elasticsearch import Elasticsearch

from helpers import parse_album_raw, parse_track_title, try_n_pass


class DarkCrawler(object):

    def __init__(self, config):
        """ Constructor. Initializes the Dark Crawler.
        Args:
            config (dict): configuration object.
        """
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
        """ Get a set of URLs to alphabet letters with letter prefixes that indicate a URL to each band.
        Returns:
            list of tuples: [(URL, prefix)]
        """
        response = self.session.get(self.dark_url)
        parsed_page = BeautifulSoup(response.text, 'html.parser')
        return [(urljoin(self.dark_url, x.get('href')), x.get('href').replace('.html', '').strip('/') + '/')
                for x in parsed_page.find_all('a')[3:30]]

    def get_band_urls(self, letter_url, prefix):
        """ Get a set of band URLs and corresponding band names for a given alphabet letter.
        Args:
            letter_url (str): URL to alphabet letter.
            prefix (str): corresponding letter prefix.
        Returns:
            list of tuples: [(band URL, band name)]
        """
        response = self.session.get(letter_url)
        parsed_page = BeautifulSoup(response.text, 'html.parser')
        return sorted([(urljoin(self.dark_url, item.get('href')), item.get_text())
                       for item in parsed_page.find_all('a', href=True)
                       if item.get('href').startswith(prefix)])

    def get_album_urls(self, single_band_url):
        """ Get a list of URLs to albums for a single band.
        Args:
            single_band_url (str): URL to a single band's page.
        Returns:
            list of str: [URL to a single album page with lyrics]
        """
        response = self.session.get(single_band_url)
        parsed_page = BeautifulSoup(response.text, 'html.parser')
        albums = parsed_page.findAll('div', {'class': 'album'})
        album_urls = []
        for album_info in albums:
            # url to the first song on album leads to the page with all album songs
            album_urls.append(urljoin(single_band_url, album_info.find('a').get('href')))
        return album_urls

    @try_n_pass
    def get_single_album_lyrics(self, album_url, artist):
        """ Get lyrics for a single album in a sensible format.
        Args:
            album_url (str): URL to a single album page with lyrics.
            artist (str): band name.
        Returns:
            list of dict: [dictionary containing single track info]
            Example:
                {'artist': 'DIMMU BORGIR', 'album': 'Death Cult Armageddon', 'year': 2003, 'track_number': 1,
                 'track_title': 'Allegiance', 'lyrics': 'Cuddled through a cold womb he was...'}
        """
        response = self.session.get(album_url)
        parsed_page = BeautifulSoup(response.text, 'html.parser')
        album_title_raw = parsed_page('h2')[0].get_text()
        lyrics = parsed_page.findChildren('div', {'class': 'lyrics'})[0]
        tracks = {}
        for item in lyrics.contents:
            if isinstance(item, Tag) and item.name == 'h3':
                # FIXME: extract() modifies list on the fly
                title = item.extract().get_text()
                tracks[title] = []
            # Annotations in italics
            if isinstance(item, Tag) and item.name == 'i':
                tracks[title].append('\n' + item.get_text())
            if isinstance(item, NavigableString) and item != '\n':
                tracks[title].append(item.strip('\r'))
        result_docs = []
        album, year = parse_album_raw(album_title_raw)
        for track, lyrics_list in tracks.iteritems():
            track_number, track_title = parse_track_title(track)
            song_doc = {'artist': artist.encode('latin1'), 'album': album.encode('latin1'),
                        'year': year, 'track_number': track_number, 'track_title': track_title.encode('latin1'),
                        'lyrics': ''.join(lyrics_list).encode('latin1')}
            result_docs.append(song_doc)
        return result_docs

    def process(self):
        """ Main process method. Goes through all lyrics and performs track info indexing. """
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
                        # wait time not to get banned by the server
                        time.sleep(5)
                    else:
                        self.logger.error('Parsing lyrics for album {0} failed'.format(album_url))


def main():
    """ Entry point. """
    conf_file_location = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/dark_crawler.yml"))
    with open(conf_file_location) as conf_file:
        config = yaml.safe_load(conf_file)

    dark_crawler = DarkCrawler(config)
    dark_crawler.process()


if __name__ == '__main__':
    main()
