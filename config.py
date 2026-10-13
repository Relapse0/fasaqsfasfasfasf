"""Конфигурация приложения через pydantic-settings.

Все значения читаются из переменных окружения с префиксом ``COUPLE_BOT_``
или из файла ``.env`` (см. ``.env.example``).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Центральные настройки бота."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="COUPLE_BOT_",
        extra="ignore",
    )

    # ── Telegram ──────────────────────────────────────────────
    bot_token: str = Field(..., description="Токен бота от @BotFather")

    # ── Базы данных ───────────────────────────────────────────
    postgres_dsn: str = "postgresql+asyncpg://couple:couple@localhost:5432/couple_bot"
    redis_dsn: str = "redis://localhost:6379/0"

    # ── Режим работы ──────────────────────────────────────────
    debug: bool = False
    webhook_enabled: bool = False
    webhook_url: str = ""
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8443
    webhook_path: str = "/webhook"

    # ── Логирование ───────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = "logs/couple_bot.log"

    # ── Локализация / часовые пояса ───────────────────────────
    default_timezone: str = "Europe/Moscow"
    default_language: str = "ru"
    scheduler_timezone: str = "UTC"

    # ── Антиспам ──────────────────────────────────────────────
    throttle_rate: float = 0.5  # минимальный интервал между сообщениями, сек

    # ── Админы ────────────────────────────────────────────────
    admins: list[int] = Field(default_factory=list)

    # ── Бэкапы (S3-совместимое хранилище) ────────────────────
    backup_enabled: bool = False
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "couple-bot-backups"

    # ── Ресурсы ───────────────────────────────────────────────
    assets_dir: str = "assets"
    generated_dir: str = "generated"  # временные PNG/графики

    @property
    def is_sqlite(self) -> bool:
        """True, если используется SQLite (локальная разработка)."""
        return self.postgres_dsn.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Возвращает закэшированный объект настроек (синглтон)."""
    return Settings()
