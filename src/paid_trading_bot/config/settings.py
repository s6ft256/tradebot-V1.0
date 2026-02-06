from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="development", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    binance_api_key: str | None = Field(default=None, alias="BINANCE_API_KEY")
    binance_api_secret: str | None = Field(default=None, alias="BINANCE_API_SECRET")
    exchange_testnet: bool = Field(default=True, alias="EXCHANGE_TESTNET")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")


settings = Settings()
