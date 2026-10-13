"""Сервис геймификации: очки, уровни, достижения."""
from __future__ import annotations

from database.repositories.achievements import AchievementsRepository, PointsRepository
from utils import emoji as e

# Каталог достижений: code -> (название, описание, порог очков)
ACHIEVEMENTS: dict[str, tuple[str, str, int]] = {
    "first_step": ("Первый шаг", "Создали пару", 0),
    "first_reminder": ("⏰ Пунктуальные", "Создали первое напоминание", 10),
    "budget_100": ("💳 Финансисты", "Накопили 100 очков бюджета", 100),
    "mood_week": ("🌤️ В контакте", "Отмечали настроение 7 дней подряд", 50),
    "gratitude_10": ("💌 Благодарные", "10 благодарностей", 30),
    "memory_10": ("🖼️ Хранители", "Сохранили 10 воспоминаний", 30),
}


class GamificationService:
    def __init__(self, session) -> None:
        self.session = session

    async def add_points(
        self, *, couple_id: int, amount: int, reason: str, user_id: int | None = None
    ) -> int:
        """Начисляет очки и возвращает новый баланс."""
        repo = PointsRepository(self.session)
        await repo.add(couple_id=couple_id, amount=amount, reason=reason, user_id=user_id)
        return await repo.balance(couple_id)

    async def balance(self, couple_id: int) -> int:
        return await PointsRepository(self.session).balance(couple_id)

    async def level(self, couple_id: int) -> tuple[int, int, int]:
        """(уровень, очки на уровне, прогресс 0..100)"""
        points = await self.balance(couple_id)
        level = points // 100  # 100 очков = 1 уровень
        in_level = points % 100
        progress = in_level  # 0..99 → нормируем в 0..100
        return level, in_level, progress

    async def check_achievements(self, couple_id: int, *, trigger: str) -> list[str]:
        """Проверяет и разблокирует достижения. Возвращает новые коды."""
        repo = AchievementsRepository(self.session)
        new: list[str] = []
        for code, (title, desc, threshold) in ACHIEVEMENTS.items():
            balance = await self.balance(couple_id)
            if balance >= threshold and await repo.unlock(couple_id, code):
                new.append(title)
        return new

    async def list_achievements(self, couple_id: int) -> list[dict]:
        """Все достижения с флагом unlocked."""
        repo = AchievementsRepository(self.session)
        unlocked = {a.code for a in await repo.list_for_couple(couple_id)}
        result = []
        for code, (title, desc, threshold) in ACHIEVEMENTS.items():
            result.append(
                {
                    "code": code,
                    "title": title,
                    "desc": desc,
                    "unlocked": code in unlocked,
                }
            )
        return result
