"""Базовый репозиторий: общие CRUD-операции."""
from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository:
    """Обёртка над сессией SQLAlchemy с типовыми операциями."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, obj: ModelT, *, flush: bool = True) -> ModelT:
        """Добавляет объект; при flush=True сразу получает автоинкрементный id."""
        self.session.add(obj)
        if flush:
            await self.session.flush()
        return obj

    async def get(self, model: type[ModelT], pk: Any) -> ModelT | None:
        return await self.session.get(model, pk)

    async def delete(self, obj: ModelT, *, flush: bool = True) -> None:
        await self.session.delete(obj)
        if flush:
            await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, obj: ModelT) -> ModelT:
        await self.session.refresh(obj)
        return obj

    async def scalar(self, stmt) -> Any:
        """Выполняет SELECT и возвращает первое скалярное значение."""
        return await self.session.scalar(stmt)

    async def scalars(self, stmt) -> list[Any]:
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def first(self, model: type[ModelT], **filters: Any) -> ModelT | None:
        stmt = select(model).filter_by(**filters).limit(1)
        return await self.session.scalar(stmt)
