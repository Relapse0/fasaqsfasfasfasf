"""Модуль «Воспоминания»: копилка моментов."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.repositories.memories import MemoriesRepository
from keyboards.builders import paginate
from utils import emoji as e

router = Router(name="memories")


class MemoryStates(StatesGroup):
    content = State()


async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.PLUS} Сохранить момент", callback_data="memory:add", style="primary")],
            [InlineKeyboardButton(text=f"{e.DICE} Случайное воспоминание", callback_data="memory:random")],
            [InlineKeyboardButton(text=f"{e.BOOK} Лента", callback_data="memory:list:0")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await message.answer(f"{e.PHOTO} <b>Воспоминания</b>\n\nСохраняйте ваши моменты:", reply_markup=kb)


@router.callback_query(F.data == "memory:add")
async def memory_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MemoryStates.content)
    await callback.message.answer(f"{e.PHOTO} Опиши момент или вставь текст:")
    await callback.answer()


@router.message(MemoryStates.content)
async def memory_content(message: Message, state: FSMContext, session, user, couple) -> None:
    await state.clear()
    repo = MemoriesRepository(session)
    await repo.create(
        couple_id=couple.couple_id,
        author_id=user.user_id,
        type="note",
        content=message.text,
    )
    await session.flush()
    await message.answer(f"{e.CHECK} Момент сохранён в вашу копилку 🖼️")


@router.callback_query(F.data == "memory:random")
async def memory_random(callback: CallbackQuery, session, couple) -> None:
    repo = MemoriesRepository(session)
    m = await repo.get_random(couple.couple_id)
    if m is None:
        await callback.message.edit_text("Пока пусто. Сохраните первый момент!")
    else:
        await callback.message.edit_text(
            f"{e.PHOTO} <b>Вспомните</b> · {m.created_at:%d.%m.%Y}\n\n{m.content}"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("memory:list:"))
async def memory_list(callback: CallbackQuery, session, couple) -> None:
    page = int(callback.data.split(":")[2])
    repo = MemoriesRepository(session)
    items = await repo.list_for_couple(couple.couple_id, limit=5, offset=page * 5)

    if not items:
        await callback.message.edit_text("Больше нет записей.")
        await callback.answer()
        return

    text = "\n\n".join(
        f"{e.PHOTO} {m.created_at:%d.%m.%Y}\n{m.content}" for m in items
    )
    kb = paginate(page=page, total=100, page_size=5, prefix="memory:list")
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
