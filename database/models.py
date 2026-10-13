"""ORM-модели. Схема БД — единый источник истины для Alembic.

Все записи привязаны к ``couple_id`` (контекст пары), а приватность
регулируется флагом ``visible_to_partner`` там, где это уместно.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from database.db import Base

# JSON, который в PostgreSQL хранится как JSONB (быстрая работа с настройками)
JSONType = JSON().with_variant(JSONB(), "postgresql")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), default="")
    couple_id: Mapped[int | None] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="SET NULL"), nullable=True, index=True
    )
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    language: Mapped[str] = mapped_column(String(8), default="ru")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Couple(Base):
    __tablename__ = "couples"

    couple_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user1_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user2_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    invite_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), default="Мы")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # settings: включённые модули, приватность, прочее
    settings: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[str] = mapped_column(Text)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    repeat_rule: Mapped[str] = mapped_column(String(16), default="once")  # once/daily/weekly/monthly
    notify_both: Mapped[bool] = mapped_column(Boolean, default=True)
    visible_to_partner: Mapped[bool] = mapped_column(Boolean, default=True)
    job_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(BigInteger)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    category: Mapped[str] = mapped_column(String(64), default="other")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class ShoppingItem(Base):
    __tablename__ = "shopping"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    item: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), default="other")
    added_by: Mapped[int] = mapped_column(BigInteger)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Mood(Base):
    __tablename__ = "moods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    mood: Mapped[int] = mapped_column(Integer)  # 1..5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(256))
    event_date: Mapped[date] = mapped_column(Date)
    repeat_yearly: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_days_before: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    date: Mapped[date] = mapped_column(Date, index=True)
    user1_done: Mapped[bool] = mapped_column(Boolean, default=False)
    user2_done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Gratitude(Base):
    __tablename__ = "gratitude"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    from_user: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[str] = mapped_column(Text)
    visible_to_partner: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(BigInteger)
    type: Mapped[str] = mapped_column(String(16), default="note")  # note/photo/video/audio
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class Capsule(Base):
    __tablename__ = "capsules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[str] = mapped_column(Text)
    open_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    opened: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Point(Base):
    __tablename__ = "points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.couple_id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
