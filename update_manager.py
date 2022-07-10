from logging import Logger

from rss import RssReader, FeedItem
from database import Database
from telegram import Notifier


class UpdateManager:
    """Implement the feed update."""

    def __init__(self, database: Database, notifier: Notifier, rss_reader: RssReader, logger: Logger) -> None:
        self.log: Logger = logger
        self.log.debug(
            'UpdateManager.__init__(database=%s, notifier=%s, rss_reader=%s, logger=%s)',
            database, notifier, rss_reader, logger
        )
        self.database: Database = database
        self.notifier: Notifier = notifier
        self.rss_reader: RssReader = rss_reader

    def update(self):
        """Send new feed items to the user."""
        self.log.info('Running update')
        feeds = self.database.find_feeds()
        self.log.info('Feeds to update: %d', len(feeds))

        for feed_id, feed_url in feeds:
            self.log.info('Processing [%d] %s', feed_id, feed_url)
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
        self.log.debug(
            '__calculate_difference(new_items=list(%d), old_items_urls=list(%d))', len(new_items), len(old_items_urls)
        )
        if not old_items_urls:
            self.log.debug('Old items are empty, returning new')
            return new_items

        diff = []

        self.log.debug('Comparing %d new items with %d old', len(new_items), len(old_items_urls))
        for item in new_items:
            if item.url not in old_items_urls:
                diff.append(item)

        self.log.debug('%d updates found', len(diff))

        return diff
