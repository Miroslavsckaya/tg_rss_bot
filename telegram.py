import time
from logging import Logger
from bleach.sanitizer import Cleaner
from telebot import TeleBot
from telebot.handler_backends import BaseMiddleware
from telebot.types import Message
import validators

from database import Database
from exceptions import DisplayableException
from rss import FeedItem


class CommandProcessor:
    """Processes user input and dispatches the data to other services."""

    def __init__(self, token: str, database: Database, logger: Logger):
        self.log = logger
        self.log.debug(
            'CommandProcessor.__init__(token=\'%s\', database=%s, logger=%s)', token[:8] + '...', database, logger
        )
        if token is None or len(token) == 0:
            raise ValueError("Token should not be empty")
        self.bot: TeleBot = TeleBot(token, use_class_middlewares=True)
        self.bot.setup_middleware(UserAuthMiddleware(database, logger))
        self.bot.setup_middleware(ExceptionHandlerMiddleware(self.bot, logger))
        self.database: Database = database

    def run(self):
        """Run a bot and poll for new messages indefinitely."""
        self.log.debug('Registering handlers')
        self.bot.register_message_handler(commands=['add'], callback=self.__add_feed)
        self.bot.register_message_handler(commands=['list'], callback=self.__list_feeds)
        self.bot.register_message_handler(commands=['del'], callback=self.__delete_feed)
        self.bot.register_message_handler(commands=['help', 'start'], callback=self.__command_help)
        self.bot.register_message_handler(callback=self.__command_help)

        self.log.info('Starting to poll the servers')
        self.bot.infinity_polling()

    def __command_help(self, message: Message, data: dict):
        # pylint: disable=unused-argument
        self.log.debug('__command_help(message=\'%s\', data=\'%s\')', message, data)
        self.bot.reply_to(
            message,
            'Supported commands:\n'
            '  /add <feed url> - Add new feed\n'
            '  /list - List currently added feeds\n'
            '  /del <feed url> - Remove feed\n'
            '  /help - Get this help message'
        )

    def __add_feed(self, message: Message, data: dict):
        self.log.debug('__add_feed(message=\'%s\', data=\'%s\')', message, data)
        args = message.text.split()
        if len(args) < 2:
            raise DisplayableException('Feed URL should be specified')

        url = str(args[1])
        self.log.info('User %s requested to subscribe to %s', data['user_id'], url)
        if not self.__is_url_valid(url):
            raise DisplayableException('Invalid feed URL')

        self.database.subscribe_user_by_url(data['user_id'], url)
        self.log.info('Subscription added')

        self.bot.reply_to(message, 'Successfully subscribed to feed.')

    def __list_feeds(self, message: Message, data: dict):
        self.log.debug('__list_feeds(message=\'%s\', data=\'%s\')', message, data)
        feeds = self.database.find_user_feeds(data['user_id'])

        feed_list = ''
        for index, feed in enumerate(feeds, start=1):
            feed_list += str(index) + ': ' + f"{feed['url']}" + '\n'

        self.bot.reply_to(message, 'Your feeds:\n' + feed_list)

    def __delete_feed(self, message: Message, data: dict):
        self.log.debug('__delete_feed(message=\'%s\', data=\'%s\')', message, data)
        args = message.text.split()
        if len(args) < 2:
            raise DisplayableException('Feed URL should be specified')

        url = str(args[1])
        self.log.info('User %s requested to unsubscribe from %s', data['user_id'], url)
        if not self.__is_url_valid(url):
            raise DisplayableException('Invalid feed URL')

        self.database.unsubscribe_user_by_url(data['user_id'], url)
        self.log.info('Subscription removed')

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

    # https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
    BATCH_LIMIT: int = 25

    sent_counter: int = 0

    def __init__(self, token: str, logger: Logger):
        self.log = logger
        self.log.debug('Notifier.__init__(token=\'%s\', logger=%s)', token[:8] + '...', logger)
        self.bot: TeleBot = TeleBot(token)
        self.html_sanitizer: Cleaner = Cleaner(
            tags=['b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'tg-spoiler', 'a', 'code', 'pre'],
            attributes={"a": ["href", "title"]},
            protocols=['http', 'https'],
            strip=True,
        )

    def send_updates(self, chat_ids: list[int], updates: list[FeedItem], feed_title: str):
        """Send notification about new items to the user"""
        self.log.debug(
            'send_updates(chat_ids=list(%d), updates=list(%d), feed_title=\'%s\')',
            len(chat_ids), len(updates), feed_title
        )
        if not updates:
            self.log.debug('No updates to send')
            return

        self.log.debug('%d updates to send to %d chats', len(updates), len(chat_ids))
        for chat_id in chat_ids:
            self.log.debug('Processing chat_id=%s', chat_id)
            self.__count_request_and_wait()
            self.bot.send_message(
                chat_id=chat_id,
                text=f'Updates from the {feed_title} feed:'
            )

            for update in updates:
                self.__count_request_and_wait()
                self.__send_update(chat_id, update)

    def __send_update(self, chat_id: int, update: FeedItem):
        self.log.debug('__send_update(chat_id=\'%s\', update=\'%s\')', chat_id, update)
        self.bot.send_message(
            chat_id=chat_id,
            text=self.__format_message(update),
            parse_mode='HTML'
        )

    def __count_request_and_wait(self):
        self.log.debug('__count_request_and_wait()')
        if self.sent_counter >= self.BATCH_LIMIT:
            self.log.debug('Requests limit exceeded, sleeping for a second')
            time.sleep(1)
            self.log.debug('Resetting counter')
            self.sent_counter = 0
        self.sent_counter += 1

    def __format_message(self, item: FeedItem) -> str:
        return (
            f"<strong><a href=\"{item.url}\">{item.title}</a></strong>\n"
            f"{item.date.strftime('%m.%d.%Y %H:%M')}\n\n"
            f"{self.__sanitize_html(item.description)}"
        )

    def __sanitize_html(self, html: str) -> str:
        if not html:
            return ''
        return self.html_sanitizer.clean(html)


class UserAuthMiddleware(BaseMiddleware):
    """Transparently authenticates and registers the user if needed."""

    def __init__(self, database: Database, logger: Logger):
        self.log: Logger = logger
        self.log.debug('UserAuthMiddleware.__init__(database=%s, logger=%s)', database, logger)
        super().__init__()
        self.update_types = ['message']
        self.database: Database = database

    def pre_process(self, message: Message, data: dict):
        """Pre-process update, find user and add it's ID to the handler data dictionary."""
        self.log.debug('UserAuthMiddleware.pre_process()')
        data['user_id'] = self.__find_or_register_user(message)

    def post_process(self, message: Message, data: dict, exception):
        """Post-process update."""

    def __find_or_register_user(self, message: Message) -> int:
        self.log.debug('__find_or_register_user()')
        telegram_id = message.from_user.id
        self.log.debug('Telegram chat_id=%s', telegram_id)

        user_id = self.database.find_user(telegram_id)
        self.log.debug('Database user ID is \'%s\'', user_id)
        if user_id is None:
            return self.database.add_user(telegram_id)
        return user_id


class ExceptionHandlerMiddleware(BaseMiddleware):
    """Sends messages to the user on exception."""

    def __init__(self, bot: TeleBot, logger: Logger):
        self.log: Logger = logger
        self.log.debug('ExceptionHandlerMiddleware.__init__(bot=%s, logger=%s)', bot, logger)
        super().__init__()
        self.update_types = ['message']
        self.bot: TeleBot = bot

    def pre_process(self, message: Message, data: dict):
        """Pre-process update."""

    # pylint: disable=W0613
    def post_process(self, message: Message, data: dict, exception: Exception | None):
        """Post-process update. Send user an error notification."""
        self.log.debug('ExceptionHandlerMiddleware.post_process()')

        if exception is None:
            return

        self.log.exception('Exception caught during message processing: %s', exception)
        if isinstance(exception, DisplayableException):
            self.bot.reply_to(message, 'Error: ' + str(exception))
        else:
            self.bot.reply_to(message, 'Something went wrong. Please try again (maybe later).')
