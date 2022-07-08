from rss import RssReader, FeedItem
from database import Database
from telegram import Notifier


class UpdateManager:
    """Implement the feed update."""

    def __init__(self, database: Database, notifier: Notifier, rss_reader: RssReader) -> None:
        self.database: Database = database
        self.notifier: Notifier = notifier
        self.rss_reader: RssReader = rss_reader

    def update(self):
        """Send new feed items to the user."""
        feeds = self.database.find_feeds()

        for feed_id, feed_url in feeds:
            feed = self.rss_reader.get_feed(feed_url)
            new_items = feed.items
            old_items_urls = self.database.find_feed_items_urls(feed_id)

            diff = self.__calculate_difference(new_items, old_items_urls)

            if not diff:
                continue

            chat_ids = self.database.find_feed_subscribers(feed_id)
            self.notifier.send_updates(chat_ids, diff, feed.title)
            self.database.update_feed_items(feed_id, new_items)

    def __calculate_difference(self, new_items: list[FeedItem], old_items_urls: list[str]) -> list[FeedItem]:
        """Calculate new feed items."""
        if not old_items_urls:
            return new_items

        diff = []

        for item in new_items:
            if item.url not in old_items_urls:
                diff.append(item)

        return diff
