"""Модуль «Покупки»: общий список, отметка, добавление."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.repositories.shopping import ShoppingRepository
from utils import emoji as e

router = Router(name="shopping")

CATEGORIES = ["food", "home", "health", "other"]


class ShoppingStates(StatesGroup):
    item = State()


async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    repo = ShoppingRepository(session)
    items = await repo.list_active(couple.couple_id)

    if not items:
        text = f"{e.CART} <b>Покупки</b>\n\nСписок пуст. Добавьте что-нибудь 👇"
    else:
        lines = [f"{e.CART} <b>Покупки</b> ({len(items)})\n"]
        for i, it in enumerate(items, 1):
            icon = "✅" if it.done else "⬜"
            lines.append(f"{icon} {it.item} · {e.category(it.category)}")
        text = "\n".join(lines)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.PLUS} Добавить", callback_data="shop:add", style="primary")],
        ]
    )
    # Кнопки отметки/удаления, если есть позиции
    rows = []
    for it in items[:8]:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"☑️ {it.item[:20]}", callback_data=f"shop:toggle:{it.id}"
                ),
                InlineKeyboardButton(text="🗑️", callback_data=f"shop:del:{it.id}"),
            ]
        )
    if rows:
        kb.inline_keyboard = rows + kb.inline_keyboard
    kb.inline_keyboard.append([InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")])

    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "shop:add")
async def shop_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ShoppingStates.item)
    await callback.message.answer(f"{e.CART} Что добавить в список?")
    await callback.answer()


@router.message(ShoppingStates.item)
async def shop_item(message: Message, state: FSMContext, session, user, couple) -> None:
    await state.clear()
    repo = ShoppingRepository(session)
    await repo.create(
        couple_id=couple.couple_id,
        item=message.text,
        category="other",
        added_by=user.user_id,
    )
    await session.flush()
    await message.answer(f"{e.CHECK} Добавлено: <b>{message.text}</b>")


@router.callback_query(F.data.startswith("shop:toggle:"))
async def shop_toggle(callback: CallbackQuery, session, couple) -> None:
    item_id = int(callback.data.split(":")[2])
    repo = ShoppingRepository(session)
    item = await repo.get_by_id(couple.couple_id, item_id)
    if item is not None:
        await repo.toggle(item)
        await session.flush()
    await callback.answer()


@router.callback_query(F.data.startswith("shop:del:"))
async def shop_del(callback: CallbackQuery, session, couple) -> None:
    item_id = int(callback.data.split(":")[2])
    repo = ShoppingRepository(session)
    item = await repo.get_by_id(couple.couple_id, item_id)
    if item is not None:
        await repo.remove(item)
        await session.flush()
        await callback.message.edit_text(f"{e.CHECK} Удалено из списка.")
    await callback.answer()
