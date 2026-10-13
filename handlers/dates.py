"""Модуль «Даты»: события, годовщины, обратный отсчёт."""
from __future__ import annotations

from datetime import date, datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.repositories.capsules import CapsulesRepository
from database.repositories.events import EventsRepository
from services.capsule_service import CapsuleService
from utils import emoji as e
from utils.validators import parse_date, parse_time

router = Router(name="dates")


class EventStates(StatesGroup):
    title = State()
    date = State()
    notify = State()


class CapsuleStates(StatesGroup):
    text = State()
    open_at = State()


async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    repo = EventsRepository(session)
    events = await repo.list_for_couple(couple.couple_id)

    today = datetime.now(timezone.utc).date()
    lines = [f"{e.CALENDAR} <b>Ваши даты</b>\n"]
    if events:
        for ev in events:
            nxt, days = _next_event(ev, today)
            lines.append(f"🎉 <b>{ev.title}</b> — через <b>{days}</b> дн. ({nxt:%d.%m})")
    else:
        lines.append("Пока нет событий. Добавьте годовщину или день рождения 👇")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.PLUS} Добавить событие", callback_data="dates:add", style="primary")],
            [InlineKeyboardButton(text=f"{e.HOURGLASS} Обратный отсчёт", callback_data="dates:countdown")],
            [InlineKeyboardButton(text=f"{e.CAPSULE} Капсула времени", callback_data="capsule:menu")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await message.answer("\n".join(lines), reply_markup=kb)


# ── Добавление события ───────────────────────────────────
@router.callback_query(F.data == "dates:add")
async def dates_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(EventStates.title)
    await callback.message.answer(f"{e.CALENDAR} Название события? (например, «Годовщина»)")
    await callback.answer()


@router.message(EventStates.title)
async def dates_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text)
    await state.set_state(EventStates.date)
    await message.answer(f"{e.CLOCK} Дата события? Формат: <code>ДД.ММ.ГГГГ</code>")


@router.message(EventStates.date)
async def dates_date(message: Message, state: FSMContext, session, couple) -> None:
    d = parse_date(message.text)
    if d is None:
        await message.answer(f"{e.CROSS} Неверная дата. Пример: <code>14.02.2020</code>")
        return
    # Храним ISO-строку: FSM-данные сериализуются в JSON (Redis)
    await state.update_data(event_date=d.date().isoformat())
    await state.set_state(EventStates.notify)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="0 дней", callback_data="dates:notify:0"),
                InlineKeyboardButton(text="За 1 день", callback_data="dates:notify:1"),
                InlineKeyboardButton(text="За 3 дня", callback_data="dates:notify:3", style="success"),
                InlineKeyboardButton(text="За неделю", callback_data="dates:notify:7"),
            ]
        ]
    )
    await message.answer("За сколько дней напомнить?", reply_markup=kb)


@router.callback_query(F.data.startswith("dates:notify:"))
async def dates_notify(callback: CallbackQuery, state: FSMContext, session, couple) -> None:
    days = int(callback.data.split(":")[2])
    data = await state.get_data()
    await state.clear()

    repo = EventsRepository(session)
    await repo.create(
        couple_id=couple.couple_id,
        title=data["title"],
        event_date=date.fromisoformat(data["event_date"]),
        repeat_yearly=True,
        notify_days_before=days,
    )
    await session.flush()
    await callback.message.edit_text(
        f"{e.CHECK} Событие <b>{data['title']}</b> добавлено!", reply_markup=None
    )
    await callback.answer()


@router.callback_query(F.data == "dates:countdown")
async def dates_countdown(callback: CallbackQuery, session, couple) -> None:
    repo = EventsRepository(session)
    events = await repo.list_for_couple(couple.couple_id)
    today = datetime.now(timezone.utc).date()

    if not events:
        await callback.message.edit_text("Нет событий для отсчёта.")
        await callback.answer()
        return

    lines = [f"{e.HOURGLASS} <b>Обратный отсчёт</b>\n"]
    for ev in sorted(events, key=lambda x: _next_event(x, today)[1]):
        nxt, days = _next_event(ev, today)
        lines.append(f"🎉 <b>{ev.title}</b> — {nxt:%d.%m.%Y} ({days} дн.)")
    await callback.message.edit_text("\n".join(lines))
    await callback.answer()


def _next_event(ev, today: date) -> tuple[date, int]:
    """Следующая дата события и число дней до неё."""
    base = ev.event_date
    year = today.year
    candidate = date(year, base.month, base.day)
    if candidate < today:
        candidate = date(year + 1, base.month, base.day)
    return candidate, (candidate - today).days


# ── Капсулы времени ──────────────────────────────────────
@router.callback_query(F.data == "capsule:menu")
async def capsule_menu(callback: CallbackQuery, session, couple) -> None:
    repo = CapsulesRepository(session)
    capsules = await repo.list_for_couple(couple.couple_id)
    unopened = [c for c in capsules if not c.opened]
    lines = [f"{e.CAPSULE} <b>Капсулы времени</b>\n"]
    if not capsules:
        lines.append("Пока нет капсул. Напишите письмо в будущее 👇")
    else:
        lines.append(f"Всего: {len(capsules)} · ждут открытия: {len(unopened)}\n")
        for c in unopened[:5]:
            lines.append(f"⏳ откроется {c.open_at:%d.%m.%Y} — «{c.text[:30]}…»")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.PLUS} Создать капсулу", callback_data="capsule:add", style="primary")],
            [InlineKeyboardButton(text=f"{e.BACK} Назад", callback_data="menu:main")],
        ]
    )
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "capsule:add")
async def capsule_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CapsuleStates.text)
    await callback.message.answer(f"{e.CAPSULE} Напишите сообщение в будущее:")
    await callback.answer()


@router.message(CapsuleStates.text)
async def capsule_text(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.text)
    await state.set_state(CapsuleStates.open_at)
    await message.answer(f"{e.CLOCK} Когда открыть? Формат: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>")


@router.message(CapsuleStates.open_at)
async def capsule_open_at(message: Message, state: FSMContext, session, user, couple) -> None:
    dt = _parse_capsule_dt(message.text, user.timezone)
    if dt is None:
        await message.answer(f"{e.CROSS} Неверная дата. Пример: <code>01.01.2026 12:00</code>")
        return
    data = await state.get_data()
    await state.clear()

    repo = CapsulesRepository(session)
    capsule = await repo.create(
        couple_id=couple.couple_id,
        author_id=user.user_id,
        text=data["text"],
        open_at=dt,
    )
    await session.flush()
    CapsuleService().schedule_open(capsule)

    await message.answer(
        f"{e.CHECK} Капсула создана! Она откроется {dt:%d.%m.%Y в %H:%M} 🕰️"
    )


def _parse_capsule_dt(text: str, tz: str) -> datetime | None:
    """Парсит 'ДД.ММ.ГГГГ ЧЧ:ММ' в aware datetime (будущее)."""
    from zoneinfo import ZoneInfo

    try:
        zone = ZoneInfo(tz)
    except Exception:  # noqa: BLE001
        zone = timezone.utc
    parts = text.strip().split()
    if len(parts) < 2:
        return None
    d = parse_date(parts[0])
    t = parse_time(parts[-1])
    if not d or not t:
        return None
    dt = datetime(d.year, d.month, d.day, t[0], t[1], tzinfo=zone)
    return dt if dt > datetime.now(zone) else None
