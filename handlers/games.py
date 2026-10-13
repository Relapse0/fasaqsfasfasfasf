"""Модуль «Игры»: викторина, дуэль, совместные цели."""
from __future__ import annotations

import random

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.repositories.couples import CouplesRepository
from services.gamification_service import GamificationService
from utils import emoji as e

router = Router(name="games")

# Статическая викторина «Как хорошо ты знаешь партнёра?» (3 вопроса)
QUIZ = [
    ("Какой язык любви у твоего партнёра?", ["Слова", "Время", "Подарки", "Забота"], 1),
    ("Что партнёр выберет на выходные?", ["Горы", "Море", "Город", "Диван"], 3),
    ("Любимый способ сказать «я тебя люблю»?", ["Словами", "Объятиями", "Сюрпризом", "Все сразу"], 2),
]

RPS = {"🗿": "камень", "📄": "бумага", "✂️": "ножницы"}


class QuizStates(StatesGroup):
    answering = State()


class GoalsStates(StatesGroup):
    title = State()


async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.QUESTION} Викторина", callback_data="games:quiz", style="primary")],
            [InlineKeyboardButton(text=f"{e.DICE} Дуэль (КНБ)", callback_data="games:duel")],
            [InlineKeyboardButton(text=f"{e.TARGET} Совместные цели", callback_data="games:goals")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await message.answer(f"{e.GAME} <b>Игры</b>\n\nВыберите:", reply_markup=kb)


# ── Викторина ────────────────────────────────────────────
@router.callback_query(F.data == "games:quiz")
async def quiz_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(QuizStates.answering)
    await state.update_data(score=0, q=0)
    await _quiz_question(callback, state)


@router.callback_query(QuizStates.answering, F.data.startswith("quiz:ans:"))
async def quiz_answer(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, q_str, choice_str = callback.data.split(":")
    q = int(q_str)
    choice = int(choice_str)
    data = await state.get_data()
    score = data.get("score", 0)
    if choice == QUIZ[q][2]:
        score += 1
    await state.update_data(score=score, q=q + 1)

    if q + 1 < len(QUIZ):
        await _quiz_question(callback, state)
    else:
        await state.clear()
        total = len(QUIZ)
        await callback.message.edit_text(
            f"{e.TROPHY} <b>Результат: {score}/{total}</b>\n\n"
            f"{'😍 Вы знаете друг друга отлично!' if score == total else '🤍 Есть куда расти — это и интересно!'}"
        )
    await callback.answer()


async def _quiz_question(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    q = data.get("q", 0)
    question, options, _ = QUIZ[q]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"quiz:ans:{q}:{i}")]
            for i, opt in enumerate(options)
        ]
    )
    await callback.message.edit_text(f"{e.QUESTION} Вопрос {q + 1}/{len(QUIZ)}\n\n{question}", reply_markup=kb)


# ── Дуэль (камень-ножницы-бумага vs бот) ─────────────────
@router.callback_query(F.data == "games:duel")
async def duel_start(callback: CallbackQuery) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗿", callback_data="duel:0"),
                InlineKeyboardButton(text="📄", callback_data="duel:1"),
                InlineKeyboardButton(text="✂️", callback_data="duel:2"),
            ]
        ]
    )
    await callback.message.edit_text(f"{e.DICE} <b>Дуэль</b>\n\nВыбери жест:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("duel:"))
async def duel_play(callback: CallbackQuery, session, couple) -> None:
    you = int(callback.data.split(":")[1])
    bot = random.randint(0, 2)
    names = ["🗿", "📄", "✂️"]
    # 0 камень, 1 бумага, 2 ножницы; (you - bot) % 3 == 1 -> победа
    diff = (you - bot) % 3
    if diff == 0:
        result = "Ничья 🤝"
        points = 1
    elif diff == 1:
        result = "Ты победил(а)! 🎉"
        points = 5
    else:
        result = "Бот победил 🤖"
        points = 1
    await GamificationService(session).add_points(
        couple_id=couple.couple_id, amount=points, reason="duel", user_id=callback.from_user.id
    )
    await session.flush()
    await callback.message.edit_text(
        f"Ты: {names[you]} · Бот: {names[bot]}\n\n{result}\n+{points} очков"
    )
    await callback.answer()


# ── Совместные цели ──────────────────────────────────────
@router.callback_query(F.data == "games:goals")
async def goals_list(callback: CallbackQuery, session, couple) -> None:
    goals = (couple.settings or {}).get("goals", [])
    if not goals:
        text = f"{e.TARGET} <b>Совместные цели</b>\n\nПока пусто. Добавьте первую цель 👇"
    else:
        text = f"{e.TARGET} <b>Совместные цели</b>\n\n" + "\n".join(f"• {g}" for g in goals)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.PLUS} Добавить цель", callback_data="goals:add", style="primary")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "goals:add")
async def goals_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GoalsStates.title)
    await callback.message.answer(f"{e.TARGET} Опишите цель (например, «Поехать в горы летом»):")
    await callback.answer()


@router.message(GoalsStates.title)
async def goals_title(message: Message, state: FSMContext, session, couple) -> None:
    await state.clear()
    couples = CouplesRepository(session)
    goals = list((couple.settings or {}).get("goals", []))
    goals.append(message.text)
    await couples.set_setting(couple, "goals", goals)
    await session.flush()
    await message.answer(f"{e.CHECK} Цель добавлена: <b>{message.text}</b>")
