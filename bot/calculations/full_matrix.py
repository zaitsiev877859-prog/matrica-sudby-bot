"""Расчётный движок полной матрицы Ладини (Направление №1).

Источники (конспекты в C:\\Users\\ww\\Desktop\\матрица судьбы\\):
09 (8 базовых точек + К/Л/М/Н/О), 13 и 35/36 (родовой квадрат Е/Ж/З/И),
21 и 35 (предназначения), 22 (прогноз года), 28 (гуны и касты),
30 (антифинкод), 31 (код миллионера), 32 (финансовый код),
34 и 36 (кармический хвост).

Не трогает и не переопределяет bot.calculations.personal_core (независимый
черновой fallback Я01/Я02/Я03). Переиспользует только редукцию из
bot.calculations.reduction (reduce_arcana, reduce_classical, digit_sum).

Совместимость (отчёты 2-4) и здоровье/чакры сюда не входят - решено в
другом направлении, см. 08-polnaya-matrica-progress.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from bot.calculations.reduction import digit_sum, reduce_arcana, reduce_classical


def _digit_root(n: int) -> int:
    """Сведение к одной цифре без остановки на мастер-числах.

    Используется там, где источник явно НЕ упоминает мастер-числа 11/22/33
    (касты - 28, антифинкод - 30, финансовый код - 32). Для «Кода
    миллионера» (31), где мастер-числа явно сохраняются, используется
    reduce_classical.
    """
    n = abs(n)
    while n > 9:
        n = digit_sum(n)
    return n


# ---------------------------------------------------------------------------
# 1. Базовые точки личного квадрата А-Д + производные К/Л/М/Н/О
# Источник: 09-formuly-8-tochek-i-arifmetika.md
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaseSquare:
    a: int
    b: int
    v: int
    g: int
    d: int


def base_square(birth_date: date) -> BaseSquare:
    """А=день, Б=месяц, В=сумма цифр года, Г=А+Б+В, Д=А+Б+В+Г.

    Контрольный пример (23.01.1987, источник 35): А=5, Б=1, В=7, Г=13, Д=8.
    Статус: подтверждено.
    """
    a = reduce_arcana(birth_date.day)
    b = reduce_arcana(birth_date.month)
    v = reduce_arcana(digit_sum(birth_date.year))
    g = reduce_arcana(a + b + v)
    d = reduce_arcana(a + b + v + g)
    return BaseSquare(a=a, b=b, v=v, g=g, d=d)


@dataclass(frozen=True)
class DerivedPoints:
    k: int
    l: int
    m: int
    n: int
    o: int


def derived_points(sq: BaseSquare) -> DerivedPoints:
    """К=Д+Г, Л=Д+В, М=К+Л, Н=К+М, О=М+Л.

    Формула О=М+Л - исправление опечатки первоисточника «О=М=Л» по смыслу
    ряда и по совпадению с записью сессии 08.09 (PROJECT-MEMORY.md).

    Контрольный пример (на числах примера 35: Д=8, Г=13, В=7):
    К=21, Л=15, М=36→9, Н=21+9=30→3, О=9+15=24→6.
    Статус: подтверждено (формулы - источник 09, числа посчитаны по ним
    поверх подтверждённого примера 35).
    """
    k = reduce_arcana(sq.d + sq.g)
    l = reduce_arcana(sq.d + sq.v)
    m = reduce_arcana(k + l)
    n = reduce_arcana(k + m)
    o = reduce_arcana(m + l)
    return DerivedPoints(k=k, l=l, m=m, n=n, o=o)


# ---------------------------------------------------------------------------
# 2. Родовой квадрат Е/Ж/З/И
# Источник: 13 (роли, без формул), 35 и 36 (формула + числовые примеры)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RodovoySquare:
    e: int
    zh: int
    z: int
    i: int


def rodovoy_square(sq: BaseSquare) -> RodovoySquare:
    """Е=А+Б, Ж=Б+В, И=В+Г, З=Г+А - сложение двух соседних вершин личного
    квадрата по кругу.

    Контрольный пример (23.01.1987, источник 35 и независимо 36 на своей
    дате 27.08.1976): Е=6, Ж=8, И=20, З=18 (для примера 35).

    ВНИМАНИЕ - оговорка источника: конспект 35 прямо пишет «осталось
    сверить порядок Ж/З на реальном кейсе, если будет возможность» -
    привязка конкретной вершины к конкретной букве (не сама формула
    сложения, а то, какая из «нижних» вершин называется З, а какая И)
    подтверждена только по ролям точек (13) и по двум независимым
    числовым примерам (35, 36), которые совпадают друг с другом, но не
    сверены с третьим источником на подписанной схеме.
    Статус: подтверждено (2 независимых источника, 35 и 36, совпадают
    между собой), но с этой прямой оговоркой первоисточника.
    """
    e = reduce_arcana(sq.a + sq.b)
    zh = reduce_arcana(sq.b + sq.v)
    i = reduce_arcana(sq.v + sq.g)
    z = reduce_arcana(sq.g + sq.a)
    return RodovoySquare(e=e, zh=zh, z=z, i=i)


# ---------------------------------------------------------------------------
# 3-5. Предназначения: личное, социальное, духовное, планетарное
# Источник: 21 (формулы и тексты 3-22), 35 (числовой пример, вводит ЛП/СП/ПП)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PersonalDestiny:
    line_earth: int  # Линия Земли = А+В
    line_heaven: int  # Линия Неба = Б+Г
    total: int  # ЛП = line_earth+line_heaven, сведено к 1-22


def personal_destiny(sq: BaseSquare) -> PersonalDestiny:
    """Личное предназначение. Источник 21 трактует Линию Земли (А+В) и
    Линию Неба (Б+Г) как два отдельных числа с общим текстом 3-22 на
    каждое; источник 35 суммирует их в одно число ЛП (используется дальше
    для духовного/планетарного предназначения).

    Контрольный пример (23.01.1987, источник 35): А+В=12, Б+Г=14, ЛП=26→8.
    Статус: подтверждено.
    """
    earth = reduce_arcana(sq.a + sq.v)
    heaven = reduce_arcana(sq.b + sq.g)
    total = reduce_arcana(earth + heaven)
    return PersonalDestiny(line_earth=earth, line_heaven=heaven, total=total)


@dataclass(frozen=True)
class SocialDestiny:
    line_father: int  # Е+И
    line_mother: int  # Ж+З
    total: int  # СП


def social_destiny(rk: RodovoySquare) -> SocialDestiny:
    """Социальное предназначение = Е+И (линия отца) и Ж+З (линия матери).
    Источник: 21 (формула и текстовая привязка к диагоналям), 35 (числовой
    пример, суммарное СП).

    Контрольный пример (23.01.1987, источник 35): Е+И=26→8, Ж+З=26→8,
    СП=16.
    Статус: подтверждено.
    """
    father = reduce_arcana(rk.e + rk.i)
    mother = reduce_arcana(rk.zh + rk.z)
    total = reduce_arcana(father + mother)
    return SocialDestiny(line_father=father, line_mother=mother, total=total)


def spiritual_destiny(pd: PersonalDestiny, sd: SocialDestiny) -> int:
    """Духовное (общее) предназначение = ЛП+СП, сведено к 1-22.
    Источник: 21 (сумма всех четырёх чисел А+В+Б+Г+Е+И+Ж+З) и 35 (ДП=ЛП+СП).

    Контрольный пример (23.01.1987, источник 35): ДП=8+16=24→6.
    Статус: подтверждено.
    """
    return reduce_arcana(pd.total + sd.total)


def planetary_destiny(sd: SocialDestiny, spiritual: int) -> int:
    """Планетарное предназначение = СП+ДП. Понятие введено только
    источником 35 (в 21 планетарного предназначения нет).

    Контрольный пример (23.01.1987, источник 35): ПП=16+6=22.
    Статус: подтверждено (один источник, 35).
    """
    return reduce_arcana(sd.total + spiritual)


# ---------------------------------------------------------------------------
# 6. Кармический хвост-триплет
# Источник: 34 (формула D=A+B+C, M=D+E, N=M+D), 36 (расшифровка E=Д, пример)
# Решение зафиксировано и не пересматривается: формула Ладини, не
# классические 13/14/16/19.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class KarmicTail:
    first: int  # Г
    second: int  # Д+Г
    third: int  # Г+(Д+Г)


def karmic_tail(sq: BaseSquare) -> KarmicTail:
    """[Г, Д+Г, Г+(Д+Г)], каждое значение сведено к 1-22.

    Источник 34 даёт формулу в других обозначениях (D=A+B+C=наша Г,
    M=D+E, N=M+D), источник 36 дословно раскрывает их точку E как нашу Д
    и даёт числовой пример (27.08.1976): Г=22, М=Д+Г=8+22=30→3,
    N=Г+М=22+3=25→7 → триплет (22, 3, 7).
    Статус: подтверждено.
    """
    first = sq.g
    second = reduce_arcana(sq.d + sq.g)
    third = reduce_arcana(sq.g + second)
    return KarmicTail(first=first, second=second, third=third)


# ---------------------------------------------------------------------------
# 7. Прогноз года по Ладини - 3 энергии
# Источник: 22-prognozirovanie-goda.md
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class YearForecast:
    base_energy: int
    antiphase_energy: int
    total_energy: int


def year_forecast(birth_date: date, target_year: int) -> YearForecast:
    """3 энергии года: базовая (по возрасту), противофаза (±40 лет), сумма.

    Возраст считается упрощённо как target_year - birth_date.year (в
    конспекте не уточняется, учитывать ли, наступил ли уже день рождения
    в target_year - это [предположение]).

    [непроверено] пункт 1 (базовая энергия года): конспект 22 прямо пишет
    «не до конца ясно... точный алгоритм сведения "полных лет" к числу
    1-22... пример из текста не приведён явно... рекомендуется
    перепроверить на конкретном кейсе перед реализацией в боте». Здесь
    реализована ЕДИНСТВЕННАЯ гипотеза, которую предлагает сам конспект
    (сложение цифр возраста, тот же принцип, что и для сумм точек), и
    проверена на собственной иллюстрации конспекта «45 лет → 4+5=9» - но
    это не числовой пример на реальной дате рождения из первоисточника, а
    отвлечённая иллюстрация автора конспекта. Перед использованием в
    отчётах желательна проверка на реальном кейсе с известным прогнозом.

    Пункты 2 и 3 (противофаза и сумма) - явная арифметика, процитирована
    дословно, статус: подтверждено. Контрольный пример (возраст 45):
    база=9, противофаза=45-40=5→5, итог=9+5=14.
    """
    age = target_year - birth_date.year
    base = reduce_arcana(age)
    if age < 40:
        antiphase_raw = age + 40
    elif age > 40:
        antiphase_raw = age - 40
    else:
        antiphase_raw = 0
    antiphase = reduce_arcana(antiphase_raw)
    total = reduce_arcana(base + antiphase)
    return YearForecast(base_energy=base, antiphase_energy=antiphase, total_energy=total)


# ---------------------------------------------------------------------------
# 8. Касты - ведическая нумерология (не часть 22-арканной матрицы)
# Источник: 28-guny-i-kasty.md
# ---------------------------------------------------------------------------

CASTE_DIGITS: dict[str, frozenset[int]] = {
    "brahmany": frozenset({3, 6}),
    "kshatrii": frozenset({1, 9}),
    "vaishyi": frozenset({2, 5}),
    "shudry": frozenset({4, 7, 8}),
}

CASTE_WEIGHTS = (0.4, 0.1, 0.1, 0.4)  # день, месяц, год, четвёртое число


def _caste_of(digit: int) -> str:
    for caste, digits in CASTE_DIGITS.items():
        if digit in digits:
            return caste
    raise ValueError(f"цифра {digit} не входит ни в одну касту 1-9")


@dataclass(frozen=True)
class CasteWeights:
    brahmany: float
    kshatrii: float
    vaishyi: float
    shudry: float


def caste_weights(birth_date: date) -> CasteWeights:
    """4 числа (день/месяц/год/сумма, свёрнутые до 1-9) с весами 40/10/10/40%,
    сведённые в проценты по 4 кастам.

    Контрольный пример (31.01.1998, источник 28): числа 4,1,9,5 →
    Шудры 40%, Кшатрии 20%, Вайшьи 40%, Брахманы 0%.
    Статус: подтверждено.
    """
    day_d = _digit_root(birth_date.day)
    month_d = _digit_root(birth_date.month)
    year_d = _digit_root(birth_date.year)
    fourth_d = _digit_root(day_d + month_d + year_d)
    weights = {"brahmany": 0.0, "kshatrii": 0.0, "vaishyi": 0.0, "shudry": 0.0}
    for digit, weight in zip((day_d, month_d, year_d, fourth_d), CASTE_WEIGHTS):
        weights[_caste_of(digit)] += weight
    return CasteWeights(**weights)


# ---------------------------------------------------------------------------
# 9a. Антифинкод
# Источник: 30-antifinkod.md
# ---------------------------------------------------------------------------


def antifincode(birth_date: date) -> int:
    """«Число блока в деньгах» - число, которого нужно избегать в
    финансовых операциях.

    Контрольный пример (28.08.1991, источник 30): день=1, месяц=8, год=2,
    четвёртое=2 → сумма 1+8+2+2=13→4, минус константа 1 → блок = 3.
    Статус: подтверждено.
    """
    day_d = _digit_root(birth_date.day)
    month_d = _digit_root(birth_date.month)
    year_d = _digit_root(birth_date.year)
    fourth_d = _digit_root(day_d + month_d + year_d)
    combo_sum = _digit_root(day_d + month_d + year_d + fourth_d)
    return combo_sum - 1


# ---------------------------------------------------------------------------
# 9b. Код миллионера (ФИО + дата рождения, пифагорейская нумерология)
# Источник: 31-kod-millionera.md
# ---------------------------------------------------------------------------

_PYTHAGOREAN_CYRILLIC = {
    1: "АИСЪ",
    2: "БЙТЫ",
    3: "ВКУЬ",
    4: "ГЛФЭ",
    5: "ДМХЮ",
    6: "ЕНЦЯ",
    7: "ЁОЧ",
    8: "ЖПШ",
    9: "ЗРЩ",
}
LETTER_TO_DIGIT: dict[str, int] = {
    letter: d for d, letters in _PYTHAGOREAN_CYRILLIC.items() for letter in letters
}


def _fio_part_code(text: str) -> int:
    """Сумма цифр букв части ФИО, сведённая по правилу с мастер-числами
    (reduce_classical - 11/22/33 не сокращаются, как в источнике 31)."""
    raw = sum(LETTER_TO_DIGIT[ch] for ch in text.upper() if ch in LETTER_TO_DIGIT)
    return reduce_classical(raw)


@dataclass(frozen=True)
class MillionaireCode:
    surname: int
    name: int
    patronymic: int
    day: int
    month: int
    year: int
    fate: int
    life_path: int
    left_root: int
    right_root: int
    heart: int
    soul: int
    activation: int


def millionaire_code(
    surname: str, name: str, patronymic: str, birth_date: date
) -> MillionaireCode:
    """«Код миллионера» - НЕ часть 22-арканной матрицы Ладини, отдельная
    пифагорейская нумерология ФИО + истинной даты рождения. patronymic
    может быть пустой строкой, если отчества нет.

    Контрольный пример (Иванова Анна Ивановна, 03.11.1987, источник 31):
    фамилия=22, имя=5, отчество=1, день=3, месяц=11(мастер-число), год=7,
    судьба=1, жизненный путь=3, левый корень=6, правый корень=5, сердце=5,
    душа=1, активация=5. Все 13 значений сверены дословно.
    Статус: подтверждено.
    """
    surname_c = _fio_part_code(surname)
    name_c = _fio_part_code(name)
    patronymic_c = _fio_part_code(patronymic) if patronymic else 0

    day_c = reduce_classical(birth_date.day)
    month_c = reduce_classical(birth_date.month)
    year_c = reduce_classical(digit_sum(birth_date.year))

    fate = reduce_classical(surname_c + name_c + patronymic_c)
    life_path = reduce_classical(day_c + month_c + year_c)
    left_root = reduce_classical(name_c + patronymic_c)
    right_root = reduce_classical(surname_c + fate)
    heart = reduce_classical(day_c + month_c)
    soul = reduce_classical(year_c + life_path)
    activation = reduce_classical((name_c + day_c) * surname_c)

    return MillionaireCode(
        surname=surname_c,
        name=name_c,
        patronymic=patronymic_c,
        day=day_c,
        month=month_c,
        year=year_c,
        fate=fate,
        life_path=life_path,
        left_root=left_root,
        right_root=right_root,
        heart=heart,
        soul=soul,
        activation=activation,
    )


# ---------------------------------------------------------------------------
# 9c. Финансовый код (код удачи + финансовый ограничитель)
# Источник: 32-finansovyy-kod.md
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LuckCode:
    day: int
    month: int
    year: int
    total: int

    def as_string(self) -> str:
        return f"{self.day}{self.month}{self.year}{self.total}"


def luck_code(birth_date: date) -> LuckCode:
    """Финансовый код (код удачи), часть 1 источника 32. Расшифровка
    отдельных цифр кода в конспекте не дана - код используется целиком
    [предположение источника].

    Контрольный пример (25.12.1993, источник 32): 7-3-4-5 → «7345».
    Статус: подтверждено.
    """
    day_d = _digit_root(birth_date.day)
    month_d = _digit_root(birth_date.month)
    year_d = _digit_root(birth_date.year)
    total_d = _digit_root(day_d + month_d + year_d)
    return LuckCode(day=day_d, month=month_d, year=year_d, total=total_d)


def financial_ceiling(birth_date: date) -> tuple[int, bool]:
    """Финансовые ограничители, часть 2 источника 32: день × (месяц+год
    слитно), сумма цифр результата. >=27 - планки нет, <=26 - планка есть.
    Возвращает (сумма цифр произведения, есть_ли_планка).

    Контрольный пример (25.12.1993, источник 32): 25×121993=3049825,
    сумма цифр=31 (>=27 → планки нет).
    Статус: подтверждено.
    """
    concat = int(f"{birth_date.month:02d}{birth_date.year}")
    product = birth_date.day * concat
    total = digit_sum(product)
    has_ceiling = total <= 26
    return total, has_ceiling


if __name__ == "__main__":
    # Самопроверка на контрольных примерах из конспектов - см. докстринги выше.
    example_date = date(1987, 1, 23)  # источник 35
    sq = base_square(example_date)
    assert (sq.a, sq.b, sq.v, sq.g, sq.d) == (5, 1, 7, 13, 8), sq

    dp = derived_points(sq)
    assert (dp.k, dp.l, dp.m, dp.n, dp.o) == (21, 15, 9, 3, 6), dp

    rk = rodovoy_square(sq)
    assert (rk.e, rk.zh, rk.i, rk.z) == (6, 8, 20, 18), rk

    pd = personal_destiny(sq)
    assert (pd.line_earth, pd.line_heaven, pd.total) == (12, 14, 8), pd

    sd = social_destiny(rk)
    assert (sd.line_father, sd.line_mother, sd.total) == (8, 8, 16), sd

    dpn = spiritual_destiny(pd, sd)
    assert dpn == 6, dpn

    ppn = planetary_destiny(sd, dpn)
    assert ppn == 22, ppn

    tail_date = date(1976, 8, 27)  # источник 36
    tail_sq = base_square(tail_date)
    assert (tail_sq.g, tail_sq.d) == (22, 8), tail_sq
    kt = karmic_tail(tail_sq)
    assert (kt.first, kt.second, kt.third) == (22, 3, 7), kt

    yf = year_forecast(date(1980, 1, 1), 2025)  # возраст 45, источник 22
    assert (yf.base_energy, yf.antiphase_energy, yf.total_energy) == (9, 5, 14), yf

    cw = caste_weights(date(1998, 1, 31))  # источник 28
    assert (cw.shudry, cw.kshatrii, cw.vaishyi, cw.brahmany) == (0.4, 0.2, 0.4, 0.0), cw

    afc = antifincode(date(1991, 8, 28))  # источник 30
    assert afc == 3, afc

    mc = millionaire_code("Иванова", "Анна", "Ивановна", date(1987, 11, 3))  # источник 31
    assert (mc.surname, mc.name, mc.patronymic) == (22, 5, 1), mc
    assert (mc.day, mc.month, mc.year) == (3, 11, 7), mc
    assert (mc.fate, mc.life_path) == (1, 3), mc
    assert (mc.left_root, mc.right_root) == (6, 5), mc
    assert (mc.heart, mc.soul, mc.activation) == (5, 1, 5), mc

    lc = luck_code(date(1993, 12, 25))  # источник 32
    assert lc.as_string() == "7345", lc

    total, has_ceiling = financial_ceiling(date(1993, 12, 25))  # источник 32
    assert (total, has_ceiling) == (31, False), (total, has_ceiling)

    print("Все контрольные примеры full_matrix.py сошлись.")
