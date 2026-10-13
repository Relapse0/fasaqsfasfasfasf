"""Модуль «Благодарности»: ежедневное спасибо + месячный отчёт."""
from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.repositories.gratitude import GratitudeRepository
from database.repositories.users import UsersRepository
from presentation.renderers import render_template
from utils import emoji as e

router = Router(name="gratitude")


class GratitudeStates(StatesGroup):
    text = State()
    visible = State()


async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.PLUS} Сказать спасибо", callback_data="gratitude:add", style="primary")],
            [InlineKeyboardButton(text=f"{e.SCROLL} Отчёт месяца", callback_data="gratitude:report")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await message.answer(
        f"{e.LETTER} <b>Благодарности</b>\n\nЗа что ты сегодня благодарен(на) партнёру?",
        reply_markup=kb,
    )


@router.callback_query(F.data == "gratitude:add")
async def gratitude_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GratitudeStates.text)
    await callback.message.answer(f"{e.LETTER} За что ты благодарен(на)?")
    await callback.answer()


@router.message(GratitudeStates.text)
async def gratitude_text(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.text)
    await state.set_state(GratitudeStates.visible)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{e.UNLOCK} Покажу партнёру", callback_data="gratitude:vis:1", style="success"),
                InlineKeyboardButton(text=f"{e.LOCK} Только себе", callback_data="gratitude:vis:0"),
            ]
        ]
    )
    await message.answer("Показать партнёру?", reply_markup=kb)


@router.callback_query(F.data.startswith("gratitude:vis:"))
async def gratitude_visible(callback: CallbackQuery, state: FSMContext, session, user, couple) -> None:
    visible = callback.data.split(":")[2] == "1"
    data = await state.get_data()
    await state.clear()

    repo = GratitudeRepository(session)
    await repo.create(
        couple_id=couple.couple_id,
        from_user=user.user_id,
        text=data["text"],
        visible_to_partner=visible,
    )
    await session.flush()
    await callback.message.edit_text(f"{e.CHECK} Спасибо записано! 💌", reply_markup=None)
    await callback.answer()


@router.callback_query(F.data == "gratitude:report")
async def gratitude_report(callback: CallbackQuery, session, couple) -> None:
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    repo = GratitudeRepository(session)
    items = await repo.list_for_couple(couple.couple_id, since=month_start, limit=50)
    users = UsersRepository(session)
    names = {u.user_id: u.first_name for u in await users.get_by_couple(couple.couple_id)}

    text = render_template(
        "gratitude_report.j2",
        month_label=now.strftime("%B %Y"),
        count=len(items),
        intro=f"{e.LETTER} Вот что вы ценили друг в друге в этом месяце:",
        items=[{"text": g.text, "author_name": names.get(g.from_user, "?")} for g in items],
    )
    await callback.message.edit_text(text)
    await callback.answer()
