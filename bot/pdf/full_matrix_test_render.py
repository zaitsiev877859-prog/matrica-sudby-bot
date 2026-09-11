"""Тестовый рендер render_full_matrix_page на контрольном примере 15.06.1990
(направление №4, ЗМ-11 - PDF-шаблон полной личной матрицы, восьмиугольник).

Числа посчитаны вручную по формулам, подтверждённым в
08-polnaya-matrica-progress.md и 09-formuly-8-tochek-i-arifmetika.md
(a=день, b=месяц, v=сумма цифр года, g=a+b+v, d=a+b+v+g; e=a+b, zh=b+v,
z=g+a, i=v+g; k=d+g, l=d+v, m=k+l, n=k+m, o=m+l; свёртка >22 - сложением
цифр результата). Модуль formуlы не пересчитывает и не проверяет - этот
скрипт лишь применяет уже закрытую арифметику к базовым числам даты, чтобы
получить реальные (не абстрактные) числа для рендера, так как ни один
прочитанный файл проекта не публикует все 14 точек сразу для одной даты.

a=15, b=6, v=19 сверены с 07-chernovaya-sborka-otchetov.md (контрольный
пример 15.06.1990: День=15, Мотив=6, Опыт=19) и с 02-methods-market.md
(таблица R14/R15: «Лево/верх/право/низ» = 15/6/19/4 для той же даты, где
низ = г = a+b+v = 40 -> 4). e/zh/z/i (21/7/19/5, свёрнуты по кругу
e-zh-i-z) численно совпадают с той же таблицей («Родовые углы» 21/7/5/19)
- независимое подтверждение формулы родового квадрата на этой дате.
k/l/m/n/o (12/9/21/6/3) нигде в архиве готовыми не встречены - досчитаны
здесь по уже закрытой формуле, это отмечено в возврате направления.

ТЕХНИЧЕСКОЕ ПРИМЕЧАНИЕ ПО ШРИФТУ (только для этого локального теста):
generator.py грузит DejaVuSans с линуксового пути пакета fonts-dejavu-core
(так и должно быть - это путь из Dockerfile для рабочего бота). На этой
машине для Windows нет ни Python, ни DejaVu исходно - оба поставлены в ходе
этой сессии (winget: Python.Python.3.12; pip: reportlab), но DejaVu-файлов
на диске нет. Чтобы не трогать generator.py ради разового теста, здесь
регистрируются под теми же именами шрифтов (DejaVuSans/DejaVuSans-Bold)
кириллические TTF из C:/Windows/Fonts (Arial) - это подменяет только
физический .ttf-файл для этого прогона, код рендера и его логика не
меняются. В самой библиотеке DejaVu отсутствие Cyrillic не проблема - она
его поддерживает; проблема только в том, что файла нет на этой Windows-
машине не в Docker-контейнере.
"""

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import generator

_WIN_FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
_WIN_FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"


def _register_windows_fallback_fonts() -> None:
    pdfmetrics.registerFont(TTFont(generator.FONT_REGULAR, _WIN_FONT_REGULAR))
    pdfmetrics.registerFont(TTFont(generator.FONT_BOLD, _WIN_FONT_BOLD))
    generator._fonts_registered = True  # noqa: SLF001 - только для локального теста без DejaVu


def main() -> None:
    _register_windows_fallback_fonts()

    # 15.06.1990: a=день, b=месяц, v=сумма цифр года (1+9+9+0=19)
    a, b, v = 15, 6, 19
    g = a + b + v            # 40 -> 4
    g = _reduce(g)
    d = _reduce(a + b + v + g)  # 15+6+19+4=44 -> 8

    e = _reduce(a + b)       # 21
    zh = _reduce(b + v)      # 25 -> 7
    z = _reduce(g + a)       # 19
    i = _reduce(v + g)       # 23 -> 5

    k = _reduce(d + g)       # 12
    l = _reduce(d + v)       # 27 -> 9
    m = _reduce(k + l)       # 21
    n = _reduce(k + m)       # 33 -> 6
    o = _reduce(m + l)       # 30 -> 3

    points = generator.FullMatrixPoints(
        a=a, b=b, v=v, g=g, d=d, e=e, zh=zh, z=z, i=i, k=k, l=l, m=m, n=n, o=o,
    )

    pdf_bytes = generator.render_full_matrix_page(
        points=points,
        specialist_name="Тестовый специалист (пример 15.06.1990)",
        title="Полная личная матрица — тестовый рендер",
    )

    out_path = Path(__file__).parent / "full_matrix_test_15_06_1990.pdf"
    out_path.write_bytes(pdf_bytes)
    print(f"OK: {out_path} ({len(pdf_bytes)} bytes)")
    print(f"points: {points}")


def _reduce(n: int) -> int:
    while n > 22:
        n = sum(int(d) for d in str(n))
    return n


if __name__ == "__main__":
    main()
