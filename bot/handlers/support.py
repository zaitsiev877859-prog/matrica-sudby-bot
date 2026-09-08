"""МН-06 «Поддержка». Учёт обращений (ДН-11) - следующий этап; пока прямая ссылка."""

from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import SUPPORT_URL

router = Router(name="support")


@router.message(F.text == "Поддержка")
async def support_stub(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Написать в поддержку", url=SUPPORT_URL)]]
    )
    await message.answer(
        "Раздел «Поддержка». Учёт обращений внутри бота (ДН-11, ЭК-33) в разработке.\n"
        "Пока - прямая связь по кнопке ниже.",
        reply_markup=keyboard,
    )
