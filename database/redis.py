"""Redis-клиент: кэш, FSM, антиспам, временные блокировки.

В режиме локальной разработки на SQLite Redis необязателен —
все потребители корректно деградируют до in-memory аналогов.
"""
from __future__ import annotations

from redis.asyncio import Redis

from config import get_settings

_redis: Redis | None = None


def init_redis() -> Redis | None:
    """Инициализирует Redis-клиент. Возвращает None, если Redis недоступен."""
    global _redis
    settings = get_settings()
    if settings.is_sqlite:
        return None
    try:
        _redis = Redis.from_url(settings.redis_dsn, decode_responses=True)
    except Exception:  # noqa: BLE001 — Redis не критичен для MVP
        _redis = None
    return _redis


def get_redis() -> Redis | None:
    return _redis


async def close_redis() -> None:
    if _redis is not None:
        await _redis.aclose()


async def cache_get(key: str) -> str | None:
    if _redis is None:
        return None
    return await _redis.get(key)


async def cache_set(key: str, value: str, ttl: int = 300) -> None:
    if _redis is None:
        return
    await _redis.set(key, value, ex=ttl)
