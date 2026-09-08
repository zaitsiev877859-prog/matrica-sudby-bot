"""СЦ-01: первый вход и профиль. ЭК-01/02/03/04."""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove

from bot.db import repo
from bot.db.pool import get_pool
from bot.keyboards import main_menu_keyboard, skip_keyboard

router = Router(name="profile")

MAIN_MENU_TEXT = (
    "Главное меню. Выбери раздел кнопкой ниже.\n"
    "[предположение] тексты разделов черновые, согласуем отдельно."
)


class ProfileForm(StatesGroup):
    name = State()
    alias = State()
    contact = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        specialist = await repo.get_specialist_by_telegram_id(conn, message.from_user.id)
        if specialist is None:
            specialist = await repo.create_specialist(conn, message.from_user.id)

        if specialist["status"] == "active" and specialist["display_name"]:
            await state.clear()
            await message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
            return

    await state.set_state(ProfileForm.name)
    await message.answer(
        "Бот считает числа и матрицу, собирает расшифровку и отдельный PDF под твоим именем "
        "как специалиста. Для подписи отчётов нужно твоё имя.\n\n"
        "Как подписывать отчёты твоим клиентам? Напиши имя.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(ProfileForm.name)
async def profile_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Имя не может быть пустым. Напиши имя для подписи отчётов.")
        return
    await state.update_data(display_name=name)
    await state.set_state(ProfileForm.alias)
    await message.answer(
        "Можно добавить рабочий псевдоним (необязательно). Пришли текст или нажми «Пропустить».",
        reply_markup=skip_keyboard(),
    )


@router.message(ProfileForm.alias)
async def profile_alias(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    alias = None if text == "Пропустить" or not text else text
    await state.update_data(alias=alias)
    await state.set_state(ProfileForm.contact)
    await message.answer(
        "Можно указать один контакт для клиентов (необязательно). Пришли текст или нажми «Пропустить».",
        reply_markup=skip_keyboard(),
    )


@router.message(ProfileForm.contact)
async def profile_contact(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    contact = None if text == "Пропустить" or not text else text
    data = await state.get_data()

    pool = get_pool()
    async with pool.acquire() as conn:
        specialist = await repo.get_specialist_by_telegram_id(conn, message.from_user.id)
        await repo.complete_profile(
            conn,
            specialist["id"],
            display_name=data["display_name"],
            alias=data.get("alias"),
            contact_value=contact,
        )

    await state.clear()
    await message.answer(
        "Профиль сохранён. Доступны 2 бесплатных демо-отчёта.",
        reply_markup=main_menu_keyboard(),
    )
    await message.answer(MAIN_MENU_TEXT)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
