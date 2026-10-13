"""Привязка пары: /start, deep-link, создание пары с именем, QR, вход по коду."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database.repositories.couples import CouplesRepository
from database.repositories.users import UsersRepository
from keyboards import main_menu as main_menu_kb
from utils import emoji as e
from utils.qr import make_qr
from utils.texts import t

router = Router(name="start")


class BindStates(StatesGroup):
    entering_code = State()
    naming = State()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command,
    state: FSMContext,
    session,
    user,
    couple,
    language: str,
    bot,
) -> None:
    """Точка входа. Обрабатывает и deep-link вида /start INVITECODE."""
    await state.clear()
    invite = command.args.strip() if command.args else None

    if invite:
        await _join_by_code(message, invite, session, user, language, bot)
        return

    if couple is not None:
        await _welcome_couple(message, couple, language)
    else:
        await _welcome_single(message, user, language)


async def _welcome_single(message: Message, user, language: str) -> None:
    text = (
        f"{e.COUPLE} Привет, {user.first_name}! {e.SPARKLES}\n\n"
        "Я — бот для пар: бюджет, напоминания, настроение, даты и воспоминания.\n\n"
        "Чтобы начать, создайте пару или введите код партнёра."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.COUPLE} Создать пару", callback_data="bind:create", style="primary")],
            [InlineKeyboardButton(text=f"{e.LINK} Ввести код", callback_data="bind:enter")],
        ]
    )
    await message.answer(text, reply_markup=kb)


async def _welcome_couple(message: Message, couple, language: str) -> None:
    text = (
        f"{e.COUPLE} <b>{couple.name}</b>\n\n"
        "Вы в паре. Выберите раздел в меню ниже 👇"
    )
    kb = main_menu_kb.build_main_menu(couple.settings, paired=True)
    await message.answer(text, reply_markup=kb)


# ── Создание пары (с именем) ─────────────────────────────
@router.callback_query(F.data == "bind:create")
async def bind_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BindStates.naming)
    await callback.message.answer(
        f"{e.COUPLE} Как назвать вашу пару?\n\n"
        "Например: «Мы», «Аня и Петя», «Наша семья» 🙂"
    )
    await callback.answer()


@router.message(BindStates.naming)
async def bind_naming(message: Message, state: FSMContext, session, user, bot) -> None:
    name = message.text.strip()[:128] or "Мы"

    couples = CouplesRepository(session)
    users = UsersRepository(session)
    couple = await couples.create(user.user_id)
    await couples.set_name(couple, name)
    await users.set_couple(user.user_id, couple.couple_id)
    await session.flush()

    me = await bot.get_me()
    deep_link = f"https://t.me/{me.username}?start={couple.invite_code}"

    await message.answer_photo(
        BufferedInputFile(make_qr(deep_link).getvalue(), filename="invite.png"),
        caption=(
            f"{e.SPARKLES} <b>Пара «{name}» создана!</b>\n\n"
            f"Код приглашения: <code>{couple.invite_code}</code>\n"
            f"Ссылка: {deep_link}\n\n"
            "Отправь код или ссылку партнёру — и вы вместе 💑"
        ),
    )
    await state.clear()

    # Сразу выдаём главное меню
    kb = main_menu_kb.build_main_menu(couple.settings, paired=True)
    await message.answer(f"{e.HOME} Вот твоё меню:", reply_markup=kb)


# ── Вход по коду ─────────────────────────────────────────
@router.callback_query(F.data == "bind:enter")
async def bind_enter(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BindStates.entering_code)
    await callback.message.answer(
        f"{e.LINK} Пришли мне код приглашения (8 символов).",
    )
    await callback.answer()


@router.message(BindStates.entering_code)
async def bind_code_input(
    message: Message, state: FSMContext, session, user, language: str
) -> None:
    code = message.text.strip().upper()
    await _join_by_code(message, code, session, user, language, message.bot)
    await state.clear()


async def _join_by_code(
    message: Message, code: str, session, user, language: str, bot
) -> None:
    """Присоединяет пользователя к паре по коду."""
    couples = CouplesRepository(session)
    users = UsersRepository(session)

    couple = await couples.get_by_invite(code)
    if couple is None:
        await message.answer(f"{e.CROSS} Код не найден. Проверь и попробуй снова.")
        return
    if couple.user1_id == user.user_id:
        await message.answer(f"{e.INFO} Это твоя же пара 🙂")
        return
    if couple.user2_id is not None and couple.user2_id != user.user_id:
        await message.answer(f"{e.CROSS} В этой паре уже двое.")
        return

    await couples.join(couple, user.user_id)
    await users.set_couple(user.user_id, couple.couple_id)
    await session.flush()

    # Уведомляем первого партнёра
    try:
        await bot.send_message(
            couple.user1_id,
            f"{e.PARTY} {user.first_name} присоединился(ась) к вашей паре!",
        )
    except Exception:  # noqa: BLE001
        pass

    kb = main_menu_kb.build_main_menu(couple.settings, paired=True)
    await message.answer(
        f"{e.HEART} Вы вместе! Добро пожаловать в {couple.name}.",
        reply_markup=kb,
    )
