import feedparser


class FeedItem():
    pass

class Feed():
    pass

class RssReader():
    def convert_to_FeedItem(self, item: dict) -> FeedItem:
        pass

    def get_items(self, items: list) -> list:
        pass

    def get_feed(self, url: str) -> Feed:
        pass


