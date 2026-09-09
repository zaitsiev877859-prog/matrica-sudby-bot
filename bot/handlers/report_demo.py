"""МН-01 «Создать отчёт» - рабочий демо-расчёт по каталогу 11 отчётов.

Только расчётный движок (Я01/Я02 из 07-chernovaya-sborka-otchetov.md, Я03 из
02c-metodika-klassicheskaya-numerologiya.md) и черновые тексты 06-teksty-lichnoe-yadro.md.
Без прав/резерваций/PDF/персистентности операции - это следующие этапы (см. 04c).
Выбор только одного отчёта за раз; несколько отчётов в одной операции - следующий шаг.
"""

from datetime import date, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.calculations.personal_core import (
    karmic_debt_numbers,
    pair_number,
    personal_core_points,
    personal_year,
)
from bot.content.arcana import ARCANA
from bot.content.karmic_debt import KARMIC_DEBT
from bot.content.personal_year import PERSONAL_YEAR
from bot.content.reports_catalog import CHILD_INTRO, POINT_LABELS, REPORTS
from bot.handlers import profile_view, rights, stub_sections, support
from bot.keyboards import MENU_BUTTONS, main_menu_keyboard, report_catalog_keyboard

router = Router(name="report_demo")

MIN_YEAR = 1900
MAX_FORECAST_YEAR = 2100
DATE_FORMAT = "%d.%m.%Y"


class ReportForm(StatesGroup):
    waiting_date_a = State()
    waiting_date_b = State()
    waiting_forecast_year = State()
    waiting_all_pair_date = State()


YA01_KEYS = [key for key, meta in REPORTS.items() if meta["core"] == "я01"]
YA02_KEYS = [key for key, meta in REPORTS.items() if meta["core"] == "я02"]


def _parse_date(text: str) -> date | None:
    try:
        parsed = datetime.strptime(text.strip(), DATE_FORMAT).date()
    except ValueError:
        return None
    if parsed.year < MIN_YEAR or parsed > date.today():
        return None
    return parsed


def _render_ya01(meta: dict, birth_date: date) -> str:
    points = personal_core_points(birth_date)
    karmic = karmic_debt_numbers(birth_date)

    lines = [
        f"<b>{meta['title']}</b> - черновой расчёт (методика 06/07)",
        f"Дата: {birth_date.strftime(DATE_FORMAT)}",
        "",
    ]

    if meta.get("child"):
        lines.append(CHILD_INTRO)
        lines.append("")

    if meta.get("karmic_only"):
        if not karmic:
            lines.append("В расчёте по этой дате чисел кармического долга (13/14/16/19) не найдено.")
        else:
            lines.append("<b>Кармические числа</b>")
            for number in karmic:
                debt = KARMIC_DEBT[number]
                lines.append(f"№{number}, {debt['title']}")
                lines.append(f"Тема: {debt['theme']}")
                lines.append(f"Как проявляется: {debt['manifestation']}")
                lines.append("")
    else:
        for key in meta["points"]:
            number = getattr(points, key)
            arcanum = ARCANA[number]
            lines.append(f"<b>{POINT_LABELS[key]} - №{number}, {arcanum['name']}</b>")
            lines.append(f"Ресурс: {arcanum['resource']}")
            lines.append(f"Грань напряжения: {arcanum['tension']}")
            lines.append("")
        if meta.get("full") and karmic:
            lines.append("<b>Кармические числа (дополнительно)</b>")
            for number in karmic:
                lines.append(f"№{number}, {KARMIC_DEBT[number]['title']}")
            lines.append("")

    lines.append("Черновой расчёт для проверки движка. PDF, комментарий специалиста, права и оплата - следующие этапы.")
    return "\n".join(lines)


def _render_ya02(meta: dict, date_a: date, date_b: date) -> str:
    points_a = personal_core_points(date_a)
    points_b = personal_core_points(date_b)
    number = pair_number(points_a.synthesis, points_b.synthesis)
    arcanum = ARCANA[number]

    lines = [
        f"<b>{meta['title']}</b> - черновой расчёт (методика 07)",
        f"Участник 1: {date_a.strftime(DATE_FORMAT)} (Синтез №{points_a.synthesis}, {ARCANA[points_a.synthesis]['name']})",
        f"Участник 2: {date_b.strftime(DATE_FORMAT)} (Синтез №{points_b.synthesis}, {ARCANA[points_b.synthesis]['name']})",
        "",
        f"<b>Число Пары - №{number}, {arcanum['name']}</b>",
        f"{meta['theme_intro']}: {arcanum['resource']}",
        f"Грань напряжения: {arcanum['tension']}",
        "",
    ]

    if points_a.synthesis == points_b.synthesis:
        lines.append(
            "Точки Синтеза совпадают: сильное взаимопонимание, риск однобокости - "
            "никто не восполняет слепые зоны другого."
        )
    else:
        lines.append(
            "Точки Синтеза расходятся: партнёры видят одну и ту же ситуацию по-разному, "
            "потенциал - в дополнении, а не в совпадении."
        )
    lines.append("")
    lines.append(
        "[предположение] Здесь показано упрощённое двоичное сравнение (совпадают/расходятся); "
        "средняя градация «близки» из 07 требует числового порога, который ещё не определён."
    )
    lines.append("Черновой расчёт для проверки движка. PDF, права и оплата - следующие этапы.")
    return "\n".join(lines)


def _render_ya03(birth_date: date, year: int) -> str:
    number = personal_year(birth_date, year)
    info = PERSONAL_YEAR[number]

    lines = [
        "<b>Прогноз на год</b> - черновой расчёт (персональный год, 02c/07)",
        f"Дата рождения: {birth_date.strftime(DATE_FORMAT)}, год: {year}",
        "",
        f"<b>Персональный год {number} - «{info['title']}»</b>",
        f"Тема года: {info['theme']}",
        f"На что обратить внимание: {info['watch']}",
        "",
        "Черновой расчёт для проверки движка. PDF, права и оплата - следующие этапы.",
    ]
    return "\n".join(lines)


async def _handle_menu_interrupt(message: Message, state: FSMContext) -> bool:
    """Если во время сбора дат/года для отчёта пришёл текст одной из кнопок главного
    меню - прерываем текущий сценарий вместо попытки разобрать кнопку как дату/год."""
    text = message.text
    if text not in MENU_BUTTONS:
        return False

    await state.clear()

    if text == "Создать отчёт":
        await open_catalog(message, state)
    elif text == "Профиль":
        await profile_view.show_profile(message)
    elif text == "Мои права":
        await rights.show_rights(message)
    elif text == "Поддержка":
        await support.support_stub(message)
    else:  # История, Тарифы - заглушки
        await stub_sections.section_stub(message)
    return True


@router.message(F.text == "Создать отчёт")
async def open_catalog(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Демо-режим: расчёт по 11 отчётам работает, PDF/права/несколько отчётов сразу - "
        "следующие этапы. Выбери отчёт:",
        reply_markup=report_catalog_keyboard(),
    )


@router.callback_query(F.data.startswith("report:"))
async def choose_report(callback: CallbackQuery, state: FSMContext) -> None:
    report_key = callback.data.split(":", 1)[1]

    if report_key != "all" and report_key not in REPORTS:
        await callback.answer("Неизвестный отчёт.", show_alert=True)
        return

    await callback.answer()
    await state.update_data(report_key=report_key)
    await state.set_state(ReportForm.waiting_date_a)

    if report_key == "all":
        await callback.message.answer(
            "Все 11 отчётов сразу. Сначала дата рождения основного человека - по ней "
            "посчитаются 7 отчётов личного ядра. Формат ДД.ММ.ГГГГ."
        )
        return

    meta = REPORTS[report_key]
    if meta["core"] == "я02":
        await callback.message.answer(
            f"«{meta['title']}». Введи дату рождения первого участника в формате ДД.ММ.ГГГГ."
        )
    elif meta["core"] == "я03":
        await callback.message.answer(
            f"«{meta['title']}». Введи дату рождения в формате ДД.ММ.ГГГГ."
        )
    else:
        await callback.message.answer(
            f"«{meta['title']}». Введи дату рождения в формате ДД.ММ.ГГГГ, например 15.06.1990."
        )


@router.message(ReportForm.waiting_date_a)
async def handle_date_a(message: Message, state: FSMContext) -> None:
    if await _handle_menu_interrupt(message, state):
        return

    parsed = _parse_date(message.text or "")
    if parsed is None:
        await message.answer(f"Не получилось разобрать дату. Формат: ДД.ММ.ГГГГ, не раньше {MIN_YEAR} года и не в будущем.")
        return

    data = await state.get_data()
    report_key = data["report_key"]

    if report_key == "all":
        await state.update_data(date_a=parsed.isoformat())
        for key in YA01_KEYS:
            await message.answer(_render_ya01(REPORTS[key], parsed))
        await state.set_state(ReportForm.waiting_forecast_year)
        await message.answer(
            "7 отчётов личного ядра отправлены выше. Теперь прогноз (отчёт 13) - "
            "на какой год посчитать? Введи год, например 2026, или напиши «Пропустить»."
        )
        return

    meta = REPORTS[report_key]

    if meta["core"] == "я01":
        text = _render_ya01(meta, parsed)
        await state.clear()
        await message.answer(text, reply_markup=main_menu_keyboard())
        return

    if meta["core"] == "я02":
        await state.update_data(date_a=parsed.isoformat())
        await state.set_state(ReportForm.waiting_date_b)
        await message.answer("Теперь дата рождения второго участника, формат ДД.ММ.ГГГГ.")
        return

    # я03: дата рождения получена, спрашиваем год прогноза
    await state.update_data(date_a=parsed.isoformat())
    await state.set_state(ReportForm.waiting_forecast_year)
    await message.answer("На какой год посчитать прогноз? Введи год, например 2026.")


@router.message(ReportForm.waiting_date_b)
async def handle_date_b(message: Message, state: FSMContext) -> None:
    if await _handle_menu_interrupt(message, state):
        return

    parsed = _parse_date(message.text or "")
    if parsed is None:
        await message.answer(f"Не получилось разобрать дату. Формат: ДД.ММ.ГГГГ, не раньше {MIN_YEAR} года и не в будущем.")
        return

    data = await state.get_data()
    meta = REPORTS[data["report_key"]]
    date_a = date.fromisoformat(data["date_a"])

    text = _render_ya02(meta, date_a, parsed)
    await state.clear()
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(ReportForm.waiting_forecast_year)
async def handle_forecast_year(message: Message, state: FSMContext) -> None:
    if await _handle_menu_interrupt(message, state):
        return

    text = (message.text or "").strip()
    data = await state.get_data()
    report_key = data["report_key"]
    birth_date = date.fromisoformat(data["date_a"])

    if report_key == "all" and text == "Пропустить":
        await state.set_state(ReportForm.waiting_all_pair_date)
        await message.answer(
            "Прогноз пропущен. Хочешь добавить дату второго человека для 3 отчётов "
            "совместимости? Пришли дату ДД.ММ.ГГГГ или напиши «Пропустить»."
        )
        return

    if not text.isdigit() or not (MIN_YEAR <= int(text) <= MAX_FORECAST_YEAR):
        hint = ", или «Пропустить»." if report_key == "all" else "."
        await message.answer(f"Введи год числом, от {MIN_YEAR} до {MAX_FORECAST_YEAR}{hint}")
        return

    text_out = _render_ya03(birth_date, int(text))

    if report_key == "all":
        await message.answer(text_out)
        await state.set_state(ReportForm.waiting_all_pair_date)
        await message.answer(
            "Прогноз отправлен выше. Хочешь добавить дату второго человека для 3 отчётов "
            "совместимости? Пришли дату ДД.ММ.ГГГГ или напиши «Пропустить»."
        )
        return

    await state.clear()
    await message.answer(text_out, reply_markup=main_menu_keyboard())


@router.message(ReportForm.waiting_all_pair_date)
async def handle_all_pair_date(message: Message, state: FSMContext) -> None:
    if await _handle_menu_interrupt(message, state):
        return

    text = (message.text or "").strip()
    data = await state.get_data()
    date_a = date.fromisoformat(data["date_a"])

    if text == "Пропустить":
        await state.clear()
        await message.answer(
            "Отчёты совместимости пропущены. Все выбранные отчёты отправлены.",
            reply_markup=main_menu_keyboard(),
        )
        return

    parsed = _parse_date(text)
    if parsed is None:
        await message.answer(
            f"Не получилось разобрать дату. Формат: ДД.ММ.ГГГГ, не раньше {MIN_YEAR} года "
            "и не в будущем, или «Пропустить»."
        )
        return

    for key in YA02_KEYS:
        await message.answer(_render_ya02(REPORTS[key], date_a, parsed))

    await state.clear()
    await message.answer("Все 11 отчётов отправлены.", reply_markup=main_menu_keyboard())
