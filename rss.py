import feedparser


class FeedItem():
    def __init__(self, url: str, title: str, description: str) -> None:
        self.url = url
        self.title = title
        self.description = description

class Feed():
    def __init__(self, url: str, items: list[FeedItem]) -> None:
        self.url = url
        self.items = items

class RssReader():
    def get_feed(self, url: str) -> Feed:
        f = feedparser.parse(url)
        items = self.__get_items(f.entries)
        return Feed(url, items)
        
    def __convert_to_feed_item(self, item: dict) -> FeedItem:
        if 'title' in item:
            title = item['title']
        if 'link' in item:
            url = item['link']
        if 'summary' in item:
            description = item['summary']
        return FeedItem(url, title, description)

    def __get_items(self, items: list) -> list:
        list_items = []
        for item in items:
            list_items.append(self.__convert_to_feed_item(item))
        return list_items

