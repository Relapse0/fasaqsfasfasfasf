"""Репозитории — тонкий слой доступа к данным поверх SQLAlchemy.

Правило: репозитории не содержат бизнес-логики, только SQL-операции.
"""
from database.repositories.base import BaseRepository

__all__ = ["BaseRepository"]
