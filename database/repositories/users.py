"""Репозиторий пользователей."""
from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.repositories.base import BaseRepository


class UsersRepository(BaseRepository):
    async def get_by_id(self, user_id: int) -> User | None:
        return await self.get(User, user_id)

    async def upsert(
        self,
        user_id: int,
        *,
        username: str | None,
        first_name: str,
        timezone: str,
        language: str,
    ) -> User:
        """Возвращает существующего пользователя или создаёт нового."""
        user = await self.get_by_id(user_id)
        if user is None:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                timezone=timezone,
                language=language,
            )
            self.session.add(user)
            await self.session.flush()
        else:
            # Актуализируем имя/username при каждом заходе
            user.username = username or user.username
            user.first_name = first_name or user.first_name
        return user

    async def set_couple(self, user_id: int, couple_id: int | None) -> None:
        await self.session.execute(
            update(User).where(User.user_id == user_id).values(couple_id=couple_id)
        )

    async def set_timezone(self, user_id: int, timezone: str) -> None:
        await self.session.execute(
            update(User).where(User.user_id == user_id).values(timezone=timezone)
        )

    async def set_language(self, user_id: int, language: str) -> None:
        await self.session.execute(
            update(User).where(User.user_id == user_id).values(language=language)
        )

    async def get_partner(self, user: User) -> User | None:
        """Партнёр пользователя внутри пары."""
        if not user.couple_id:
            return None
        stmt = select(User).where(
            User.couple_id == user.couple_id, User.user_id != user.user_id
        )
        return await self.session.scalar(stmt)

    async def get_by_couple(self, couple_id: int) -> list[User]:
        stmt = select(User).where(User.couple_id == couple_id)
        res = await self.session.scalars(stmt)
        return list(res.all())
