"""МН-01 «Создать отчёт» - рабочий демо-расчёт ОТ-01 (Полная личная матрица).

Только расчётный движок (ядро Я01 из 07-chernovaya-sborka-otchetov.md) и черновые
тексты 06-teksty-lichnoe-yadro.md. Без прав/резерваций/PDF/персистентности операции -
это следующие этапы (см. 04c). Остальные 10 отчётов и ядра Я02/Я03 подключаются позже.
"""

from datetime import date, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.calculations.personal_core import karmic_debt_numbers, personal_core_points
from bot.content.arcana import ARCANA
from bot.content.karmic_debt import KARMIC_DEBT
from bot.keyboards import main_menu_keyboard

router = Router(name="report_demo")

MIN_YEAR = 1900
DATE_FORMAT = "%d.%m.%Y"

POINT_LABELS = (
    ("day", "День"),
    ("motive", "Мотив"),
    ("experience", "Опыт"),
    ("synthesis", "Синтез"),
)


class ReportForm(StatesGroup):
    waiting_date = State()


@router.message(F.text == "Создать отчёт")
async def start_report(message: Message, state: FSMContext) -> None:
    await state.set_state(ReportForm.waiting_date)
    await message.answer(
        "Демо-режим: пока считается только «Полная личная матрица» (ОТ-01) по одной дате.\n"
        "Остальные 10 отчётов, выбор нескольких отчётов и права появятся на следующих этапах.\n\n"
        "Введи дату рождения в формате ДД.ММ.ГГГГ, например 15.06.1990."
    )


@router.message(ReportForm.waiting_date)
async def handle_date(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    try:
        parsed = datetime.strptime(text, DATE_FORMAT).date()
    except ValueError:
        await message.answer("Не получилось разобрать дату. Формат: ДД.ММ.ГГГГ, например 15.06.1990.")
        return

    if parsed.year < MIN_YEAR or parsed > date.today():
        await message.answer(f"Дата должна быть не раньше {MIN_YEAR} года и не в будущем.")
        return

    points = personal_core_points(parsed)
    karmic = karmic_debt_numbers(parsed)

    lines = [
        "<b>Полная личная матрица</b> - черновой расчёт (методика 06/07, тексты не финальные)",
        f"Дата: {parsed.strftime(DATE_FORMAT)}",
        "",
    ]
    for key, label in POINT_LABELS:
        number = getattr(points, key)
        arcanum = ARCANA[number]
        lines.append(f"<b>{label} - №{number}, {arcanum['name']}</b>")
        lines.append(f"Ресурс: {arcanum['resource']}")
        lines.append(f"Грань напряжения: {arcanum['tension']}")
        lines.append("")

    if karmic:
        lines.append("<b>Кармические числа (для отчёта 10)</b>")
        for number in karmic:
            debt = KARMIC_DEBT[number]
            lines.append(f"№{number}, {debt['title']}: {debt['theme']}")
        lines.append("")

    lines.append("Это проверка расчётного движка. PDF, комментарий специалиста, права и оплата подключатся отдельно.")

    await state.clear()
    await message.answer("\n".join(lines), reply_markup=main_menu_keyboard())
