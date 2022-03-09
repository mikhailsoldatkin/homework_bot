import datetime
import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

import requests
import telegram
from dotenv import load_dotenv

from exceptions import BotTypeError, BotKeyError, ResponseError
from exceptions import SendMessageError


PERIOD_IN_DAYS = 30
PERIOD = int(datetime.timedelta(days=PERIOD_IN_DAYS).total_seconds())

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
)
handler.setFormatter(formatter)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Посылает сообщение о статусе проверки работы в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение отправлено!')
    except SendMessageError as error:
        message = f'Сообщение не отправлено: {error}'
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        raise error


def get_api_answer(current_timestamp):
    """Выполняет запрос к API. Возвращает ответ, преобразовав его из формата
    JSON в словарь Python."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise ResponseError('эндпойнт API "Практикум.Домашка" не доступен!')
    return response.json()


def check_response(response):
    """Проверяет ответ API на тип данных Python: словарь. Возвращает список
    домашних работ."""
    if not isinstance(response, dict):
        raise BotTypeError('response', 'dict')
    try:
        homework_list = response.get('homeworks')
        if not isinstance(homework_list, list):
            raise BotTypeError('homework_list', 'list')
        return homework_list
    except KeyError:
        raise BotKeyError('response', 'homeworks')


def parse_status(homework):
    """Извлекает статус из конкретной домашней работы. Возвращает
    подготовленную для отправки в Telegram строку."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES.get(homework_status)

    if not homework_status:
        raise BotKeyError('homework', 'homework_status')

    if not homework_name:
        raise BotKeyError('homework', 'homework_name')

    if not verdict:
        raise BotKeyError('HOMEWORK_STATUSES', 'homework_status')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет наличие всех нужных переменных окружения (токенов)."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    else:
        logger.critical('отсутствуют переменные окружения!')
        SystemExit()


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - PERIOD
    previous_status = ''
    previous_error = Exception

    check_tokens()

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            current_status = parse_status(homeworks[0])
            if current_status != previous_status:
                send_message(bot, current_status)
                previous_status = current_status
            else:
                logger.debug('Статус проверки работы не изменился.')
            time.sleep(RETRY_TIME)

        except Exception as error:
            if previous_error.args == error.args:
                previous_error = error
                logger.debug('Ошибка не устранена')
            else:
                message = f'Сбой в работе программы: {error}'
                logger.error(message)
                send_message(bot, message)
                previous_error = error
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
