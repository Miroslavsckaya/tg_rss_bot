from logging import Logger
from datetime import datetime
from time import mktime
from feedparser import FeedParserDict, parse


class FeedItem:
    def __init__(self, item: FeedParserDict) -> None:
        self.url = item.get('link', '')
        self.title = item.get('title', '')
        self.description = item.get('summary', '')
        self.guid = item.get('id', '')
        if 'updated' in item:
            self.date = datetime.fromtimestamp(mktime(item.updated_parsed))
        elif 'published' in item:
            self.date = datetime.fromtimestamp(mktime(item.published_parsed))
        else:
            self.date = None


class Feed:
    def __init__(self, url: str, feed: FeedParserDict) -> None:
        self.url = url
        self.items = []
        self.title = feed.feed.get('title', '')
        for item in feed.entries:
            self.items.append(FeedItem(item))


class RssReader:

    def __init__(self, logger: Logger):
        self.log: Logger = logger
        self.log.debug('RssReader.__init__(logger=%s)', logger)

    def get_feed(self, url: str) -> Feed:
        self.log.debug('get_feed(url=\'%s\')', url)
        return Feed(url, parse(url))
