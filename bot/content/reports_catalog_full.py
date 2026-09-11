"""Каталог отчётов на полной матрице Ладини (Направление №А).

Маппинг «отчёт -> какие точки/формулы full_matrix.py и какие библиотеки
текстов участвуют». Не движок и не сборщик PDF - только реестр для
направления «переключение хендлера» (Б), которое будет переписывать
report_demo.py на базе full_matrix.py вместо personal_core.py.

РЕШЕНИЕ ПО СОСТАВУ (сверка 03e-decisions-approved.md vs PROJECT-MEMORY.md,
раздел 4, см. возврат направления): рабочий список - 12 отчётов = 13-й
утверждённый каталог 03e-decisions-approved.md БЕЗ отчёта №12 «Здоровье и
чакры» (подтверждённо исключён и в PROJECT-MEMORY, и в
08-polnaya-matrica-progress.md: «формулу дальше не ищем»). Отчёт №11
«Родовые программы» ОСТАВЛЕН в каталоге с явной пометкой GAP по формуле
(кандидат-формула найдена в 08-polnaya-matrica-progress.md ПОСЛЕ решения
PROJECT-MEMORY об исключении; rodovye_programmy_katalog.py как каталог
архетипов уже существует). 11-отчётный список из PROJECT-MEMORY.md
описывает старую 4-точечную методику (personal_core.py/06/07), это другая
система координат и не отменяет 12-отчётный список здесь.

Статусы:
    "готов"    - формула(ы) подтверждены источниками (full_matrix.py),
                 контент-библиотеки существуют, точечные GAP внутри
                 отдельных библиотек (пропуски аркана 1-2 и т.п.)
                 перечислены в примечании, но не блокируют отчёт целиком.
    "GAP"      - либо формула привязки к точкам матрицы не найдена
                 (родовые программы, особые тройки совместимости), либо
                 не решено распределение готового контента между
                 несколькими отчётами (любовная/деловая совместимость).

Ничего из формул full_matrix.py/pair_compatibility.py здесь не
пересчитывается и не меняется, тексты content-файлов не редактируются -
это только реестр ссылок на уже существующий код.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReportEntry:
    id: str
    title: str
    core_formulas: tuple[str, ...]  # "модуль.функция/класс" из full_matrix.py / pair_compatibility.py
    content_libraries: tuple[str, ...]  # "модуль.ИМЯ_СЛОВАРЯ" из bot.content
    status: str  # "готов" | "GAP"
    note: str = ""


REPORTS_FULL: dict[str, ReportEntry] = {

    "rf01": ReportEntry(
        id="rf01",
        title="Полная личная матрица",
        core_formulas=(
            "full_matrix.base_square (А,Б,В,Г,Д)",
            "full_matrix.derived_points (К,Л,М,Н,О)",
            "full_matrix.rodovoy_square (Е,Ж,З,И)",
        ),
        content_libraries=(
            "tochka_a.TOCHKA_A", "tochka_b.TOCHKA_B", "tochka_v.TOCHKA_V",
            "tochka_g.TOCHKA_G", "tochka_d.TOCHKA_D", "tochka_e.TOCHKA_E",
            "tochka_zh.TOCHKA_ZH", "tochka_z.TOCHKA_Z", "tochka_i.TOCHKA_I",
            "tochka_k.TOCHKA_K", "tochka_l.TOCHKA_L", "tochka_m.TOCHKA_M",
            "tochka_n.TOCHKA_N", "tochka_o.TOCHKA_O",
        ),
        status="готов",
        note=(
            "Полный разбор всех 14 позиций А-О. Внутри отдельных библиотек "
            "есть точечные GAP первоисточника (не отчёта): tochka_v аркан 1, "
            "tochka_d арканы 1-2, tochka_k/n/m арканы 1-2 («в этой точке не "
            "бывает» по формуле). tochka_e идентична tochka_i, tochka_zh "
            "идентична tochka_z - источник не различает Е/И и Ж/З текстуально "
            "(см. докстринги файлов), это не ошибка извлечения."
        ),
    ),

    "rf02": ReportEntry(
        id="rf02",
        title="Совместимость пары",
        core_formulas=(
            "pair_compatibility.pair_number_ab [предположение, подтверждено пользователем 2026-09-11]",
            "pair_compatibility.pair_number_d [предположение, подтверждено пользователем 2026-09-11]",
            "pair_compatibility.pair_number_m [предположение с пониженной уверенностью]",
        ),
        content_libraries=(
            "compatibility.FOR_WHAT_MET",
            "compatibility.HOW_PAIR_MANIFESTS",
            "compatibility.FINANCIAL_WELLBEING_KNMOL",
            "compatibility.PROBLEMS_AND_DIFFICULTIES",
            "compatibility.NEGATIVE_KARMA_IF_TASK_UNMET",
            "compatibility.COMFORT_ZONE",
            "compatibility.SPECIAL_PROGRAMS [GAP по формуле]",
        ),
        status="готов",
        note=(
            "Формула единого «числа пары» - гипотеза, не факт источника "
            "(см. pair_compatibility.py докстринг), подтверждена пользователем "
            "2026-09-11. SPECIAL_PROGRAMS (особые тройки 13-16-3, 19-7, "
            "19-8-7, 5-14-19) - GAP: формула привязки тройки к точкам "
            "матрицы двух партнёров не найдена, включено по прямому "
            "указанию задания, без домысливания формулы."
        ),
    ),

    "rf03": ReportEntry(
        id="rf03",
        title="Любовная совместимость",
        core_formulas=(
            "pair_compatibility.pair_number_ab / _d / _m (та же механика, что rf02)",
        ),
        content_libraries=(
            "compatibility.* (тот же набор 6 библиотек + SPECIAL_PROGRAMS, что и rf02)",
        ),
        status="GAP",
        note=(
            "GAP по сборке, не по формуле: compatibility.py докстринг прямо "
            "пишет, что распределение 6 библиотек и особых программ между "
            "отчётами «Совместимость пары» / «Любовная совместимость» / "
            "«Деловая совместимость» - решение направления «сборка», не "
            "принято. Ядро расчёта то же, что у rf02."
        ),
    ),

    "rf04": ReportEntry(
        id="rf04",
        title="Деловая совместимость",
        core_formulas=(
            "pair_compatibility.pair_number_ab / _d / _m (та же механика, что rf02)",
        ),
        content_libraries=(
            "compatibility.* (тот же набор 6 библиотек + SPECIAL_PROGRAMS, что и rf02)",
        ),
        status="GAP",
        note="GAP по сборке - см. примечание rf03, тот же нерешённый вопрос.",
    ),

    "rf05": ReportEntry(
        id="rf05",
        title="Детская матрица",
        core_formulas=(
            "full_matrix.base_square (используются только А и Б ребёнка)",
        ),
        content_libraries=(
            "detskaya_matrica.DETSKAYA_MATRICA",
            "detskaya_matrica.DETSKAYA_MATRICA_KRUZHKI",
            "drk.DRK [доп. материал для полного варианта, не собран в движок]",
        ),
        status="готов",
        note=(
            "detskaya_matrica.py реализует только «сокращённый вариант» "
            "источника (только точки А и Б). Полный 7-8-подразделный "
            "вариант («Детская матрица 1» из 08-progress: Личные качества, "
            "Отношения с родителями ДРК+МЖ, Таланты Б/Е/Ж, Предназначение "
            "детское, Мышление В/Г и т.д.) в движке не собран - GAP по "
            "объёму, не по формуле базовой части. drk.py (детско-"
            "родительская карма, индексируется по точке А) готов как "
            "библиотека, но не подключён ни к одному расчёту."
        ),
    ),

    "rf06": ReportEntry(
        id="rf06",
        title="Финансовый отчёт",
        core_formulas=(
            "full_matrix.derived_points (Л,О,М - денежная линия ЛОМ)",
            "full_matrix.antifincode",
            "full_matrix.millionaire_code",
            "full_matrix.luck_code",
            "full_matrix.financial_ceiling",
        ),
        content_libraries=(
            "tochka_l.TOCHKA_L (поле spending)",
            "tochka_o.TOCHKA_O (поле professions)",
            "tochka_m.TOCHKA_M (поле money_aspect)",
        ),
        status="готов",
        note=(
            "3 независимые формулы (антифинкод, код миллионера, финансовый "
            "код) - не часть 22-арканной матрицы, отдельные ведущие "
            "источники (30/31/32), все подтверждены контрольными примерами "
            "в full_matrix.py."
        ),
    ),

    "rf07": ReportEntry(
        id="rf07",
        title="Предназначение и таланты",
        core_formulas=(
            "full_matrix.personal_destiny (Линия Земли А+В, Линия Неба Б+Г)",
            "full_matrix.social_destiny (линия отца Е+И, линия матери Ж+З)",
            "full_matrix.spiritual_destiny",
            "full_matrix.planetary_destiny",
        ),
        content_libraries=(
            "prednaznachenie.PREDNAZNACHENIE (поля lichnoe/sotsialnoe/obshchee_prednaznachenie)",
        ),
        status="готов",
        note="Формулы подтверждены 2 независимыми источниками (21, 35).",
    ),

    "rf08": ReportEntry(
        id="rf08",
        title="Профессия и реализация",
        core_formulas=(
            "full_matrix.derived_points (точка О = М+Л)",
        ),
        content_libraries=(
            "tochka_o.TOCHKA_O (поле professions, источник 41)",
        ),
        status="готов",
        note=(
            "08-polnaya-matrica-progress.md: числовой пример источника 41 "
            "«согласуется с О=М+Л» - это проверка примера, отдельной новой "
            "формулы для профессии нет, используется уже известная точка О."
        ),
    ),

    "rf09": ReportEntry(
        id="rf09",
        title="Отношения",
        core_formulas=(
            "full_matrix.derived_points (К,Н,М - линия любви КНМ)",
            "full_matrix.base_square (точка А - портрет, точка Г - кармический хвостик)",
        ),
        content_libraries=(
            "tochka_k.TOCHKA_K", "tochka_n.TOCHKA_N", "tochka_m.TOCHKA_M (поле love_aspect)",
            "otnosheniya_markery.OTNOSHENIYA_MARKERY (5 маркерных каталогов внутри: Абьюзеры/Изменщики/Ревнивцы/Холостяки/Эмоциональные качели)",
        ),
        status="готов",
        note=(
            "Маркерные каталоги otnosheniya_markery.py опираются на К/Н/М, "
            "точку А и точку Г - привязка дословно указана в 4 из 5 "
            "источников (в «Ревнивцы.pdf» - без слова «Абьюзеры», но по "
            "сути идентична)."
        ),
    ),

    "rf10": ReportEntry(
        id="rf10",
        title="Кармический хвост",
        core_formulas=(
            "full_matrix.karmic_tail (триплет [Г, Д+Г, Г+(Д+Г)])",
        ),
        content_libraries=(
            "karmicheskiy_hvost_katalog.KARMICHESKIY_HVOST_KATALOG (25 архетипов, 26 кодов-триплетов)",
        ),
        status="готов",
        note=(
            "Формула Ладини (не классические 13/14/16/19) - решение "
            "зафиксировано и не пересматривается. Подтверждена 3 "
            "независимыми источниками (34, 36 и текстовый источник "
            "каталога)."
        ),
    ),

    "rf11": ReportEntry(
        id="rf11",
        title="Родовые программы",
        core_formulas=(
            "ФОРМУЛА НЕ РЕАЛИЗОВАНА В full_matrix.py",
        ),
        content_libraries=(
            "rodovye_programmy_katalog.RODOVYE_PROGRAMMY_KATALOG (~61 уникальная запись после схлопывания 4 дублей из 65 исходных)",
        ),
        status="GAP",
        note=(
            "GAP по формуле, включено по прямому указанию задания, формула "
            "не выдумывается. rodovye_programmy_katalog.py докстринг: "
            "источник «НИГДЕ в этом уроке не объясняет явно, из каких "
            "именно позиций расчёта складывается тройка чисел». "
            "08-polnaya-matrica-progress.md называет вероятного (не "
            "подтверждённого) кандидата: «вершина родового квадрата + "
            "сумма всех 4 вершин, тем же способом [что кармический хвост]» "
            "- нужна проверка на реальных кейсах против каталога 29, не "
            "реализовано."
        ),
    ),

    "rf13": ReportEntry(
        id="rf13",
        title="Прогноз на год",
        core_formulas=(
            "full_matrix.year_forecast (3 энергии: базовая, противофаза, сумма)",
        ),
        content_libraries=(
            "prognoz_goda.PROGNOZ_GODA (22 аркана, поля name/general/plus/minus)",
        ),
        status="готов",
        note=(
            "[непроверено] базовая энергия года: full_matrix.py докстринг - "
            "источник сам пишет «точный алгоритм... не до конца ясен», "
            "реализована единственная гипотеза конспекта, проверена только "
            "на отвлечённой иллюстрации, не на реальном кейсе с известным "
            "прогнозом. Противофаза и сумма - подтверждено, явная "
            "арифметика."
        ),
    ),
}


# 03e-нумерация (1-13) отчёта №12 «Здоровье и чакры» сюда сознательно не
# включена ни как rf-запись, ни как GAP-заглушка: решение исключить отчёт
# принято и не пересматривается (PROJECT-MEMORY.md, 08-polnaya-matrica-progress.md,
# раздел «Решение по открытым вопросам №3») - формулу дальше не ищем.
EXCLUDED_REPORTS_NOTE = (
    "Отчёт «Здоровье и чакры» (позиция 12 из 13 в 03e-decisions-approved.md) "
    "исключён из этого каталога решением заказчика, формула не ищется. "
    "Библиотека текстов существует вне зоны этого каталога "
    "(26-karta-zdorovya.md), но не подключена ни к одной content-библиотеке "
    "bot/bot/content."
)
