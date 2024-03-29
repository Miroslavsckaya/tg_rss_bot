from logging import Logger
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor, DictRow
from yoyo import get_backend, read_migrations
from exceptions import DisplayableException
from rss import FeedItem


class Database:
    """Implement interaction with the database."""

    def __init__(self, dsn: str, log: Logger) -> None:
        """Initialize the database"""
        self.log: Logger = log
        self.log.debug('Database.__init__(DSN=\'%s\')', dsn)
        self.conn: connection = psycopg2.connect(dsn)
        self.cur: DictCursor = self.conn.cursor(cursor_factory=DictCursor)
        self.__migrate(dsn)

    def add_user(self, telegram_id: int) -> int:
        """Add a user's telegram id to the database and return its database id."""
        self.log.debug('add_user(telegram_id=\'%s\')', telegram_id)
        self.cur.execute('INSERT INTO users (telegram_id) VALUES (%s) RETURNING id', [telegram_id])
        self.conn.commit()
        return self.cur.fetchone()[0]

    def find_user(self, telegram_id: int) -> int | None:
        """Get a user's telegram id and return its database id."""
        self.log.debug('find_user(telegram_id=\'%s\')', telegram_id)
        self.cur.execute('SELECT id FROM users WHERE telegram_id = %s', [telegram_id])
        row = self.cur.fetchone()
        if row is None:
            return None
        return row['id']

    def add_feed(self, url: str) -> int:
        """Add a feed to the database and return its id."""
        self.log.debug('add_feed(url=\'%s\')', url)
        self.cur.execute('INSERT INTO feeds (url) VALUES (%s) RETURNING id', [url])
        self.conn.commit()
        return self.cur.fetchone()[0]

    def find_feed_by_url(self, url: str) -> int | None:
        """Find feed ID by url."""
        self.log.debug('find_feed_by_url(url=\'%s\')', url)
        self.cur.execute('SELECT id FROM feeds WHERE url = %s', [url])
        row = self.cur.fetchone()
        if row is None:
            return None
        return row['id']

    def subscribe_user_by_url(self, user_id: int, url: str) -> None:
        """Subscribe user to the feed creating it if does not exist yet."""
        self.log.debug('subscribe_user_by_url(user_id=\'%s\', url=\'%s\')', user_id, url)
        feed_id = self.find_feed_by_url(url)
        if feed_id is None:
            feed_id = self.add_feed(url)

        if self.is_user_subscribed(user_id, feed_id):
            raise DisplayableException('Already subscribed')

        self.subscribe_user(user_id, feed_id)

    def subscribe_user(self, user_id: int, feed_id: int) -> None:
        """Subscribe a user to the feed."""
        self.log.debug('subscribe_user(user_id=\'%s\', feed_id=\'%s\')', user_id, feed_id)
        self.cur.execute('INSERT INTO subscriptions (user_id, feed_id) VALUES (%s, %s)', [user_id, feed_id])
        self.conn.commit()

    def unsubscribe_user_by_url(self, user_id: int, url: str) -> None:
        """Subscribe a user to the feed by url."""
        self.log.debug('unsubscribe_user_by_url(user_id=\'%s\', url=\'%s\')', user_id, url)
        feed_id = self.find_feed_by_url(url)
        if feed_id is None:
            raise DisplayableException('Feed does not exist')

        if not self.is_user_subscribed(user_id, feed_id):
            raise DisplayableException('Not subscribed')

        self.unsubscribe_user(user_id, feed_id)

        if self.get_feed_subscribers_count(feed_id) == 0:
            # Feed is not used anymore. Removing.
            self.delete_feed(feed_id)

    def unsubscribe_user(self, user_id: int, feed_id: int) -> None:
        """Unsubscribe a user from the feed."""
        self.log.debug('unsubscribe_user(user_id=\'%s\', feed_id=\'%s\')', user_id, feed_id)
        self.cur.execute('DELETE FROM subscriptions WHERE feed_id = %s AND user_id = %s', [feed_id, user_id])
        self.conn.commit()

    def is_user_subscribed(self, user_id: int, feed_id: int) -> bool:
        """Check if user subscribed to specific feed."""
        self.log.debug('is_user_subscribed(user_id=\'%s\', feed_id=\'%s\')', user_id, feed_id)
        self.cur.execute('SELECT 1 FROM subscriptions WHERE user_id = %s AND feed_id = %s', [user_id, feed_id])
        row = self.cur.fetchone()
        if row is None:
            return False
        return True

    def delete_feed(self, feed_id: int) -> None:
        """Delete a feed."""
        self.log.debug('delete_feed(feed_id=\'%s\')', feed_id)
        self.cur.execute('DELETE FROM feeds WHERE id = %s', [feed_id])
        self.conn.commit()

    def get_feed_subscribers_count(self, feed_id: int) -> int:
        """Count feed subscribers."""
        self.log.debug('get_feed_subscribers_count(feed_id=\'%s\')', feed_id)
        self.cur.execute('SELECT COUNT(user_id) AS amount_subscribers FROM subscriptions WHERE feed_id = %s', [feed_id])
        row = self.cur.fetchone()
        return row['amount_subscribers']

    def find_feed_subscribers(self, feed_id: int) -> list[int]:
        """Return feed subscribers"""
        self.log.debug('find_feed_subscribers(feed_id=\'%s\')', feed_id)
        self.cur.execute('SELECT telegram_id FROM users WHERE id IN (SELECT user_id FROM subscriptions WHERE feed_id = %s)',
                         [feed_id])
        subscribers = self.cur.fetchall()
        return list(map(lambda x: x['telegram_id'], subscribers))

    def find_feeds(self) -> list[dict]:
        """Get a list of feeds."""
        self.log.debug('find_feeds()')
        self.cur.execute('SELECT * FROM feeds')
        return self.__dictrow_to_dict_list(self.cur.fetchall())

    def find_user_feeds(self, user_id: int) -> list[dict]:
        """Return a list of feeds the user is subscribed to."""
        self.log.debug('find_user_feeds(user_id=\'%s\')', user_id)
        self.cur.execute('SELECT * FROM feeds WHERE id IN (SELECT feed_id FROM subscriptions WHERE user_id = %s)',
                         [user_id])
        return self.__dictrow_to_dict_list(self.cur.fetchall())

    def find_feed_items(self, feed_id: int) -> list[dict]:
        """Get last feed items."""
        self.log.debug('find_feed_items(feed_id=\'%s\')', feed_id)
        self.cur.execute('SELECT * FROM feeds_last_items WHERE feed_id = %s', [feed_id])
        return self.__dictrow_to_dict_list(self.cur.fetchall())

    def find_feed_items_urls(self, feed_id: int) -> list[str]:
        """Return urls last feed items"""
        self.log.debug('find_feed_items_urls(feed_id=\'%s\')', feed_id)
        items = self.find_feed_items(feed_id)
        if not items:
            return []
        return list(map(lambda x: x['url'], items))

    def update_feed_items(self, feed_id: int, new_items: list[FeedItem]) -> None:
        """Replace last feed items with a list items that receive."""
        self.log.debug('update_feed_items(feed_id=\'%s\', new_items=list(%d))', feed_id, len(new_items))
        for i, _ in enumerate(new_items):
            new_items[i] = [feed_id, new_items[i].url, new_items[i].guid]
        self.cur.execute('DELETE FROM feeds_last_items WHERE feed_id = %s', [feed_id])
        self.cur.executemany(
            'INSERT INTO feeds_last_items (feed_id, url, guid) VALUES (%s, %s, %s)', new_items)
        self.conn.commit()

    def __migrate(self, dsn: str) -> None:
        """Migrate or initialize the database schema"""
        self.log.debug(f'Database.__migrate(dsn={dsn})')
        backend = get_backend(dsn)
        migrations = read_migrations('./migrations')

        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))

    @staticmethod
    def __dictrow_to_dict_list(rows: list[DictRow]) -> list[dict]:
        """Convert list of DictRows to list of dicts"""
        return list(map(dict, rows))
