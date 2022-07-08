import os
from rss import RssReader
from update_manager import UpdateManager
from database import Database
from telegram import Notifier

token = os.getenv('TELEGRAM_TOKEN')
db_path = os.getenv('DATABASE_PATH')

db = Database(db_path)
notifier = Notifier(token)
rss_reader = RssReader()

updater = UpdateManager(db, notifier, rss_reader)
updater.update()
