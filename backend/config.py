"""
Загрузка настроек из .env через pydantic-settings.
"""

from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str

    database_url: str = (
        "postgresql+asyncpg://postgres:secret@localhost:5432/accounting_bot"
    )

    @property
    def async_database_url(self) -> str:
        url = self.database_url.strip()
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    admin_ids: str = ""
    webapp_url: str = "https://your-app.up.railway.app"
    port: int = 8000
    admin_invite_code: str = "ACC-ADMIN-2025"

    # Подписки (Telegram Stars)
    pro_price_stars: int = 199    # ~362 руб
    business_price_stars: int = 499  # ~908 руб

    @property
    def admin_ids_list(self) -> List[int]:
        return [
            int(x.strip())
            for x in self.admin_ids.split(",")
            if x.strip().isdigit()
        ]


settings = Settings()
