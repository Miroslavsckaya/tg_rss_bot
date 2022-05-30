import time

from telebot import TeleBot
from telebot.handler_backends import BaseMiddleware
from telebot.types import Message
import validators

from database import Database
from exceptions import DisplayableException
from rss import FeedItem


class CommandProcessor:
    """Processes user input and dispatches the data to other services."""

    def __init__(self, token: str, database: Database):
        if token is None or len(token) == 0:
            raise ValueError("Token should not be empty")
        self.bot: TeleBot = TeleBot(token, use_class_middlewares=True)
        self.bot.setup_middleware(UserAuthMiddleware(database))
        self.bot.setup_middleware(ExceptionHandlerMiddleware(self.bot))
        self.database: Database = database

    def run(self):
        """Run a bot and poll for new messages indefinitely."""
        self.bot.register_message_handler(commands=['add'], callback=self.__add_feed)
        self.bot.register_message_handler(commands=['list'], callback=self.__list_feeds)
        self.bot.register_message_handler(commands=['del'], callback=self.__delete_feed)
        self.bot.register_message_handler(commands=['help', 'start'], callback=self.__command_help)
        self.bot.register_message_handler(callback=self.__command_help)

        self.bot.infinity_polling()

    def __command_help(self, message: Message):
        self.bot.reply_to(
            message,
            'Supported commands:\n'
            '  /add <feed url> - Add new feed\n'
            '  /list - List currently added feeds\n'
            '  /del <feed url> - Remove feed\n'
            '  /help - Get this help message'
        )

    def __add_feed(self, message: Message, data: dict):
        args = message.text.split()
        if len(args) < 2:
            raise DisplayableException('Feed URL should be specified')

        url = str(args[1])
        if not self.__is_url_valid(url):
            raise DisplayableException('Invalid feed URL')

        self.database.subscribe_user_by_url(data['user_id'], url)

        self.bot.reply_to(message, 'Successfully subscribed to feed.')

    def __list_feeds(self, message: Message, data: dict):
        feeds = self.database.find_user_feeds(data['user_id'])

        feed_list = ''
        for feed in feeds:
            feed_list += '* ' + str(feed[0]) + ': ' + feed[1] + '\n'

        self.bot.reply_to(message, 'Your feeds:\n' + feed_list)

    def __delete_feed(self, message: Message, data: dict):
        args = message.text.split()
        if len(args) < 2:
            raise DisplayableException('Feed URL should be specified')

        url = str(args[1])
        if not self.__is_url_valid(url):
            raise DisplayableException('Invalid feed URL')

        self.database.unsubscribe_user_by_url(data['user_id'], url)

        self.bot.reply_to(message, 'Unsubscribed.')

    @staticmethod
    def __is_url_valid(url: str) -> bool:
        if not validators.url(url):
            return False

        # For security reasons we should not allow anything except HTTP/HTTPS.
        if not url.startswith(('http://', 'https://')):
            return False
        return True


class Notifier:
    """Sends notifications to users about new RSS feed items."""

    BATCH_LIMIT: int = 30

    sent_counter: int = 0

    def __init__(self, token: str):
        self.bot: TeleBot = TeleBot(token)

    def send_updates(self, chat_ids: list[int], updates: list[FeedItem]):
        """Send notification about new items to the user"""
        for chat_id in chat_ids:
            for update in updates:
                self.__send_update(chat_id, update)
                self.sent_counter += 1
                if self.sent_counter >= self.BATCH_LIMIT:
                    # TODO: probably implement better later
                    time.sleep(1)
                    self.sent_counter = 0

    def __send_update(self, chat_id: int, update: FeedItem):
        self.bot.send_message(
            chat_id=chat_id,
            text=self.__format_message(update),
            parse_mode='HTML'
        )

    @staticmethod
    def __format_message(item: FeedItem) -> str:
        return (
            f"<strong><a href=\"{item.url}\">{item.title}</a></strong>\n\n"
            f"{item.description}"
        )


class UserAuthMiddleware(BaseMiddleware):
    """Transparently authenticates and registers the user if needed."""

    def __init__(self, database: Database):
        super().__init__()
        self.update_types = ['message']
        self.database: Database = database

    def pre_process(self, message: Message, data: dict):
        """Pre-process update, find user and add it's ID to the handler data dictionary."""
        data['user_id'] = self.__find_or_register_user(message)

    def post_process(self, message: Message, data: dict, exception):
        """Post-process update."""

    def __find_or_register_user(self, message: Message) -> int:
        telegram_id = message.from_user.id

        user_id = self.database.find_user(telegram_id)
        if user_id is None:
            return self.database.add_user(telegram_id)
        return user_id


class ExceptionHandlerMiddleware(BaseMiddleware):
    """Sends messages to the user on exception."""

    def __init__(self, bot: TeleBot):
        super().__init__()
        self.update_types = ['message']
        self.bot: TeleBot = bot

    def pre_process(self, message: Message, data: dict):
        """Pre-process update."""

    # pylint: disable=W0613
    def post_process(self, message: Message, data: dict, exception: Exception | None):
        """Post-process update. Send user an error notification."""
        if exception is None:
            return
        if isinstance(exception, DisplayableException):
            self.bot.reply_to(message, 'Error: ' + str(exception))
        else:
            self.bot.reply_to(message, 'Something went wrong. Please try again (maybe later).')
