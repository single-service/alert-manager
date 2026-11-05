from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    tg_token_client: str
    webhook_base: str                # https://bots.example.com
    bot_secret: str                  # общий secret для телеграма
    AUTH_TOKEN: str
    TARGET_CHAT_ID: str
    TELEGRAM_PROXY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()              # берёт из .env
