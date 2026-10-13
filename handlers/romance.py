"""Модуль «Романтика»: вопрос дня, челлендж, правда/действие, сигналы."""
from __future__ import annotations

import random
from datetime import date

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.repositories.challenges import ChallengesRepository
from utils import emoji as e

router = Router(name="romance")

QUESTIONS = [
    "Что впервые привлекло тебя во мне?",
    "Какое наше воспоминание ты переживаешь заново чаще всего?",
    "Чему ты научился(ась) у меня?",
    "Какой наш совместный день был идеальным?",
    "Что ты хочешь попробовать вместе в этом году?",
]

CHALLENGES = [
    "Приготовьте ужин вместе 🍝",
    "Сходите на прогулку без телефонов 🌳",
    "Сделайте друг другу комплименты 🤍",
    "Посмотрите фильм, который выберет партнёр 🎬",
    "Напишите друг другу письма от руки 💌",
]

TRUTHS = [
    "Самое смешное, что ты обо мне думал(а) в начале?",
    "Какой твой самый неловкий момент?",
    "Что ты никогда не рассказывал(а) никому?",
]

DARES = [
    "Спой куплет любимой песни 🎤",
    "Изобрази партнёра 🤭",
    "Расскажи анекдот 😄",
    "Станцуй 10 секунд 💃",
]

SIGNALS = ["❤️", "🔥", "😘", "🤗", "😉", "🫶"]


async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.QUESTION} Вопрос дня", callback_data="romance:question", style="primary")],
            [InlineKeyboardButton(text=f"{e.FIRE} Челлендж дня", callback_data="romance:challenge")],
            [InlineKeyboardButton(text=f"{e.DICE} Правда или действие", callback_data="romance:td")],
            [InlineKeyboardButton(text=f"{e.SECRET} Секретный сигнал", callback_data="romance:signal")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await message.answer(f"{e.FIRE} <b>Романтика</b>\n\nВыберите:", reply_markup=kb)


@router.callback_query(F.data == "romance:question")
async def romance_question(callback: CallbackQuery) -> None:
    q = QUESTIONS[date.today().toordinal() % len(QUESTIONS)]
    await callback.message.edit_text(f"{e.QUESTION} <b>Вопрос дня</b>\n\n{q}\n\n<i>Обсудите вместе 🤍</i>")
    await callback.answer()


@router.callback_query(F.data == "romance:challenge")
async def romance_challenge(callback: CallbackQuery, session, couple, user) -> None:
    today = date.today()
    repo = ChallengesRepository(session)
    ch = await repo.get_for_date(couple.couple_id, today)
    if ch is None:
        text = CHALLENGES[today.toordinal() % len(CHALLENGES)]
        ch = await repo.create(couple_id=couple.couple_id, text=text, day=today)
        await session.flush()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.CHECK} Выполнено!", callback_data="challenge:done", style="success")],
        ]
    )
    await callback.message.edit_text(
        f"{e.FIRE} <b>Челлендж дня</b>\n\n{ch.text}\n\n"
        f"Первый: {'✅' if ch.user1_done else '⏳'} · Второй: {'✅' if ch.user2_done else '⏳'}",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data == "challenge:done")
async def challenge_done(callback: CallbackQuery, session, couple, user) -> None:
    repo = ChallengesRepository(session)
    ch = await repo.get_for_date(couple.couple_id, date.today())
    if ch is None:
        await callback.answer("Сначала создайте челлендж.")
        return
    is_user1 = couple.user1_id == user.user_id
    await repo.mark_done(ch, is_user1=is_user1)
    await session.flush()
    done = int(ch.user1_done) + int(ch.user2_done)
    await callback.message.edit_text(
        f"{e.FIRE} Челлендж: {ch.text}\n\n"
        f"Выполнили: {done}/2 {'🎉' if done == 2 else ''}"
    )
    await callback.answer()


@router.callback_query(F.data == "romance:td")
async def romance_td(callback: CallbackQuery) -> None:
    kind = random.choice(["truth", "dare"])
    if kind == "truth":
        item = random.choice(TRUTHS)
        prefix = "Правда"
    else:
        item = random.choice(DARES)
        prefix = "Действие"
    await callback.message.edit_text(f"{e.DICE} <b>{prefix}</b>\n\n{item}")
    await callback.answer()


@router.callback_query(F.data == "romance:signal")
async def romance_signal(callback: CallbackQuery, couple) -> None:
    signal = random.choice(SIGNALS)
    partner_id = None
    if couple is not None:
        partner_id = couple.user2_id if couple.user1_id == callback.from_user.id else couple.user1_id
    if partner_id:
        await callback.message.bot.send_message(
            partner_id,
            f"{signal}\n\n<i>Тебе прилетел секретный сигнал 🤫</i>",
        )
    await callback.message.edit_text(f"{e.SECRET} Сигнал отправлен партнёру: {signal}")
    await callback.answer()
