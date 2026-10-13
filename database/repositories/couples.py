"""Репозиторий пар. Содержит логику кодов приглашений и настроек модулей."""
from __future__ import annotations

import secrets

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Couple
from database.repositories.base import BaseRepository

# Настройки пары по умолчанию: каждый модуль можно включать/выключать
DEFAULT_SETTINGS: dict = {
    "modules": {
        "reminders": True,
        "shopping": True,
        "budget": True,
        "mood": True,
        "gratitude": True,
        "dates": True,
        "romance": True,
        "analytics": True,
        "memories": True,
        "games": True,
        "achievements": True,
    },
    "mood_poll_hour": 21,  # час ежедневного опроса настроения
    "challenge_hour": 9,    # час выдачи челленджа дня
    "privacy": {
        "mood_visible": True,
        "transactions_visible": True,
    },
}


class CouplesRepository(BaseRepository):
    async def get_by_id(self, couple_id: int) -> Couple | None:
        return await self.get(Couple, couple_id)

    async def get_by_invite(self, invite_code: str) -> Couple | None:
        stmt = select(Couple).where(Couple.invite_code == invite_code)
        return await self.session.scalar(stmt)

    async def create(self, user1_id: int) -> Couple:
        """Создаёт пару с первым участником и уникальным кодом приглашения."""
        couple = Couple(
            user1_id=user1_id,
            invite_code=self._gen_code(),
            settings=DEFAULT_SETTINGS.copy(),
        )
        self.session.add(couple)
        await self.session.flush()
        return couple

    async def join(self, couple: Couple, user_id: int) -> Couple:
        """Присоединяет второго участника (идемпотентно)."""
        if couple.user2_id is None:
            couple.user2_id = user_id
            await self.session.flush()
        return couple

    async def is_full(self, couple: Couple) -> bool:
        return couple.user2_id is not None

    async def regenerate_invite(self, couple: Couple) -> str:
        code = self._gen_code()
        couple.invite_code = code
        await self.session.flush()
        return code

    async def set_setting(self, couple: Couple, path: str, value) -> Couple:
        """Устанавливает настройку по dotted-пути, например 'modules.budget'."""
        settings = dict(couple.settings or {})
        parts = path.split(".")
        node = settings
        for key in parts[:-1]:
            node = node.setdefault(key, {})
        node[parts[-1]] = value
        couple.settings = settings
        await self.session.flush()
        return couple

    async def get_setting(self, couple: Couple, path: str, default=None):
        node = couple.settings or {}
        for key in path.split("."):
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    async def set_name(self, couple: Couple, name: str) -> Couple:
        couple.name = name
        await self.session.flush()
        return couple

    async def set_avatar(self, couple: Couple, url: str | None) -> Couple:
        couple.avatar_url = url
        await self.session.flush()
        return couple

    def _gen_code(self) -> str:
        """Генерирует читаемый 8-символьный код (без похожих символов)."""
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "".join(secrets.choice(alphabet) for _ in range(8))
