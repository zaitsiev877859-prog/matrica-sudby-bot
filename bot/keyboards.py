from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

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
