"""Модуль «Настройки»: модули вкл/выкл, TZ, имя пары, карточка профиля."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.repositories.couples import CouplesRepository
from database.repositories.users import UsersRepository
from keyboards.main_menu import MODULES
from services.card_service import CardService
from utils import emoji as e
from utils.validators import is_valid_timezone

router = Router(name="settings")


class SettingsStates(StatesGroup):
    timezone = State()
    name = State()


NOT_PAIRED = "Сначала создайте пару 👉 /start"


async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.GAME} Модули", callback_data="settings:modules", style="primary")],
            [InlineKeyboardButton(text=f"{e.CLOCK} Часовой пояс", callback_data="settings:tz")],
            [InlineKeyboardButton(text=f"{e.EDIT} Имя пары", callback_data="settings:name")],
            [InlineKeyboardButton(text=f"{e.PHOTO} Карточка профиля", callback_data="settings:profile")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    tz_line = (
        f"Текущий пояс: <b>{user.timezone}</b>"
        if couple
        else "Вы пока не в паре — создайте её через /start"
    )
    await message.answer(f"{e.SETTINGS} <b>Настройки</b>\n\n{tz_line}", reply_markup=kb)


# ── Модули вкл/выкл ──────────────────────────────────────
@router.callback_query(F.data == "settings:modules")
async def settings_modules(callback: CallbackQuery, couple) -> None:
    if couple is None:
        await callback.message.answer(NOT_PAIRED)
        await callback.answer()
        return
    modules = (couple.settings or {}).get("modules", {})
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{'✅' if modules.get(code, True) else '⛔'} {MODULES[code].split(' ', 1)[1]}",
                    callback_data=f"settings:toggle:{code}",
                )
            ]
            for code in MODULES
            if code != "settings"
        ]
    )
    kb.inline_keyboard.append([InlineKeyboardButton(text=f"{e.BACK} Назад", callback_data="settings:back")])
    await callback.message.edit_text(f"{e.GAME} Включённые модули отображаются в меню:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("settings:toggle:"))
async def settings_toggle(callback: CallbackQuery, session, couple) -> None:
    if couple is None:
        await callback.answer(NOT_PAIRED)
        return
    code = callback.data.split(":")[2]
    couples = CouplesRepository(session)
    current = await couples.get_setting(couple, f"modules.{code}", default=True)
    await couples.set_setting(couple, f"modules.{code}", not current)
    await session.flush()
    await settings_modules(callback, couple)
    await callback.answer()


@router.callback_query(F.data == "settings:back")
async def settings_back(callback: CallbackQuery, session, user, couple, settings, language: str) -> None:
    await callback.answer()
    await show_menu(callback.message, session, user, couple, settings, language)


# ── Часовой пояс ─────────────────────────────────────────
@router.callback_query(F.data == "settings:tz")
async def settings_tz(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsStates.timezone)
    await callback.message.answer(
        f"{e.CLOCK} Введи часовой пояс (IANA), например: <code>Europe/Moscow</code>"
    )
    await callback.answer()


@router.message(SettingsStates.timezone)
async def settings_tz_input(message: Message, state: FSMContext, session, user) -> None:
    tz = message.text.strip()
    if not is_valid_timezone(tz):
        await message.answer(f"{e.CROSS} Неверный пояс. Пример: <code>Europe/Moscow</code>")
        return
    await state.clear()
    await UsersRepository(session).set_timezone(user.user_id, tz)
    await session.flush()
    await message.answer(f"{e.CHECK} Часовой пояс: <b>{tz}</b>")


# ── Имя пары ─────────────────────────────────────────────
@router.callback_query(F.data == "settings:name")
async def settings_name(callback: CallbackQuery, state: FSMContext, couple) -> None:
    if couple is None:
        await callback.message.answer(NOT_PAIRED)
        await callback.answer()
        return
    await state.set_state(SettingsStates.name)
    await callback.message.answer(f"{e.EDIT} Как назвать вашу пару?")
    await callback.answer()


@router.message(SettingsStates.name)
async def settings_name_input(message: Message, state: FSMContext, session, couple) -> None:
    if couple is None:
        await state.clear()
        await message.answer(NOT_PAIRED)
        return
    await state.clear()
    name = message.text.strip()[:128] or "Мы"
    await CouplesRepository(session).set_name(couple, name)
    await session.flush()
    await message.answer(f"{e.CHECK} Теперь вы — <b>{name}</b> ❤️")


# ── Карточка профиля ─────────────────────────────────────
@router.callback_query(F.data == "settings:profile")
async def settings_profile(callback: CallbackQuery, session, couple) -> None:
    if couple is None:
        await callback.message.answer(NOT_PAIRED)
        await callback.answer()
        return
    await callback.message.answer_chat_action("upload_photo")
    path = await CardService().profile_card(session, couple)
    await callback.message.answer_photo(FSInputFile(path), caption=f"{e.COUPLE} Профиль пары")
    await callback.answer()
