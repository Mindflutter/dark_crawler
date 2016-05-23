Dark Crawler
============

**Don't betray metal!**

## What

Dark Crawler is a service that crawls a website containing metal lyrics and indexes results to Elasticsearch.
Resulting documents have a flat structure and contain info on the following items:

* Artist
* Album
* Year
* Track number
* Track title
* Lyrics

## Why

Result data acquired with the help of the Dark Crawler is presented in a convenient and sensible json format and stored
into a modern database, which enables easy retrieving, analysis, representation and further processing of the data. 

## Limitations

* Dark Crawler is a custom solution and works with [Darklyrics](http://www.darklyrics.com/) only. A generic solution
could be considered, but usually those just suck. Tweak the Dark Crawler to create a new custom crawler instead.
* Dark Crawler works synchronously and slowly not to bombard the remote server with requests, which results in
empty lyrics pages (essentially an IP ban).
* Dark Crawler understands only latin1 encoding, which is the most common one. It could be improved by implementing
an encoding resolver.
