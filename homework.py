import logging
from os import getenv
from sys import stdout
from time import time

from dotenv import load_dotenv
from requests import get
from telegram import Bot
from telegram.ext import Updater

from .exceptions import ChatIdError, TokenError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='homework.log',
    format='%(asctime)s, %(levelname)s, %(lineno)s, %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=stdout)
logger.addHandler(handler)

PRACTICUM_TOKEN = getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Checks if everything's correct with tokens, etc."""
    if PRACTICUM_TOKEN is None:
        error = TokenError('PRACTICUM_TOKEN returned None! Secrets expected')
        logger.critical(error)
    if TELEGRAM_TOKEN is None:
        error = TokenError('TELEGRAM_TOKEN returned None! Secrets expected')
        logger.critical(error)
    if TELEGRAM_CHAT_ID is None:
        error = ChatIdError('TELEGRAM_CHAT_ID returned None! Secrets expected')
        logger.critical(error)


def send_message(bot, message):
    """Sends a message to bot."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.debug()
    except Exception as error:
        logger.error(error)


def get_api_answer(timestamp):
    """Gets a response from Yandex's homework API in JSON."""
    try:
        payload = {'from_date': timestamp}
        json_response = get(ENDPOINT, headers=HEADERS, params=payload).json()
        return json_response
    except Exception as error:
        logger.error(error)


def check_response(response):
    """Checks resposne from get_api_answer function."""
    if response.get('homeworks') is None:
        error = KeyError(
            'Something wrong with "homeworks" key in API response!'
        )
        logger.error(error)
    if response.get('current_time') is None:
        error = KeyError(
            '''Something wrong with "current_time" key in API response!'''
        )
        logger.error(error)


def parse_status(homework):
    """Returns homeworks's name and verdict."""
    homework_name = homework[0].get('homework_name')
    verdict = HOMEWORK_VERDICTS[homework[0].get('status')]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Main logic of the bot."""
    bot = Bot(token=TELEGRAM_TOKEN)
    updater = Updater(token=TELEGRAM_TOKEN)
    timestamp = int(time())
    while True:
        updater.start_polling(RETRY_PERIOD)
        updater.idle()
        try:
            check_tokens()
            api_answer = get_api_answer(timestamp=timestamp)
            last_homework = api_answer.get('homeworks')
            message = parse_status(homework=last_homework)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
        send_message(bot, message)


if __name__ == '__main__':
    main()
