"""Модуль «Бюджет»: траты, категории, лимит, карточка отчёта."""
from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.repositories.transactions import TransactionsRepository
from services.budget_service import BudgetService
from services.card_service import CardService
from services.gamification_service import GamificationService
from utils import emoji as e
from utils.validators import parse_amount

router = Router(name="budget")

CATEGORIES = ["food", "transport", "home", "health", "fun", "gifts", "travel", "other"]


class BudgetStates(StatesGroup):
    amount = State()
    comment = State()
    limit = State()


async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.PLUS} Добавить трату", callback_data="budget:add", style="primary")],
            [InlineKeyboardButton(text=f"{e.CHART} Отчёт месяца", callback_data="budget:report", style="success")],
            [InlineKeyboardButton(text=f"{e.TARGET} Лимит", callback_data="budget:limit")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await message.answer(f"{e.WALLET} <b>Бюджет</b>\n\nВыберите действие:", reply_markup=kb)


# ── Добавление траты ─────────────────────────────────────
@router.callback_query(F.data == "budget:add")
async def budget_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BudgetStates.amount)
    await callback.message.answer(f"{e.WALLET} Введи сумму траты (например, 250.50):")
    await callback.answer()


@router.message(BudgetStates.amount)
async def budget_amount(message: Message, state: FSMContext) -> None:
    amount = parse_amount(message.text)
    if amount is None or amount <= 0:
        await message.answer(f"{e.CROSS} Введи корректную сумму.")
        return
    # Храним строку: FSM-данные сериализуются в JSON (Redis)
    await state.update_data(amount=str(amount))
    await state.set_state(BudgetStates.comment)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{e.category(c)} {c}", callback_data=f"budget:cat:{c}")
                for c in CATEGORIES[:4]
            ],
            [
                InlineKeyboardButton(text=f"{e.category(c)} {c}", callback_data=f"budget:cat:{c}")
                for c in CATEGORIES[4:]
            ],
        ]
    )
    await message.answer(f"{e.QUESTION} Выбери категорию:", reply_markup=kb)


@router.callback_query(F.data.startswith("budget:cat:"))
async def budget_category(callback: CallbackQuery, state: FSMContext, session, user, couple) -> None:
    category = callback.data.split(":")[2]
    data = await state.get_data()
    await state.clear()

    service = BudgetService(session)
    await service.add_transaction(
        couple_id=couple.couple_id,
        user_id=user.user_id,
        amount=Decimal(data["amount"]),
        category=category,
        comment=None,
    )
    # Геймификация: очки за активность
    await GamificationService(session).add_points(
        couple_id=couple.couple_id, amount=2, reason="budget", user_id=user.user_id
    )
    await session.flush()

    await callback.message.edit_text(
        f"{e.CHECK} Трата записана!\n\n{e.category(category)} {category}: <b>{data['amount']} ₽</b>",
        reply_markup=None,
    )
    await callback.answer()


# ── Отчёт (карточка) ─────────────────────────────────────
@router.callback_query(F.data == "budget:report")
async def budget_report(callback: CallbackQuery, session, couple) -> None:
    await callback.message.answer_chat_action("upload_photo")
    path = await CardService().budget_card(session, couple)
    from aiogram.types import FSInputFile

    await callback.message.answer_photo(FSInputFile(path), caption=f"{e.CHART} Бюджет месяца")
    await callback.answer()


# ── Лимит ────────────────────────────────────────────────
@router.callback_query(F.data == "budget:limit")
async def budget_limit(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BudgetStates.limit)
    await callback.message.answer(f"{e.TARGET} Введи месячный лимит (0 — убрать):")
    await callback.answer()


@router.message(BudgetStates.limit)
async def budget_limit_input(message: Message, state: FSMContext, session, couple) -> None:
    amount = parse_amount(message.text)
    if amount is None:
        await message.answer(f"{e.CROSS} Введи корректную сумму.")
        return
    await state.clear()
    await BudgetService(session).set_limit(couple.couple_id, amount)
    await session.flush()
    await message.answer(f"{e.CHECK} Лимит установлен: <b>{amount} ₽</b>")
