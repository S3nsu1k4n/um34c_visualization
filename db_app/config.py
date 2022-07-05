from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = 'sqlite:///./sql_app.db'

    class Config:
        env_file = '.env'


def get_settings():
    return Settings()