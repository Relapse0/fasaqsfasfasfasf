"""Инициализация движка БД и фабрики асинхронных сессий.

Используется SQLAlchemy 2.0 (async) + драйвер asyncpg (PostgreSQL)
или aiosqlite (локальная разработка).
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import get_settings


class Base(DeclarativeBase):
    """Базовый класс всех ORM-моделей (для ``Base.metadata`` в Alembic)."""


# Глобальные объекты, заполняются в init_db()
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db() -> AsyncEngine:
    """Создаёт движок и фабрику сессий. Вызывается один раз при старте бота."""
    global _engine, _session_factory
    settings = get_settings()

    kwargs: dict = {"echo": settings.debug, "pool_pre_ping": True}
    if settings.is_sqlite:
        # SQLite не поддерживает пул соединений и pool_pre_ping
        kwargs.pop("pool_pre_ping", None)

    _engine = create_async_engine(settings.postgres_dsn, **kwargs)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_engine() -> AsyncEngine:
    """Возвращает движок (или падает, если БД не инициализирована)."""
    assert _engine is not None, "БД не инициализирована: вызовите init_db()"
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    assert _session_factory is not None, "БД не инициализирована: вызовите init_db()"
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """DI-генератор сессии: открывает и гарантированно закрывает её.

    Используется middleware и планировщиком через ``get_session_factory()``.
    """
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def create_all() -> None:
    """Создаёт таблицы (только для локальной разработки).

    В проде схему накатывает Alembic: ``alembic upgrade head``.
    """
    from database import models  # noqa: F401  — регистрация моделей в metadata

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_db() -> None:
    """Корректно закрывает пул соединений при остановке."""
    if _engine is not None:
        await _engine.dispose()
