"""Заглушки МН-01, МН-02, МН-04 - каталог, история, тарифы.
Полная логика появится на этапах 3 (сценарии/генерация) и 4 (оплата Kaspi) плана работ.
"""

from aiogram import F, Router
from aiogram.types import Message

router = Router(name="stub_sections")

STUBS = {
    "История": "Список прошлых операций и скачивание PDF появятся вместе с расчётным контуром.",
    "Тарифы": "Покупка тарифов и разбор Kaspi-квитанции появятся отдельным этапом.",
}


@router.message(F.text.in_(STUBS.keys()))
async def section_stub(message: Message) -> None:
    await message.answer(f"Раздел «{message.text}» в разработке.\n{STUBS[message.text]}")
