"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("first_name", sa.String(128), server_default="", nullable=False),
        sa.Column("couple_id", sa.Integer(), nullable=True),
        sa.Column("timezone", sa.String(64), server_default="Europe/Moscow", nullable=False),
        sa.Column("language", sa.String(8), server_default="ru", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # couples
    op.create_table(
        "couples",
        sa.Column("couple_id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user1_id", sa.BigInteger(), nullable=False),
        sa.Column("user2_id", sa.BigInteger(), nullable=True),
        sa.Column("invite_code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(128), server_default="Мы", nullable=False),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_couples_invite_code", "couples", ["invite_code"], unique=True)

    # reminders
    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("repeat_rule", sa.String(16), server_default="once", nullable=False),
        sa.Column("notify_both", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("visible_to_partner", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("job_id", sa.String(64), nullable=True),
        sa.Column("done", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reminders_couple_id", "reminders", ["couple_id"])
    op.create_index("ix_reminders_remind_at", "reminders", ["remind_at"])

    # transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("category", sa.String(64), server_default="other", nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transactions_couple_id", "transactions", ["couple_id"])
    op.create_index("ix_transactions_created_at", "transactions", ["created_at"])

    # shopping
    op.create_table(
        "shopping",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("item", sa.Text(), nullable=False),
        sa.Column("category", sa.String(64), server_default="other", nullable=False),
        sa.Column("added_by", sa.BigInteger(), nullable=False),
        sa.Column("done", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_shopping_couple_id", "shopping", ["couple_id"])

    # moods
    op.create_table(
        "moods",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("mood", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_moods_user_id", "moods", ["user_id"])
    op.create_index("ix_moods_couple_id", "moods", ["couple_id"])

    # events
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("repeat_yearly", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("notify_days_before", sa.Integer(), server_default="3", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_events_couple_id", "events", ["couple_id"])

    # challenges
    op.create_table(
        "challenges",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("user1_done", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("user2_done", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_challenges_couple_id", "challenges", ["couple_id"])
    op.create_index("ix_challenges_date", "challenges", ["date"])

    # gratitude
    op.create_table(
        "gratitude",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("from_user", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("visible_to_partner", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_gratitude_couple_id", "gratitude", ["couple_id"])

    # memories
    op.create_table(
        "memories",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(16), server_default="note", nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("media_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_memories_couple_id", "memories", ["couple_id"])

    # capsules
    op.create_table(
        "capsules",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("open_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opened", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_capsules_couple_id", "capsules", ["couple_id"])
    op.create_index("ix_capsules_open_at", "capsules", ["open_at"])

    # achievements
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_achievements_couple_id", "achievements", ["couple_id"])

    # points
    op.create_table(
        "points",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("couple_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_points_couple_id", "points", ["couple_id"])

    # Внешние ключи на couples (добавляем после создания всех таблиц)
    for src_table, ondelete in (
        ("users", "SET NULL"),
        ("reminders", "CASCADE"),
        ("transactions", "CASCADE"),
        ("shopping", "CASCADE"),
        ("moods", "CASCADE"),
        ("events", "CASCADE"),
        ("challenges", "CASCADE"),
        ("gratitude", "CASCADE"),
        ("memories", "CASCADE"),
        ("capsules", "CASCADE"),
        ("achievements", "CASCADE"),
        ("points", "CASCADE"),
    ):
        op.create_foreign_key(
            f"fk_{src_table}_couple_id",
            src_table,
            "couples",
            ["couple_id"],
            ["couple_id"],
            ondelete=ondelete,
        )


def downgrade() -> None:
    # Сначала дочерние таблицы, затем users (ссылается на couples), затем couples
    for table in (
        "points", "achievements", "capsules", "memories", "gratitude",
        "challenges", "events", "moods", "shopping", "transactions",
        "reminders",
    ):
        op.drop_table(table)
    op.drop_table("users")
    op.drop_table("couples")
