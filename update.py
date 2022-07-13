import logging
import os
from dotenv import load_dotenv

from rss import RssReader
from update_manager import UpdateManager
from database import Database
from telegram import Notifier


load_dotenv()

token = os.getenv('RSSBOT_TG_TOKEN')
dsn = os.getenv('RSSBOT_DSN')
log_level = os.getenv('LOG_LEVEL', 'INFO')

print('Starting the updater with logging level', log_level.upper())
logging.basicConfig(
    level=log_level.upper(),
    format='%(asctime)s: <%(name)s> [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

db = Database(dsn, logging.getLogger('Database'))
notifier = Notifier(token, logging.getLogger('Notifier'))
rss_reader = RssReader(logging.getLogger('RssReader'))

updater = UpdateManager(db, notifier, rss_reader, logging.getLogger('UpdateManager'))
updater.update()
