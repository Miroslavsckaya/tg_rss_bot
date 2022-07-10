import logging
import os
from dotenv import load_dotenv

from database import Database
from telegram import CommandProcessor


load_dotenv()

token = os.getenv('TELEGRAM_TOKEN')
db_path = os.getenv('DATABASE_PATH', './bot.db')
log_level = os.getenv('LOG_LEVEL', 'INFO')

print('Starting the bot with logging level', log_level.upper())
logging.basicConfig(
    level=log_level.upper(),
    format='%(asctime)s: <%(name)s> [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

db = Database(db_path, logging.getLogger('Database'))
bot = CommandProcessor(token, db, logging.getLogger('CommandProcessor'))

bot.run()
