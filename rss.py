import feedparser


class FeedItem():
    def __init__(self, url: str, title: str, description: str) -> None:
        self.url = url
        self.title = title
        self.description = description

class Feed():
    def __init__(self, url: str, items: list) -> None:
        self.url = url
        self.items = items

class RssReader():
    def convert_to_FeedItem(self, item: dict) -> FeedItem:
        if 'title' in item:
            title = item['title']
        if 'link' in item:
            url = item['link']
        if 'summary' in item:
            description = item['summary']
        return FeedItem(url, title, description)

    def get_items(self, items: list) -> list:
        list_items = []
        for item in items:
            list_items.append(self.convert_to_FeedItem(item))
        return list_items

    def get_feed(self, url: str) -> Feed:
        f = feedparser.parse(url)
        items = self.get_items(f.entries)
        return Feed(url, items)
