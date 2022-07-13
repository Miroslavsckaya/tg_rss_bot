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

        for feed in feeds:
            self.log.info('Processing [%d] %s', feed['id'], feed['url'])
            feed_obj = self.rss_reader.get_feed(feed['url'])
            new_items = feed_obj.items
            old_items = self.database.find_feed_items(feed['id'])

            diff = self.__calculate_difference(new_items, old_items)

            if not diff:
                continue

            chat_ids = self.database.find_feed_subscribers(feed['id'])
            self.notifier.send_updates(chat_ids, diff, feed_obj.title)
            self.database.update_feed_items(feed['id'], new_items)

    def __calculate_difference(self, new_items: list[FeedItem], old_items: list[dict]) -> list[FeedItem]:
        """Calculate new feed items."""
        self.log.debug(
            '__calculate_difference(new_items=list(%d), old_items=list(%d))', len(new_items), len(old_items)
        )
        if not old_items:
            self.log.debug('Old items are empty, returning new')
            return new_items

        diff = []
        guids = [item['guid'] for item in old_items if item['guid']]
        urls = [item['url'] for item in old_items]

        self.log.debug('Comparing %d new items with %d old', len(new_items), len(old_items))
        for item in new_items:
            if not guids and item.url not in urls:
                diff.append(item)
                continue
            if item.guid not in guids:
                diff.append(item)

        self.log.debug('%d updates found', len(diff))

        return diff
