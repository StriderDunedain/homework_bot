import logging
import time
from http import HTTPStatus
from os import getenv
from sys import stdout

import requests
from dotenv import load_dotenv
import telegram

from exceptions import ChatIdError, HomeworkError, ResponseError, TokenError

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    format='%(asctime)s [%(levelname)s] |%(lineno)s| > %(message)s',
    filemode='w'
)

logger = logging.getLogger(__name__)
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
        logger.critical(msg=error)
        exit()
    if TELEGRAM_TOKEN is None:
        error = TokenError('TELEGRAM_TOKEN returned None! Secrets expected')
        logger.critical(msg=error)
        exit()
    if TELEGRAM_CHAT_ID is None:
        error = ChatIdError('TELEGRAM_CHAT_ID returned None! Secrets expected')
        logger.critical(msg=error)
        exit()


def send_message(bot, message):
    """Sends a message to bot."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.debug('''Yay! Everything compiled seamlessly
         (or no) but the message was sent''')
        return message
    except Exception as error:
        logger.error(msg=error)
        return error


def get_api_answer(timestamp):
    """Gets a response from Yandex's homework API in JSON."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as error:
        logger.error(msg=error)
        raise ResponseError(error)

    if response.status_code != HTTPStatus.OK:
        error = 'Response did not return 200'
        logger.error(msg=error)
        raise ResponseError(error)
    return response.json()


def check_response(response):
    """Checks resposne from get_api_answer function."""
    if not isinstance(response, dict):
        raise TypeError('Response is not dict')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('`homeworks` key is not a list, expected list')
    if response.get('homeworks') is None:
        error = KeyError(
            'Something wrong with `homeworks` key in API response!'
        )
        logger.error(msg=error)
        raise error
    if response.get('current_date') is None:
        error = KeyError(
            '''Something wrong with `current_date` key in API response!'''
        )
        logger.error(msg=error)


def parse_status(homework):
    """Returns homeworks's name and verdict."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise HomeworkError('`homework` is None')

    status = homework.get('status')
    if status is None:
        raise HomeworkError('`Status` is None')

    if status not in HOMEWORK_VERDICTS:
        raise KeyError('No such status in HOMEWORK_VERDICTS')

    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Main logic of the bot."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    last_message = ''
    while True:
        try:
            # returns a dict
            api_response = get_api_answer(timestamp=timestamp)
            check_response(api_response)
            all_homeworks = api_response.get('homeworks')
            # gets last homework (i.e. first element)
            last_homework = all_homeworks[0]
            message = parse_status(homework=last_homework)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(msg=error)
        if last_message != message:
            last_message = send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
