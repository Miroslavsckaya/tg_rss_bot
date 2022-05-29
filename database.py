import sqlite3
"""
Classes:
Database - implement intercaction with the database.
"""

class Database():
    """Implement intercaction with the database."""

    def __init__(self, path: str) -> None:
        """Create a database file if not exists."""
        self.conn = sqlite3.connect(path)
        self.cur = self.conn.cursor()
        self.cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER, telegram_id NUMERIC NOT NULL UNIQUE, PRIMARY KEY(id))')
        self.cur.execute('CREATE TABLE IF NOT EXISTS feeds (id INTEGER, url TEXT NOT NULL UNIQUE, PRIMARY KEY(id))')
        self.cur.execute('CREATE TABLE IF NOT EXISTS subscriptions (user_id INTEGER, feed_id INTEGER, UNIQUE (user_id, feed_id), FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(feed_id) REFERENCES feeds(id))')
        self.cur.execute('CREATE TABLE IF NOT EXISTS feeds_last_items (feed_id INTEGER, url TEXT NOT NULL UNIQUE, title TEXT, description TEXT, date NUMERIC, FOREIGN KEY(feed_id) REFERENCES feeds(id))')

    def add_user(self, telegram_id: str) -> int:
        """Add a user's telegram id to the database and return its database id."""
        self.cur.execute('INSERT INTO users (telegram_id) VALUES (?)', [telegram_id])
        self.conn.commit()
        return self.cur.lastrowid

    def find_user(self, telegram_id: str) -> int | None:
        """Get a user's telegram id and return its database id."""
        self.cur.execute('SELECT id FROM users WHERE telegram_id = ?', [telegram_id])
        row = self.cur.fetchone()
        if row is None:
            return None
        return row[0]

    def add_feed(self, url: str) -> int:
        """Add a feed to the database and return its id."""
        self.cur.execute('INSERT INTO feeds (url) VALUES (?)', [url])
        self.conn.commit()
        return self.cur.lastrowid

    def subscribe_user(self, user_id: int, feed_id: int) -> None:
        """Subscribe a user to the feed."""
        self.cur.execute('INSERT INTO subscriptions (user_id, feed_id) VALUES (?, ?)', [user_id, feed_id])
        self.conn.commit()

    def unsubscribe_user(self, user_id: int, feed_id: int) -> None:
        """Unsubscribe a user from the feed."""
        self.cur.execute('DELETE FROM subscriptions WHERE feed_id = ? AND user_id = ?', [feed_id, user_id])
        self.conn.commit()

    def delete_feed(self, feed_id: int) -> None:
        """Delete a feed."""
        self.cur.execute('DELETE FROM feeds WHERE id = ?', [feed_id])
        self.conn.commit()

    def find_feeds(self) -> list:
        """Get a list of feeds."""
        self.cur.execute('SELECT * FROM feeds')
        return self.cur.fetchall()

    def find_user_feeds(self, user_id: int) -> list:
        """Return a list of feeds the user is subscribed to."""
        self.cur.execute('SELECT * FROM feeds WHERE id IN (SELECT feed_id FROM subscriptions WHERE user_id = ?)', [user_id])
        return self.cur.fetchall()

    def find_feed_items(self, feed_id: int) -> list:
        """Get last feed items."""
        self.cur.execute('SELECT * FROM feeds_last_items WHERE feed_id = ?', [feed_id])
        return self.cur.fetchall()

    def update_feed_items(self, feed_id: int, new_items: list) -> None:
        """Replace last feed items with a list items that receive."""
        for i in range(len(new_items)):
            new_items[i] = (feed_id,) + new_items[i]

        self.cur.execute('DELETE FROM feeds_last_items WHERE feed_id = ?', [feed_id])
        self.cur.executemany('INSERT INTO feeds_last_items (feed_id, url, title, description, date) VALUES (?, ?, ?, ?, ?)', new_items)
        self.conn.commit()
