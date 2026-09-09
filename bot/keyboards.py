from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.content.reports_catalog import REPORTS

MENU_BUTTONS = [
    "Создать отчёт",
    "История",
    "Мои права",
    "Тарифы",
    "Профиль",
    "Поддержка",
]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for text in MENU_BUTTONS:
        builder.button(text=text)
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)


def skip_keyboard(button_text: str = "Пропустить") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=button_text)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def report_catalog_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, meta in REPORTS.items():
        builder.button(text=meta["title"], callback_data=f"report:{key}")
    builder.adjust(1)
    return builder.as_markup()
