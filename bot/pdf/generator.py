"""Сборка отдельного PDF на отчёт (Д02, ЗМ-12 - версия шаблона не проектировалась,
это черновой, минимально читаемый макет для проверки движка).

Шрифт - DejaVu Sans (пакет fonts-dejavu-core, ставится в Dockerfile), нужен для
кириллицы: встроенные PDF-шрифты reportlab (Helvetica и т.п.) её не поддерживают.

Графическая схема (MatrixDiagram) - собственный рисунок под раскладку 07
(День/Мотив/Опыт -> Синтез), не копия чужой 10-22-позиционной схемы конкурентов.
ЗМ-11 (эталон графики) этим не закрывается - черновой первый вариант.
"""

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
