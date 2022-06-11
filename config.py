from os import environ
from os.path import join, dirname
from enum import Enum
from dotenv import load_dotenv
load_dotenv(join(dirname(__file__), '.env'))


class ServerConfig(str, Enum):
    HOST = environ.get('HOST') or '127.0.0.1'
    PORT = environ.get('PORT') or '8080'


class UM34CConfig(str, Enum):
    MACADDRESS = environ.get('MACADDRESS') or ''