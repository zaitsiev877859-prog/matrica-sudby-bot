"""Правила редукции по 02c-metodika-klassicheskaya-numerologiya.md и
07-chernovaya-sborka-otchetov.md. Две разные редукции для двух разных ядер:

- reduce_arcana: до диапазона 1-22 (Личное ядро Я01, Число Пары Я02).
- reduce_classical: до одной цифры, с остановкой на мастер-числах 11/22/33
  (Персональный Год/Месяц Я03).
"""

MASTER_NUMBERS = {11, 22, 33}
KARMIC_DEBT_NUMBERS = {13, 14, 16, 19}


def digit_sum(n: int) -> int:
    return sum(int(d) for d in str(abs(n)))


def reduce_arcana(n: int) -> int:
    """07: «сложить цифры, повторять пока не останется одна цифра или 22,
    22 не сокращать дальше» - на практике: сокращать, пока значение больше 22."""
    while n > 22:
        n = digit_sum(n)
    return n


def reduce_classical(n: int) -> int:
    """02c: сокращать до одной цифры, останавливаясь на мастер-числах 11/22/33."""
    while n > 9 and n not in MASTER_NUMBERS:
        n = digit_sum(n)
    return n
