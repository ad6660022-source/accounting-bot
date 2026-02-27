"""
Загрузка настроек из .env через pydantic-settings.
Все параметры читаются из переменных окружения или файла .env.
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

    # ── Telegram ──────────────────────────────────────────────────────────────
    telegram_bot_token: str

    # ── База данных ───────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://postgres:secret@localhost:5432/accounting_bot"
    )

    @property
    def async_database_url(self) -> str:
        """Гарантирует использование asyncpg-драйвера."""
        url = self.database_url.strip()
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # ── Администраторы (Telegram ID через запятую) ────────────────────────────
    admin_ids: str = ""

    # ── Mini App / Web ────────────────────────────────────────────────────────
    # URL Mini App (нужен HTTPS для Telegram). На Railway выставляется автоматически.
    webapp_url: str = "https://your-app.up.railway.app"
    # Порт FastAPI-сервера (Railway использует PORT из окружения)
    port: int = 8000

    # ── Безопасность ──────────────────────────────────────────────────────────
    # Код для получения прав администратора (/start ADMIN_CODE)
    admin_invite_code: str = "ACC-ADMIN-2025"

    @property
    def admin_ids_list(self) -> List[int]:
        """Парсит строку 'id1,id2,id3' в список целых чисел."""
        return [
            int(x.strip())
            for x in self.admin_ids.split(",")
            if x.strip().isdigit()
        ]


# Синглтон — импортировать как: from backend.config import settings
settings = Settings()
