import configparser
from pathlib import Path

from language import en, ru, el

# Absolut path
dir_path = Path.cwd()
path = Path(dir_path, 'config', 'config.ini')
config = configparser.ConfigParser()
config.read(path)

# Constants
DB_PASSWORD = config['Database']['db_password']
DB_LOGIN = config['Database']['db_login']
DB_NAME = config['Database']['db_name']

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

SLEEP = 300  # How often will be check db and sent msgs (sec)
