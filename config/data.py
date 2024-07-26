import configparser
from pathlib import Path

from language import en, ru, el

# Absolut path
dir_path = Path.cwd().parent
print(dir_path)
path = Path(dir_path, 'config', 'config.ini')
print(path)
config = configparser.ConfigParser()
config.read(path)

# Constants
DB_PASSWORD = config['Database']['db_password']
DB_LOGIN = config['Database']['db_login']
DB_NAME = config['Database']['db_name']

DATABASE_URL = f"postgresql+asyncpg://{DB_LOGIN}:{DB_PASSWORD}@localhost/{DB_NAME}"

BOT_TOKEN = config['Telegram']['bot_token']
BOT_USERNAME = config['Telegram']['bot_username']
ADMIN = int(config['Telegram']['admin_1'])

WAIT_BF_DEL_CHART_PNG = 3  # second

LANGUAGES = {
    'en': en,
    'ru': ru,
    'el': el,
}
DEFAULT_LANGUAGE = 'en'

SLEEP = 60 * 60 * 3  # How often will check db and sent msgs (sec) = seconds * minutes * hours
TIME_SEND_MSG = 60 * 60 * 3  # Send msgs every 3 h for usual user
TIME_SEND_VIP_MSG = 60 * 5  # Send msgs every 5 min for vip
