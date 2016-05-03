import requests
from bs4 import BeautifulSoup


DARK_URL = 'http://darklyrics.com'

resp = requests.get(DARK_URL)

# print resp.text

soup = BeautifulSoup(resp.text, 'html.parser')

letter_urls = [DARK_URL + x.get('href') for x in soup.find_all('a', href=True)[3:30]]

# print letter_urls

resp_letter = requests.get(letter_urls[0])
# print resp_letter.text
soup_a = BeautifulSoup(resp_letter.text, 'html.parser')
# print soup_a.find_all('a', href=True)
band_urls = [x.get('href') for x in soup_a.find_all('a', href=True) if x.get('href').startswith('a/')]
print band_urls
print len(band_urls)
