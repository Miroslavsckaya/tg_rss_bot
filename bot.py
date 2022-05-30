import logging
import os
from dotenv import load_dotenv

from database import Database
from telegram import CommandProcessor


load_dotenv()

token = os.getenv('TELEGRAM_TOKEN')
db_path = os.getenv('DATABASE_PATH')

db = Database(db_path)
bot = CommandProcessor(token, db)

logging.info("Starting Telegram bot")
bot.run()
