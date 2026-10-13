"""Модуль «Напоминания»: создание (FSM), список, удаление.

FSM: текст → дата/время → повтор → кому (обоим/только мне) → приватность.
"""
from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.repositories.reminders import RemindersRepository
from services.reminder_service import REPEAT_LABELS, ReminderService
from utils import emoji as e
from utils.helpers import human_date
from utils.validators import parse_date, parse_time

router = Router(name="reminders")


class ReminderStates(StatesGroup):
    text = State()
    datetime = State()
    repeat = State()
    notify = State()
    private = State()


# ── Меню модуля ──────────────────────────────────────────
async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    repo = RemindersRepository(session)
    items = await repo.list_visible_for(couple.couple_id, user.user_id, limit=10)

    lines = [f"{e.BELL} <b>Напоминания</b>\n"]
    if not items:
        lines.append("Пока пусто. Создайте первое напоминание 👇")
    for r in items:
        icon = "🔁" if r.repeat_rule != "once" else "🔔"
        lines.append(
            f"{icon} <b>{r.text}</b>\n"
            f"   ⏰ {human_date(r.remind_at, user.timezone)} · {REPEAT_LABELS.get(r.repeat_rule, '')}"
        )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.PLUS} Создать", callback_data="rem:create", style="primary")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await message.answer("\n".join(lines), reply_markup=kb)


# ── Создание (FSM) ───────────────────────────────────────
@router.callback_query(F.data == "rem:create")
async def rem_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ReminderStates.text)
    await callback.message.answer(f"{e.EDIT} Что нужно напомнить?")
    await callback.answer()


@router.message(ReminderStates.text)
async def rem_text(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.text)
    await state.set_state(ReminderStates.datetime)
    await message.answer(
        f"{e.CLOCK} Когда? Формат: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
        "или <code>ДД.ММ ЧЧ:ММ</code>, или просто <code>ЧЧ:ММ</code> (сегодня)."
    )


@router.message(ReminderStates.datetime)
async def rem_datetime(message: Message, state: FSMContext, user) -> None:
    dt = _parse_reminder_dt(message.text, user.timezone)
    if dt is None:
        await message.answer(f"{e.CROSS} Не понял дату. Пример: <code>14.02 21:00</code>")
        return
    # Храним ISO-строку: FSM-данные сериализуются в JSON (Redis)
    await state.update_data(remind_at=dt.isoformat())
    await state.set_state(ReminderStates.repeat)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔂 Один раз", callback_data="rem:rep:once", style="primary"),
                InlineKeyboardButton(text="🔁 Ежедневно", callback_data="rem:rep:daily"),
                InlineKeyboardButton(text="🗓️ Еженедельно", callback_data="rem:rep:weekly"),
            ],
            [InlineKeyboardButton(text="📅 Ежемесячно", callback_data="rem:rep:monthly")],
        ]
    )
    await message.answer(f"{e.BELL} Как часто повторять?", reply_markup=kb)


@router.callback_query(F.data.startswith("rem:rep:"))
async def rem_repeat(callback: CallbackQuery, state: FSMContext) -> None:
    rule = callback.data.split(":")[2]
    await state.update_data(repeat_rule=rule)
    await state.set_state(ReminderStates.notify)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Обоим", callback_data="rem:notify:1", style="success"),
                InlineKeyboardButton(text="🙋 Только мне", callback_data="rem:notify:0"),
            ]
        ]
    )
    await callback.message.edit_text(f"{e.BELL} Кого уведомлять?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("rem:notify:"))
async def rem_notify(callback: CallbackQuery, state: FSMContext) -> None:
    notify_both = callback.data.split(":")[2] == "1"
    await state.update_data(notify_both=notify_both)
    await state.set_state(ReminderStates.private)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{e.UNLOCK} Видно партнёру", callback_data="rem:priv:0", style="success"),
                InlineKeyboardButton(text=f"{e.LOCK} Приватное", callback_data="rem:priv:1"),
            ]
        ]
    )
    await callback.message.edit_text("Кто видит это напоминание?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("rem:priv:"))
async def rem_private(callback: CallbackQuery, state: FSMContext, session, user, couple) -> None:
    private = callback.data.split(":")[2] == "1"
    data = await state.get_data()
    await state.clear()

    repo = RemindersRepository(session)
    reminder = await repo.create(
        couple_id=couple.couple_id,
        author_id=user.user_id,
        text=data["text"],
        remind_at=datetime.fromisoformat(data["remind_at"]),
        repeat_rule=data["repeat_rule"],
        notify_both=data["notify_both"],
        visible_to_partner=not private,
    )
    # Планируем джобу (job_id сохранится при коммите мидлвари)
    ReminderService().schedule(reminder)
    await session.flush()

    await callback.message.edit_text(
        f"{e.CHECK} Напоминание создано!\n\n"
        f"🔔 {reminder.text}\n"
        f"⏰ {human_date(reminder.remind_at, user.timezone)}",
        reply_markup=None,
    )
    await callback.answer()


# ── Удаление (через список — пока простой вариант) ───────
@router.callback_query(F.data.startswith("rem:del:"))
async def rem_delete(callback: CallbackQuery, session) -> None:
    rid = int(callback.data.split(":")[2])
    repo = RemindersRepository(session)
    reminder = await repo.get_by_id(rid)
    if reminder is not None:
        ReminderService(callback.message.bot).unschedule(reminder)
        await repo.delete(reminder)
        await session.flush()
        await callback.message.edit_text(f"{e.CHECK} Напоминание удалено.")
    await callback.answer()


def _parse_reminder_dt(text: str, tz: str) -> datetime | None:
    """Парсит 'ДД.ММ.ГГГГ ЧЧ:ММ' | 'ДД.ММ ЧЧ:ММ' | 'ЧЧ:ММ' в aware datetime."""
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    try:
        zone = ZoneInfo(tz)
    except Exception:  # noqa: BLE001
        zone = timezone.utc

    parts = text.strip().split()
    now = datetime.now(zone)

    if len(parts) == 1:
        # только время — сегодня
        t = parse_time(parts[0])
        if not t:
            return None
        dt = now.replace(hour=t[0], minute=t[1], second=0, microsecond=0)
    elif len(parts) >= 2:
        date_str, time_str = parts[0], parts[-1]
        t = parse_time(time_str)
        d = parse_date(date_str, year=now.year)
        if not t or not d:
            return None
        dt = datetime(d.year, d.month, d.day, t[0], t[1], tzinfo=zone)
    else:
        return None

    if dt <= now:
        # Если время уже прошло — переносим на следующий день
        dt = dt + timedelta(days=1)
    return dt
