"""Сборка отдельного PDF на отчёт (Д02, ЗМ-12 - версия шаблона не проектировалась,
это черновой, минимально читаемый макет для проверки движка).

Шрифт - DejaVu Sans (пакет fonts-dejavu-core, ставится в Dockerfile), нужен для
кириллицы: встроенные PDF-шрифты reportlab (Helvetica и т.п.) её не поддерживают.
"""

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

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


def build_report_pdf(title: str, specialist_name: str, body_lines: list[str]) -> bytes:
    """body_lines - строки отчёта (как в сообщении бота); строки с <b>...</b>
    рендерятся жирным reportlab-ом нативно, отдельная стилизация заголовков не нужна.
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
