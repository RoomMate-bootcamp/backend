from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str
    db_echo: bool = False

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    yandex_folder_id: str
    yandex_api_key: str
    telegram_bot_token: str

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
