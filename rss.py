import feedparser


class FeedItem():
    pass

class Feed():
    def __init__(self, url: str, items: list) -> None:
        self.url = url
        self.items = items

class RssReader():
    def convert_to_FeedItem(self, item: dict) -> FeedItem:
        pass

    def get_items(self, items: list) -> list:
        pass

    def get_feed(self, url: str) -> Feed:
        f = feedparser.parse(url)
        items = self.get_items(f.entries)
        return Feed(url, items)
