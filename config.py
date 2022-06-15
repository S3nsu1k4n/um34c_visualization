from os import environ
from os.path import join, dirname
from pydantic import BaseSettings
from dotenv import load_dotenv
load_dotenv(join(dirname(__file__), '.env'))


class ServerSettings(BaseSettings):
    host = environ.get('HOST') or '127.0.0.1'
    port = environ.get('PORT') or '8080'


class BluetoothSettings(BaseSettings):
    bd_address = environ.get('BD_ADDRESS') or 'xx:xx:xx:xx:xx:xx'
    bl_port = environ.get('BL_PORT') or '1'
    max_attempts: int = environ.get('MAX_ATTEMPTS') or '10'
    attempts_delay: int = environ.get('ATTEMPT_DELAY') or '5000'


class SQLSetting(BaseSettings):
    sqlalchemy_database_url = environ.get('SQLALCHEMY_DATABASE_URL') or 'sqlite:///./sql_app.db'


class Settings(BaseSettings):
    server = ServerSettings().dict()
    bluetooth = BluetoothSettings().dict()
