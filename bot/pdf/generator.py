"""Сборка отдельного PDF на отчёт (Д02, ЗМ-12 - версия шаблона не проектировалась,
это черновой, минимально читаемый макет для проверки движка).

Шрифт - DejaVu Sans (пакет fonts-dejavu-core, ставится в Dockerfile), нужен для
кириллицы: встроенные PDF-шрифты reportlab (Helvetica и т.п.) её не поддерживают.

Графическая схема (MatrixDiagram) - собственный рисунок под раскладку 07
(День/Мотив/Опыт -> Синтез), не копия чужой 10-22-позиционной схемы конкурентов.
ЗМ-11 (эталон графики) этим не закрывается - черновой первый вариант.
"""

import math
from dataclasses import dataclass
from io import BytesIO

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer

FONT_REGULAR_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"

_fonts_registered = False


def _ensure_fonts_registered() -> None:
    global _fonts_registered
    if _fonts_registered:
        return
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, FONT_REGULAR_PATH))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, FONT_BOLD_PATH))
    _fonts_registered = True


class PersonalMatrixDiagram(Flowable):
    """День/Мотив/Опыт по вершинам треугольника, линии сходятся в Синтез по центру -
    визуализация формулы Синтез = День + Мотив + Опыт (07, раздел «Личное ядро»)."""

    _WIDTH = 150 * mm
    _HEIGHT = 95 * mm
    _OUTER_R = 15 * mm
    _CENTER_R = 19 * mm

    _NODES = (
        ("day", "День", HexColor("#c9a86a")),
        ("experience", "Опыт", HexColor("#7a9fb5")),
        ("motive", "Мотив", HexColor("#b5809f")),
    )

    def __init__(self, points) -> None:
        super().__init__()
        self.points = points

    def wrap(self, available_width, available_height):
        return self._WIDTH, self._HEIGHT

    def draw(self) -> None:
        c = self.canv
        cx = self._WIDTH / 2
        top = (cx, self._HEIGHT - self._OUTER_R - 4 * mm)
        left = (self._OUTER_R + 8 * mm, self._OUTER_R + 4 * mm)
        right = (self._WIDTH - self._OUTER_R - 8 * mm, self._OUTER_R + 4 * mm)
        center = (cx, self._HEIGHT / 2 - 4 * mm)
        positions = {"day": top, "experience": left, "motive": right}

        c.setLineWidth(1)
        c.setStrokeColor(HexColor("#aaaaaa"))
        for key in positions:
            x, y = positions[key]
            c.line(x, y, center[0], center[1])

        for key, label, color in self._NODES:
            self._draw_node(positions[key], self._OUTER_R, getattr(self.points, key), label, color)
        self._draw_node(center, self._CENTER_R, self.points.synthesis, "Синтез", HexColor("#4a4a4a"))

    def _draw_node(self, pos: tuple[float, float], radius: float, number: int, label: str, color) -> None:
        c = self.canv
        x, y = pos
        c.setFillColor(color)
        c.setStrokeColor(HexColor("#333333"))
        c.circle(x, y, radius, stroke=1, fill=1)

        c.setFillColor(white)
        c.setFont(FONT_BOLD, 16)
        c.drawCentredString(x, y - 6, str(number))

        c.setFillColor(HexColor("#333333"))
        c.setFont(FONT_REGULAR, 9)
        c.drawCentredString(x, y - radius - 11, label)


def build_matrix_diagram(points) -> PersonalMatrixDiagram:
    return PersonalMatrixDiagram(points)


@dataclass
class FullMatrixPoints:
    """Числа всех точек полной личной матрицы (система Ладини, восьмиугольник).

    Формулы (подтверждены в 09-formuly-8-tochek-i-arifmetika.md и
    08-polnaya-matrica-progress.md, раздел «Не сделано», п.1-2):
    a=день, b=месяц, v=сумма цифр года, g=a+b+v, d=a+b+v+g (центр).
    e=a+b, zh=b+v, z=g+a, i=v+g (родовой квадрат).
    k=d+g, l=d+v, m=k+l, n=k+m, o=m+l (канал любви k-n-m, канал денег l-o-m).
    Модуль generator.py формулы не считает и не проверяет - числа передаются
    готовыми (см. render_full_matrix_page для примера с готовым набором).
    """

    a: int
    b: int
    v: int
    g: int
    d: int
    e: int
    zh: int
    z: int
    i: int
    k: int
    l: int
    m: int
    n: int
    o: int


class FullMatrixDiagram(Flowable):
    """Восьмиугольник полной личной матрицы Ладини - все точки А-О (ЗМ-11,
    направление №4). Заменяет PersonalMatrixDiagram (треугольник 06/07) для
    отчётов на полной матрице; треугольник не удаляется, остаётся fallback
    для отчётов, которые ещё считаются по черновой методике.

    Источник геометрии - 08-polnaya-matrica-progress.md, раздел «Структура
    матрицы»: порядок 8 внешних точек по кругу с привязкой к возрасту
    (А-Е-Б-Ж-В-И-Г-З = 0-10-20-30-40-50-60-70 лет) и точка Д в центре -
    подтверждены дословно. Стартовый угол и направление обхода -
    подтверждены (скан «2 урок. Шаблон матрицы.pdf», школа Ладини,
    Макарова В.Р., шаблоны-эксперта\\): А слева (9 часов), Б сверху
    (12 часов), В справа (3 часа), Г снизу (6 часов), далее по кругу
    Е/Ж/И/З между ними по возрасту - обход по часовой стрелке. (До скана
    здесь стояло [предположение] с А сверху - это было неверно, исправлено.)

    Диагонали Е-И (линия мужского рода) и Ж-З (линия женского рода) - по
    формулам родового квадрата (е=a+b, zh=b+v, z=g+a, i=v+g) точки Е/И и
    Ж/З лежат на противоположных вершинах восьмиугольника, что даёт готовые
    диагонали через центр - совпадает с прямым указанием 08 «линия мужского
    рода и линия женского рода (диагонали через центр)» и с тем же скан-
    шаблоном (те же две подписанные диагонали, теми же цветами - синяя
    мужская, красная женская).

    Точки К/Л/М/Н/О - подтверждены тем же сканом: К стоит прямо на оси
    Д-Г, Л - прямо на оси Д-В (это и предполагалось), но не на середине
    луча, а ближе к внешнему кольцу. Канал денег $ помечен у Л/О, канал
    любви ♥ - у К/Н (тоже подтверждено). Главная правка после скана: Н и О
    на схеме НЕ лежат на прямых лучах К и Л - они сдвинуты к центру и в
    сторону луча И (там, где по формулам к=д+г и л=д+в сходится общий
    выход М=к+л), то есть Н - примерно на полпути между лучом Г и лучом И,
    О - между лучом В и лучом И; М - на самом луче И, ближе к центру.
    Раньше (до скана) Н/О стояли [предположение] прямо на лучах К/Л - это
    было отличие от скана, исправлено на «между лучом канала и лучом И»."""

    _SIZE = 170 * mm
    _CX = _SIZE / 2
    _CY = _SIZE / 2
    _RING_R = 64 * mm

    _NODE_R_OUTER = 8 * mm
    _NODE_R_CENTER = 11 * mm
    _NODE_R_INNER = 5.5 * mm

    # (ключ, буква, подпись возраста) - порядок строго по кругу А-Е-Б-Ж-В-И-Г-З
    _OUTER_ORDER = (
        ("a", "А", "0 лет"),
        ("e", "Е", "10 лет"),
        ("b", "Б", "20 лет"),
        ("zh", "Ж", "30 лет"),
        ("v", "В", "40 лет"),
        ("i", "И", "50 лет"),
        ("g", "Г", "60 лет"),
        ("z", "З", "70 лет"),
    )

    _COLOR_PERSONAL = HexColor("#7a9fb5")   # А,Б,В,Г - личный квадрат
    _COLOR_RODOVOY = HexColor("#b5809f")    # Е,Ж,З,И - родовой квадрат
    _COLOR_CENTER = HexColor("#4a4a4a")     # Д
    _COLOR_LOVE = HexColor("#c0546f")       # К,Н,М (М - общий выход)
    _COLOR_MONEY = HexColor("#a3862f")      # Л,О,М

    def __init__(self, points: FullMatrixPoints) -> None:
        super().__init__()
        self.points = points

    def wrap(self, available_width, available_height):
        return self._SIZE, self._SIZE

    def _polar(self, angle_deg: float, radius: float) -> tuple[float, float]:
        rad = math.radians(angle_deg)
        return (self._CX + radius * math.cos(rad), self._CY + radius * math.sin(rad))

    def _outer_angle(self, index: int) -> float:
        # index 0 (А) слева (180°), далее по часовой стрелке шагом 45° -
        # подтверждено сканом «2 урок. Шаблон матрицы.pdf» (А слева, Б
        # сверху, В справа, Г снизу).
        return 180 - 45 * index

    def draw(self) -> None:
        c = self.canv
        points = self.points

        outer_pos = {
            key: self._polar(self._outer_angle(idx), self._RING_R)
            for idx, (key, _, _) in enumerate(self._OUTER_ORDER)
        }
        center_pos = (self._CX, self._CY)

        angle_g = self._outer_angle(6)   # Г
        angle_v = self._outer_angle(4)   # В
        angle_i = self._outer_angle(5)   # И - луч между Г и В (сюда сходится М)

        # К/Л - строго на лучах Г/В, ближе к кольцу; Н/О - не на тех же
        # лучах, а сдвинуты к лучу И (посередине между "своим" каналом и
        # И); М - на самом луче И, ближе к центру. Подтверждено сканом
        # «2 урок. Шаблон матрицы.pdf» (см. докстринг класса).
        inner_pos = {
            "k": self._polar(angle_g, 0.72 * self._RING_R),
            "l": self._polar(angle_v, 0.72 * self._RING_R),
            "n": self._polar((angle_g + angle_i) / 2, 0.46 * self._RING_R),
            "o": self._polar((angle_v + angle_i) / 2, 0.46 * self._RING_R),
            "m": self._polar(angle_i, 0.30 * self._RING_R),
        }

        # Внешнее кольцо
        c.setLineWidth(1)
        c.setStrokeColor(HexColor("#aaaaaa"))
        ring_points = [outer_pos[key] for key, _, _ in self._OUTER_ORDER]
        for idx in range(len(ring_points)):
            x1, y1 = ring_points[idx]
            x2, y2 = ring_points[(idx + 1) % len(ring_points)]
            c.line(x1, y1, x2, y2)

        # Диагонали рода (через центр)
        c.setDash(3, 3)
        c.setStrokeColor(self._COLOR_RODOVOY)
        e_x, e_y = outer_pos["e"]
        i_x, i_y = outer_pos["i"]
        c.line(e_x, e_y, i_x, i_y)
        zh_x, zh_y = outer_pos["zh"]
        z_x, z_y = outer_pos["z"]
        c.line(zh_x, zh_y, z_x, z_y)
        c.setDash()

        # Канал любви К-Н-М (вход-центр-выход)
        c.setLineWidth(1.4)
        c.setStrokeColor(self._COLOR_LOVE)
        kx, ky = inner_pos["k"]
        nx, ny = inner_pos["n"]
        mx, my = inner_pos["m"]
        c.line(kx, ky, nx, ny)
        c.line(nx, ny, mx, my)

        # Канал денег Л-О-М (вход-центр-выход)
        c.setStrokeColor(self._COLOR_MONEY)
        lx, ly = inner_pos["l"]
        ox, oy = inner_pos["o"]
        c.line(lx, ly, ox, oy)
        c.line(ox, oy, mx, my)

        # Личный квадрат А-Б-В-Г (диагонали внутри восьмиугольника)
        c.setLineWidth(0.7)
        c.setStrokeColor(self._COLOR_PERSONAL)
        a_x, a_y = outer_pos["a"]
        b_x, b_y = outer_pos["b"]
        v_x, v_y = outer_pos["v"]
        g_x, g_y = outer_pos["g"]
        c.line(a_x, a_y, v_x, v_y)
        c.line(b_x, b_y, g_x, g_y)

        # Узлы личного квадрата + родового квадрата (внешнее кольцо)
        for key, label, age in self._OUTER_ORDER:
            color = self._COLOR_PERSONAL if key in ("a", "b", "v", "g") else self._COLOR_RODOVOY
            self._draw_node(outer_pos[key], self._NODE_R_OUTER, getattr(points, key), f"{label} · {age}", color, number_font=13)

        # Центр Д
        self._draw_node(center_pos, self._NODE_R_CENTER, points.d, "Д · центр", self._COLOR_CENTER, number_font=15)

        # Каналы К/Л/М/Н/О
        self._draw_node(inner_pos["k"], self._NODE_R_INNER, points.k, "К · вход ♥", self._COLOR_LOVE, number_font=10)
        self._draw_node(inner_pos["n"], self._NODE_R_INNER, points.n, "Н · ♥", self._COLOR_LOVE, number_font=10)
        self._draw_node(inner_pos["l"], self._NODE_R_INNER, points.l, "Л · вход $", self._COLOR_MONEY, number_font=10)
        self._draw_node(inner_pos["o"], self._NODE_R_INNER, points.o, "О · $", self._COLOR_MONEY, number_font=10)
        self._draw_node(inner_pos["m"], self._NODE_R_INNER, points.m, "М · баланс", HexColor("#8a6a52"), number_font=10)

    def _draw_node(self, pos: tuple[float, float], radius: float, number: int, label: str, color, number_font: int = 12) -> None:
        c = self.canv
        x, y = pos
        c.setFillColor(color)
        c.setStrokeColor(HexColor("#333333"))
        c.setLineWidth(1)
        c.circle(x, y, radius, stroke=1, fill=1)

        c.setFillColor(white)
        c.setFont(FONT_BOLD, number_font)
        c.drawCentredString(x, y - number_font * 0.35, str(number))

        c.setFillColor(HexColor("#333333"))
        c.setFont(FONT_REGULAR, 7.5)
        c.drawCentredString(x, y - radius - 9, label)


def build_full_matrix_diagram(points: FullMatrixPoints) -> FullMatrixDiagram:
    return FullMatrixDiagram(points)


FULL_MATRIX_LEGEND = (
    ("А", "личный квадрат: день рождения (визитная карточка, ресурс)"),
    ("Б", "личный квадрат: месяц рождения (таланты, самая плюсовая точка)"),
    ("В", "личный квадрат: сумма цифр года (материальная карма, здоровье)"),
    ("Г", "личный квадрат: А+Б+В (кармическая задача, самая минусовая точка)"),
    ("Д", "центр: А+Б+В+Г, зона комфорта, социальная реализация"),
    ("Е", "родовой квадрат: А+Б, духовные задачи мужского рода"),
    ("Ж", "родовой квадрат: Б+В, духовные задачи женского рода"),
    ("З", "родовой квадрат: Г+А, материальные задачи женского рода"),
    ("И", "родовой квадрат: В+Г, материальные задачи мужского рода"),
    ("К", "канал любви (вход): Д+Г"),
    ("Н", "канал любви (середина/итог, знак ♥): К+М"),
    ("Л", "канал денег (вход): Д+В"),
    ("О", "канал денег (середина/итог, знак $): М+Л"),
    ("М", "баланс между финансами и отношениями, общий выход обоих каналов: К+Л"),
)


def render_full_matrix_page(
    points: FullMatrixPoints,
    specialist_name: str,
    title: str = "Полная личная матрица",
) -> bytes:
    """Точка входа направления №4 - собирает PDF-страницу полной личной
    матрицы (восьмиугольник, все точки А-О) на готовых числах points, тем же
    способом (build_report_pdf), что и черновой шаблон 06/07. Формулы не
    считает - принимает уже посчитанные числа (см. FullMatrixPoints)."""

    body_lines = ["<b>Соответствие точек (для сверки со сборкой отчётов)</b>", ""]
    for letter, meaning in FULL_MATRIX_LEGEND:
        body_lines.append(f"<b>{letter}</b> — {meaning}")

    return build_report_pdf(
        title=title,
        specialist_name=specialist_name,
        body_lines=body_lines,
        diagram=build_full_matrix_diagram(points),
    )


def build_report_pdf(
    title: str,
    specialist_name: str,
    body_lines: list[str],
    diagram: Flowable | None = None,
) -> bytes:
    """body_lines - строки отчёта (как в сообщении бота); строки с <b>...</b>
    рендерятся жирным reportlab-ом нативно, отдельная стилизация заголовков не нужна.
    diagram - опциональная графическая схема (см. build_matrix_diagram), вставляется
    сразу после заголовка.
    """
    _ensure_fonts_registered()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        title=title,
    )

    base_styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleRu", parent=base_styles["Title"], fontName=FONT_BOLD, fontSize=18, leading=22
    )
    normal_style = ParagraphStyle(
        "NormalRu", parent=base_styles["Normal"], fontName=FONT_REGULAR, fontSize=11, leading=15
    )
    footer_style = ParagraphStyle(
        "FooterRu", parent=base_styles["Normal"], fontName=FONT_REGULAR, fontSize=9, textColor="#666666"
    )

    story = [Paragraph(title, title_style), Spacer(1, 6 * mm)]

    if diagram is not None:
        story.append(diagram)
        story.append(Spacer(1, 6 * mm))

    for line in body_lines:
        if not line:
            story.append(Spacer(1, 3 * mm))
            continue
        story.append(Paragraph(line, normal_style))

    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(f"Подготовлено специалистом: {specialist_name}", footer_style))
    story.append(Paragraph("Черновой макет для проверки движка. Не финальная редакция и не финальный дизайн PDF.", footer_style))

    doc.build(story)
    return buffer.getvalue()
