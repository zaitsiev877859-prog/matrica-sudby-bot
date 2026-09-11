"""МН-01 «Создать отчёт» - рабочий демо-расчёт по каталогу 11 отчётов.

Направление №Б (переключение хендлера): движок full_matrix.py/pair_compatibility.py
(полная матрица Ладини) вместо старого personal_core.py (черновая 4-точечная
методика 06/07). Соответствие старых кнопок (ot-id) новым записям каталога
reports_catalog_full.py (rf-id) - см. возврат направления.

personal_core.py, старый reports_catalog.py (используется здесь только как
источник заголовков/типов ядра для кнопок) и треугольная диаграмма в
generator.py не удаляются и не вызываются этим хендлером.

Без прав/резерваций/персистентности операции в БД (ДН-02/03/04/09) - это
следующие этапы (см. 04c).
"""

from datetime import date, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.calculations.full_matrix import (
    antifincode,
    base_square,
    derived_points,
    financial_ceiling,
    karmic_tail,
    luck_code,
    millionaire_code,
    personal_destiny,
    planetary_destiny,
    rodovoy_square,
    social_destiny,
    spiritual_destiny,
    year_forecast,
)
from bot.calculations.pair_compatibility import pair_numbers
from bot.content import compatibility
from bot.content.detskaya_matrica import DETSKAYA_MATRICA, get_kruzhki_dlya_arkana
from bot.content.karmicheskiy_hvost_katalog import KARMICHESKIY_HVOST_KATALOG
from bot.content.otnosheniya_markery import OTNOSHENIYA_MARKERY
from bot.content.prednaznachenie import PREDNAZNACHENIE
from bot.content.prognoz_goda import PROGNOZ_GODA
from bot.content.reports_catalog import CHILD_INTRO, REPORTS
from bot.content.tochka_a import TOCHKA_A
from bot.content.tochka_b import TOCHKA_B
from bot.content.tochka_d import TOCHKA_D
from bot.content.tochka_e import TOCHKA_E
from bot.content.tochka_g import TOCHKA_G
from bot.content.tochka_i import TOCHKA_I
from bot.content.tochka_k import TOCHKA_K
from bot.content.tochka_l import TOCHKA_L
from bot.content.tochka_m import TOCHKA_M
from bot.content.tochka_n import TOCHKA_N
from bot.content.tochka_o import TOCHKA_O
from bot.content.tochka_v import TOCHKA_V
from bot.content.tochka_z import TOCHKA_Z
from bot.content.tochka_zh import TOCHKA_ZH
from bot.db import repo
from bot.db.pool import get_pool
from bot.handlers import profile_view, rights, stub_sections, support
from bot.keyboards import MENU_BUTTONS, main_menu_keyboard, report_catalog_keyboard
from bot.pdf.generator import FullMatrixPoints, build_full_matrix_diagram, build_report_pdf

router = Router(name="report_demo")

MIN_YEAR = 1900
MAX_FORECAST_YEAR = 2100
DATE_FORMAT = "%d.%m.%Y"

# Соответствие старых кнопок (ot-id, см. bot/content/reports_catalog.py) новым
# записям каталога направления А (rf-id, bot/content/reports_catalog_full.py).
# Используется только для читаемости кода/возврата - runtime сам вызывает
# нужную функцию рендера по ot-id.
OT_TO_RF = {
    "ot01": "rf01",
    "ot05": "rf05",
    "ot06": "rf06",
    "ot07": "rf07",
    "ot08": "rf08",
    "ot09": "rf09",
    "ot10": "rf10",
    "ot02": "rf02",
    "ot03": "rf03",
    "ot04": "rf04",
    "ot13": "rf13",
}

YA01_ORDER = ("ot01", "ot05", "ot06", "ot07", "ot08", "ot09", "ot10")
PAIR_ORDER = ("ot02", "ot03", "ot04")

OT_PAIR_INTRO = {
    "ot02": "Общая тема, которую эта пара создаёт вместе",
    "ot03": "В романтическом ключе общая тема пары",
    "ot04": "В партнёрстве по делу общая тема пары",
}


class ReportForm(StatesGroup):
    waiting_date_a = State()
    waiting_fio = State()
    waiting_date_b = State()
    waiting_forecast_year = State()
    waiting_all_pair_date = State()


def _parse_date(text: str) -> date | None:
    try:
        parsed = datetime.strptime(text.strip(), DATE_FORMAT).date()
    except ValueError:
        return None
    if parsed.year < MIN_YEAR or parsed > date.today():
        return None
    return parsed


def _gap(label: str, number: int) -> str:
    return f"<b>{label} - №{number}</b>\n[GAP источника: трактовки для этого числа нет в библиотеке.]\n"


def _r_a(n: int) -> str:
    e = TOCHKA_A.get(n)
    if not e:
        return _gap("А (портрет)", n)
    return f"<b>А (портрет) - №{n}, {e['название']}</b>\n{e['описание']}\n"


def _r_b(n: int) -> str:
    e = TOCHKA_B.get(n)
    if not e:
        return _gap("Б (внутренний ресурс)", n)
    return f"<b>Б (внутренний ресурс) - №{n}, {e['name']}</b>\n{e['message']}\n"


def _r_v(n: int) -> str:
    e = TOCHKA_V.get(n)
    if not e:
        return _gap("В (материальная карма)", n)
    extra = e.get("material_karma") or e.get("money_block") or ""
    return f"<b>В (материальная карма) - №{n}, {e['name']}</b>\n{e['soul_tasks']}\n{extra}\n"


def _r_g(n: int) -> str:
    e = TOCHKA_G.get(n)
    if not e:
        return _gap("Г (кармическая задача)", n)
    return f"<b>Г (кармическая задача) - №{n}, {e['name']}</b>\n{e['main_work']}\n{e.get('karmic_tail', '')}\n"


def _r_d(n: int) -> str:
    e = TOCHKA_D.get(n)
    if not e:
        return _gap("Д (зона комфорта)", n)
    parts = [f"<b>Д (зона комфорта) - №{n}, {e['name']}</b>", e["source_of_power"]]
    ep = e.get("entry_point")
    if isinstance(ep, list):
        ep = " / ".join(x for x in ep if x)
    if ep:
        parts.append(f"Точка входа: {ep}")
    return "\n".join(parts) + "\n"


def _r_rodovaya(label: str, catalog: dict, n: int) -> str:
    e = catalog.get(n)
    if not e:
        return _gap(label, n)
    return f"<b>{label} - №{n}, {e['name']}</b>\n{e['clan_karma']}\n{e['healing']}\n"


def _r_k(n: int) -> str:
    e = TOCHKA_K.get(n)
    if not e:
        return _gap("К (вход в отношения)", n)
    return f"<b>К (вход в отношения) - №{n}, {e['name']}</b>\n{e['text']}\n"


def _r_l(n: int) -> str:
    e = TOCHKA_L.get(n)
    if not e:
        return _gap("Л (вход денежного канала)", n)
    parts = [f"<b>Л (вход денежного канала) - №{n}, {e['name']}</b>", e["text"]]
    if e.get("spending"):
        parts.append(f"На что тратить: {e['spending']}")
    return "\n".join(parts) + "\n"


def _r_m(n: int) -> str:
    e = TOCHKA_M.get(n)
    if not e:
        return _gap("М (баланс, общий выход)", n)
    return f"<b>М (баланс) - №{n}, {e['name']}</b>\nДеньги: {e['money_aspect']}\nОтношения: {e['love_aspect']}\n"


def _r_n(n: int) -> str:
    e = TOCHKA_N.get(n)
    if not e:
        return _gap("Н (характер партнёра)", n)
    return f"<b>Н (характер партнёра) - №{n}, {e['name']}</b>\n{e['partner']}\n"


def _r_o(n: int) -> str:
    e = TOCHKA_O.get(n)
    if not e:
        return _gap("О (профессия/сфера)", n)
    parts = [f"<b>О (профессия/сфера) - №{n}, {e['name']}</b>", e["text"]]
    if e.get("professions"):
        parts.append(f"Профессии: {e['professions']}")
    return "\n".join(parts) + "\n"


def _full_matrix_points(sq, rk, dp) -> FullMatrixPoints:
    return FullMatrixPoints(
        a=sq.a, b=sq.b, v=sq.v, g=sq.g, d=sq.d,
        e=rk.e, zh=rk.zh, z=rk.z, i=rk.i,
        k=dp.k, l=dp.l, m=dp.m, n=dp.n, o=dp.o,
    )


def _render_rf01(birth_date: date) -> tuple[str, FullMatrixPoints]:
    sq = base_square(birth_date)
    rk = rodovoy_square(sq)
    dp = derived_points(sq)
    points = _full_matrix_points(sq, rk, dp)
    lines = [
        "<b>Полная личная матрица</b> - расчёт по полной матрице Ладини (движок full_matrix.py)",
        f"Дата: {birth_date.strftime(DATE_FORMAT)}",
        "",
        _r_a(sq.a), _r_b(sq.b), _r_v(sq.v), _r_g(sq.g), _r_d(sq.d),
        _r_rodovaya("Е (духовные задачи мужского рода)", TOCHKA_E, rk.e),
        _r_rodovaya("Ж (духовные задачи женского рода)", TOCHKA_ZH, rk.zh),
        _r_rodovaya("З (материальные задачи женского рода)", TOCHKA_Z, rk.z),
        _r_rodovaya("И (материальные задачи мужского рода)", TOCHKA_I, rk.i),
        _r_k(dp.k), _r_l(dp.l), _r_m(dp.m), _r_n(dp.n), _r_o(dp.o),
        "Черновой расчёт по полной матрице. Комментарий специалиста, права и оплата - следующие этапы.",
    ]
    return "\n".join(lines), points


def _render_rf05(birth_date: date) -> tuple[str, FullMatrixPoints]:
    sq = base_square(birth_date)
    rk = rodovoy_square(sq)
    dp = derived_points(sq)
    points = _full_matrix_points(sq, rk, dp)
    lines = [
        "<b>Детская матрица</b> - черновой расчёт по точкам А и Б ребёнка (движок full_matrix.py)",
        f"Дата: {birth_date.strftime(DATE_FORMAT)}",
        "",
        CHILD_INTRO,
        "",
    ]
    for number, label in ((sq.a, "личные качества (точка А)"), (sq.b, "мотивация и таланты (точка Б)")):
        entry = DETSKAYA_MATRICA.get(number)
        if not entry:
            lines.append(_gap(label, number))
            continue
        lines.append(f"<b>{label} - {entry['name']}</b>")
        lines.append(entry["harakteristika"])
        lines.append(f"Рекомендации: {entry['rekomendacii']}")
        kruzhki = get_kruzhki_dlya_arkana(number)
        if kruzhki:
            lines.append(kruzhki)
        lines.append("")
    lines.append(
        "[предположение] Полная матрица посчитана целиком (движок тот же, что и для полного "
        "отчёта), но в детском разборе показаны только точки А и Б по решению каталога "
        "направления А; графическая схема ниже отражает все точки."
    )
    return "\n".join(lines), points


def _render_rf06(birth_date: date, surname: str, name: str, patronymic: str) -> str:
    sq = base_square(birth_date)
    dp = derived_points(sq)
    afc = antifincode(birth_date)
    mc = millionaire_code(surname, name, patronymic, birth_date)
    lc = luck_code(birth_date)
    fc_total, fc_no_ceiling = financial_ceiling(birth_date)
    lines = [
        "<b>Финансовый отчёт</b> - черновой расчёт (движок full_matrix.py)",
        f"Дата: {birth_date.strftime(DATE_FORMAT)}. ФИО для кода миллионера: {surname} {name} {patronymic}".rstrip(),
        "",
        _r_l(dp.l), _r_o(dp.o), _r_m(dp.m),
        f"<b>Антифинкод</b>: число {afc} - число, которого стоит избегать в финансовых операциях.",
        (
            f"<b>Код миллионера</b>: активация {mc.activation}, судьба {mc.fate}, "
            f"жизненный путь {mc.life_path}, левый корень {mc.left_root}, правый корень {mc.right_root}, "
            f"сердце {mc.heart}, душа {mc.soul}."
        ),
        f"<b>Финансовый код (код удачи)</b>: {lc.as_string()}.",
        f"<b>Финансовый ограничитель</b>: {'планки нет' if fc_no_ceiling else 'планка есть'} (контрольная сумма {fc_total}).",
        "Черновой расчёт для проверки движка. Права и оплата - следующие этапы.",
    ]
    return "\n".join(lines)


def _render_rf07(birth_date: date) -> str:
    sq = base_square(birth_date)
    rk = rodovoy_square(sq)
    pd_ = personal_destiny(sq)
    sd_ = social_destiny(rk)
    dpn = spiritual_destiny(pd_, sd_)
    ppn = planetary_destiny(sd_, dpn)

    def block(number: int, key: str, label: str) -> str:
        entry = PREDNAZNACHENIE.get(number)
        if not entry:
            return _gap(label, number)
        value = entry[key]
        if isinstance(value, dict):
            value = value.get("m") or value.get("zh") or ""
        return f"<b>{label} - №{number}, {entry['name']}</b>\n{value}\n"

    lines = [
        "<b>Предназначение и таланты</b> - черновой расчёт (движок full_matrix.py)",
        f"Дата: {birth_date.strftime(DATE_FORMAT)}",
        "",
        block(pd_.total, "lichnoe", "Личное предназначение"),
        block(sd_.total, "sotsialnoe", "Социальное предназначение"),
        block(dpn, "obshchee_prednaznachenie", "Духовное предназначение"),
        (
            f"[предположение] Планетарное предназначение (число {ppn}) выходит за структуру "
            "библиотеки (в ней только личное/социальное/общее), отдельного текста для него нет."
        ),
    ]
    return "\n".join(lines)


def _render_rf08(birth_date: date) -> str:
    sq = base_square(birth_date)
    dp = derived_points(sq)
    lines = [
        "<b>Профессия и реализация</b> - черновой расчёт (движок full_matrix.py)",
        f"Дата: {birth_date.strftime(DATE_FORMAT)}",
        "",
        _r_o(dp.o),
    ]
    return "\n".join(lines)


def _render_rf09(birth_date: date) -> str:
    sq = base_square(birth_date)
    dp = derived_points(sq)
    lines = [
        "<b>Отношения</b> - черновой расчёт (движок full_matrix.py)",
        f"Дата: {birth_date.strftime(DATE_FORMAT)}",
        "",
        _r_k(dp.k), _r_n(dp.n), _r_m(dp.m),
    ]
    relevant = {sq.a, sq.d, sq.g, dp.k, dp.n, dp.m}
    marker_lines: list[str] = []
    for category in OTNOSHENIYA_MARKERY.values():
        matched = []
        for item in category["items"]:
            if relevant.intersection(item["arcana"]):
                label = item.get("label") or item.get("category")
                matched.append(f"- {label}: {item['text']}")
        if matched:
            marker_lines.append(f"<b>{category['title']}</b> ({category['disclaimer']})")
            marker_lines.extend(matched)
    if marker_lines:
        lines.append("<b>Маркеры в отношениях</b>")
        lines.extend(marker_lines)
    return "\n".join(lines)


def _render_rf10(birth_date: date) -> str:
    sq = base_square(birth_date)
    kt = karmic_tail(sq)
    key = f"{kt.first}-{kt.second}-{kt.third}"
    entry = KARMICHESKIY_HVOST_KATALOG.get(key)
    lines = [
        "<b>Кармический хвост</b> - черновой расчёт (движок full_matrix.py, триплет Г/Д+Г/Г+(Д+Г))",
        f"Дата: {birth_date.strftime(DATE_FORMAT)}, триплет {key}",
        "",
    ]
    if not entry:
        lines.append(
            f"[GAP источника: комбинация {key} не описана в каталоге (в нём разобрано 25 из 27 сочетаний)."
        )
    else:
        lines.append(f"<b>{entry['name']}</b>")
        if entry.get("lesson"):
            lines.append(f"Урок: {entry['lesson']}")
        if entry.get("past_life"):
            lines.append(f"Прошлое воплощение: {entry['past_life']}")
        if entry.get("current_life"):
            lines.append(f"Текущее воплощение: {entry['current_life']}")
        if entry.get("recommendations"):
            lines.append(f"Рекомендации: {entry['recommendations']}")
    return "\n".join(lines)


def _render_rf13(birth_date: date, year: int) -> str:
    yf = year_forecast(birth_date, year)
    lines = [
        "<b>Прогноз на год</b> - черновой расчёт (движок full_matrix.py, 3 энергии года)",
        f"Дата рождения: {birth_date.strftime(DATE_FORMAT)}, год: {year}",
        "",
    ]
    for label, number in (
        ("Базовая энергия", yf.base_energy),
        ("Противофаза", yf.antiphase_energy),
        ("Итоговая энергия", yf.total_energy),
    ):
        entry = PROGNOZ_GODA.get(number)
        if not entry:
            lines.append(_gap(label, number))
            continue
        lines.append(f"<b>{label} - {entry['name']}</b>\n{entry['general']}\n")
    lines.append(
        "[предположение] Показан только общий текст периода; плюс/минус-трактовка не выбирается "
        "автоматически - движок не определяет знак энергии."
    )
    return "\n".join(lines)


def _render_pair(title: str, intro: str, date_a: date, date_b: date) -> str:
    pn = pair_numbers(date_a, date_b)

    def gap_or(catalog: dict, number: int, label: str) -> str:
        value = catalog.get(number)
        if value is None:
            return _gap(label, number)
        return f"<b>{label} - №{number}</b>\n{value}\n"

    lines = [
        f"<b>{title}</b> - черновой расчёт совместимости (движок pair_compatibility.py)",
        f"Участник 1: {date_a.strftime(DATE_FORMAT)}",
        f"Участник 2: {date_b.strftime(DATE_FORMAT)}",
        "",
        f"{intro}.",
        "",
        gap_or(compatibility.FOR_WHAT_MET, pn.ab, "Для чего встретились"),
        gap_or(compatibility.HOW_PAIR_MANIFESTS, pn.ab, "Как проявляется пара"),
        gap_or(compatibility.PROBLEMS_AND_DIFFICULTIES, pn.ab, "Проблемы и трудности"),
        gap_or(compatibility.NEGATIVE_KARMA_IF_TASK_UNMET, pn.ab, "Негативная карма, если задача не решена"),
        gap_or(compatibility.FINANCIAL_WELLBEING_KNMOL, pn.m, "Финансовое благополучие (КНМОЛ)"),
        gap_or(compatibility.COMFORT_ZONE, pn.d, "Зона комфорта"),
        (
            "[предположение] Интерим-решение оркестратора: все три отчёта совместимости "
            "(«Совместимость пары», «Любовная совместимость», «Деловая совместимость») используют "
            "один и тот же набор из 6 библиотек, различается только вступительная фраза."
        ),
    ]
    return "\n".join(lines)


RENDER_YA01_SINGLE = {
    "ot01": _render_rf01,
    "ot05": _render_rf05,
}
RENDER_YA01_TEXT_ONLY = {
    "ot07": _render_rf07,
    "ot08": _render_rf08,
    "ot09": _render_rf09,
    "ot10": _render_rf10,
}


async def _get_specialist_name(telegram_id: int) -> str:
    pool = get_pool()
    async with pool.acquire() as conn:
        specialist = await repo.get_specialist_by_telegram_id(conn, telegram_id)
    if specialist and specialist["display_name"]:
        return specialist["display_name"]
    return "Специалист"


async def _send_report(
    message: Message, title: str, text: str, specialist_name: str, points: FullMatrixPoints | None = None
) -> None:
    """Отправляет текст отчёта в чат и отдельным файлом - черновой PDF (Д02).
    points - точки полной матрицы для графической схемы (только для полного и детского отчётов)."""
    await message.answer(text)
    diagram = build_full_matrix_diagram(points) if points is not None else None
    pdf_bytes = build_report_pdf(title, specialist_name, text.split("\n"), diagram=diagram)
    await message.answer_document(BufferedInputFile(pdf_bytes, filename=f"{title}.pdf"))


async def _send_ya01_report(message: Message, ot_id: str, birth_date: date, specialist_name: str) -> None:
    meta = REPORTS[ot_id]
    if ot_id in RENDER_YA01_SINGLE:
        text_out, points = RENDER_YA01_SINGLE[ot_id](birth_date)
    else:
        text_out = RENDER_YA01_TEXT_ONLY[ot_id](birth_date)
        points = None
    await _send_report(message, meta["title"], text_out, specialist_name, points=points)


async def _handle_menu_interrupt(message: Message, state: FSMContext) -> bool:
    """Если во время сбора дат/года/ФИО для отчёта пришёл текст одной из кнопок главного
    меню - прерываем текущий сценарий вместо попытки разобрать кнопку как ввод."""
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
        "Демо-режим: расчёт и черновой PDF по 11 отчётам работают на полной матрице Ладини, "
        "права/оплата/история - следующие этапы. Выбери отчёт:",
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
        specialist_name = await _get_specialist_name(message.from_user.id)
        await state.update_data(date_a=parsed.isoformat(), specialist_name=specialist_name)
        await state.set_state(ReportForm.waiting_fio)
        await message.answer(
            "Для финансового кода (отчёт «Финансовый отчёт») нужно ФИО клиента. "
            "Формат: Фамилия Имя Отчество, если отчества нет - поставь прочерк вместо него."
        )
        return

    if report_key == "ot06":
        await state.update_data(date_a=parsed.isoformat())
        await state.set_state(ReportForm.waiting_fio)
        await message.answer(
            "Для кода миллионера нужно ФИО клиента. Формат: Фамилия Имя Отчество, "
            "если отчества нет - поставь прочерк вместо него."
        )
        return

    meta = REPORTS[report_key]

    if meta["core"] == "я01":
        specialist_name = await _get_specialist_name(message.from_user.id)
        await state.clear()
        await _send_ya01_report(message, report_key, parsed, specialist_name)
        await message.answer("Готово.", reply_markup=main_menu_keyboard())
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


@router.message(ReportForm.waiting_fio)
async def handle_fio(message: Message, state: FSMContext) -> None:
    if await _handle_menu_interrupt(message, state):
        return

    parts = (message.text or "").strip().split()
    if len(parts) < 2:
        await message.answer(
            "Нужно минимум Фамилия и Имя через пробел. Если отчества нет - третьим словом поставь прочерк."
        )
        return

    surname, name = parts[0], parts[1]
    patronymic = "" if len(parts) < 3 or parts[2] == "-" else " ".join(parts[2:])

    data = await state.get_data()
    report_key = data["report_key"]
    birth_date = date.fromisoformat(data["date_a"])

    if report_key == "ot06":
        specialist_name = await _get_specialist_name(message.from_user.id)
        text_out = _render_rf06(birth_date, surname, name, patronymic)
        await state.clear()
        await _send_report(message, REPORTS["ot06"]["title"], text_out, specialist_name)
        await message.answer("Готово.", reply_markup=main_menu_keyboard())
        return

    # report_key == "all"
    specialist_name = data.get("specialist_name") or await _get_specialist_name(message.from_user.id)
    for ot_id in YA01_ORDER:
        if ot_id == "ot06":
            text_out = _render_rf06(birth_date, surname, name, patronymic)
            await _send_report(message, REPORTS["ot06"]["title"], text_out, specialist_name)
        else:
            await _send_ya01_report(message, ot_id, birth_date, specialist_name)

    await state.set_state(ReportForm.waiting_forecast_year)
    await message.answer(
        "7 отчётов личного ядра отправлены выше. Теперь прогноз (отчёт 13) - "
        "на какой год посчитать? Введи год, например 2026, или напиши «Пропустить»."
    )


@router.message(ReportForm.waiting_date_b)
async def handle_date_b(message: Message, state: FSMContext) -> None:
    if await _handle_menu_interrupt(message, state):
        return

    parsed = _parse_date(message.text or "")
    if parsed is None:
        await message.answer(f"Не получилось разобрать дату. Формат: ДД.ММ.ГГГГ, не раньше {MIN_YEAR} года и не в будущем.")
        return

    data = await state.get_data()
    report_key = data["report_key"]
    date_a = date.fromisoformat(data["date_a"])
    meta = REPORTS[report_key]

    text_out = _render_pair(meta["title"], OT_PAIR_INTRO[report_key], date_a, parsed)
    specialist_name = await _get_specialist_name(message.from_user.id)
    await state.clear()
    await _send_report(message, meta["title"], text_out, specialist_name)
    await message.answer("Готово.", reply_markup=main_menu_keyboard())


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

    text_out = _render_rf13(birth_date, int(text))

    if report_key == "all":
        specialist_name = data.get("specialist_name") or await _get_specialist_name(message.from_user.id)
        await _send_report(message, REPORTS["ot13"]["title"], text_out, specialist_name)
        await state.set_state(ReportForm.waiting_all_pair_date)
        await message.answer(
            "Прогноз отправлен выше. Хочешь добавить дату второго человека для 3 отчётов "
            "совместимости? Пришли дату ДД.ММ.ГГГГ или напиши «Пропустить»."
        )
        return

    specialist_name = await _get_specialist_name(message.from_user.id)
    await state.clear()
    await _send_report(message, REPORTS["ot13"]["title"], text_out, specialist_name)
    await message.answer("Готово.", reply_markup=main_menu_keyboard())


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

    specialist_name = data.get("specialist_name") or await _get_specialist_name(message.from_user.id)
    for ot_id in PAIR_ORDER:
        meta = REPORTS[ot_id]
        text_out = _render_pair(meta["title"], OT_PAIR_INTRO[ot_id], date_a, parsed)
        await _send_report(message, meta["title"], text_out, specialist_name)

    await state.clear()
    await message.answer("Все 11 отчётов отправлены.", reply_markup=main_menu_keyboard())
