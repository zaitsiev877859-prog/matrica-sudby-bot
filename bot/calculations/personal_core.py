"""Формулы ядер Я01 (личное), Я02 (совместимость, через Число Пары) и
Я03 (прогноз) по 07-chernovaya-sborka-otchetov.md и 02c-metodika-klassicheskaya-numerologiya.md.

Проверено на контрольных примерах из обоих файлов:
- 15.06.1990 (соло): День=15, Мотив=6, Опыт=19, Синтез=4; ЧЖП-компоненты M=6,D=6,Y=1;
  кармические числа [13, 19]; персональный год на 2026 = 4.
- 15.06.1990 + 22.11.1988 (пара): Синтез_Б=5, Число Пары=9.
"""

from dataclasses import dataclass
from datetime import date

from bot.calculations.reduction import (
    KARMIC_DEBT_NUMBERS,
    digit_sum,
    reduce_arcana,
    reduce_classical,
)


@dataclass(frozen=True)
class PersonalCorePoints:
    day: int
    motive: int
    experience: int
    synthesis: int


def personal_core_points(birth_date: date) -> PersonalCorePoints:
    """4 точки Личного ядра Я01 (07, раздел «Личное ядро: собственная раскладка»)."""
    day_point = reduce_arcana(birth_date.day)
    motive_point = reduce_arcana(birth_date.month)
    experience_point = reduce_arcana(digit_sum(birth_date.year))
    synthesis_point = reduce_arcana(day_point + motive_point + experience_point)
    return PersonalCorePoints(
        day=day_point,
        motive=motive_point,
        experience=experience_point,
        synthesis=synthesis_point,
    )


def pair_number(synthesis_a: int, synthesis_b: int) -> int:
    """Число Пары для ядра Я02 (07, раздел «Отчёты 2, 3, 4. Совместимость»)."""
    return reduce_arcana(synthesis_a + synthesis_b)


def karmic_debt_numbers(birth_date: date) -> list[int]:
    """Числа кармического долга, всплывшие в расчёте (07, раздел «Число кармического долга»).

    Проверяются независимо два пути:
    - сумма цифр года (та же величина, что используется для точки «Опыт» до
      редукции в диапазон 1-22, если она уже входит в 13/14/16/19 - digit_sum
      уже даёт значение <=22 в подавляющем большинстве дат, поэтому дополнительно
      сокращать не нужно);
    - промежуточная сумма M+D+Y классического ЧЖП (02c) до его финальной редукции.
    """
    found: list[int] = []

    year_sum = digit_sum(birth_date.year)
    if year_sum in KARMIC_DEBT_NUMBERS:
        found.append(year_sum)

    m = reduce_classical(birth_date.month)
    d = reduce_classical(birth_date.day)
    y = reduce_classical(year_sum)
    life_path_intermediate = m + d + y
    if life_path_intermediate in KARMIC_DEBT_NUMBERS and life_path_intermediate not in found:
        found.append(life_path_intermediate)

    return sorted(found)


def personal_year(birth_date: date, target_year: int) -> int:
    """Персональный Год ядра Я03 (02c, переиспользуется в 07 без изменений)."""
    m = reduce_classical(birth_date.month)
    d = reduce_classical(birth_date.day)
    y = reduce_classical(digit_sum(target_year))
    return reduce_classical(m + d + y)


def personal_month(birth_date: date, target_year: int, target_month: int) -> int:
    py = personal_year(birth_date, target_year)
    return reduce_classical(py + target_month)
