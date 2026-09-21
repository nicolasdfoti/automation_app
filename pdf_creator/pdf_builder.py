from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from . import schema

PAGE_W, PAGE_H = A4


def _draw_watermark(c: canvas.Canvas) -> None:
    c.saveState()
    c.setFont("Helvetica-Bold", 60)
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.07))
    c.translate(PAGE_W / 2, PAGE_H / 2)
    c.rotate(35)
    c.drawCentredString(0, 0, "DATO MOCK - DEMO")
    c.restoreState()


def _draw_header(c: canvas.Canvas, record: dict) -> float:
    y = PAGE_H - 25 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, "ESQUEMATICO DE PROPIEDAD")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.grey)
    c.drawString(20 * mm, y - 6 * mm, "Documento sintetico generado para demo — no representa un inmueble real")
    c.setFillColor(colors.black)

    y -= 16 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, f"Codigo: {record['codigo']}")
    c.drawString(90 * mm, y, f"Fecha de relevamiento: {record['fecha_relevamiento']}")
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Direccion: {record['direccion']}")
    return y - 10 * mm


def _draw_tabla_datos(c: canvas.Canvas, record: dict, top_y: float) -> float:
    fields = schema.NUMERIC_FIELDS
    col_w = (PAGE_W - 40 * mm) / 2
    row_h = 10 * mm
    x0 = 20 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(x0, top_y, "Tabla de datos tecnicos")
    top_y -= 4 * mm

    table_top = top_y
    n_rows = -(-len(fields) // 2)
    table_bottom = table_top - n_rows * row_h

    c.setLineWidth(0.6)
    c.rect(x0, table_bottom, col_w * 2, table_top - table_bottom, stroke=1, fill=0)
    for i in range(1, n_rows):
        y = table_top - i * row_h
        c.line(x0, y, x0 + col_w * 2, y)
    c.line(x0 + col_w, table_bottom, x0 + col_w, table_top)

    c.setFont("Helvetica", 9)
    for idx, field in enumerate(fields):
        col = idx // n_rows
        row = idx % n_rows
        cell_x = x0 + col * col_w
        cell_y = table_top - row * row_h
        value = record[field.key]
        text = f"{value} {field.unit}".strip()
        c.setFont("Helvetica-Bold", 9)
        c.drawString(cell_x + 3 * mm, cell_y - 5 * mm, field.label + ":")
        c.setFont("Helvetica", 9)
        c.drawRightString(cell_x + col_w - 3 * mm, cell_y - 5 * mm, text)

    return table_bottom - 10 * mm


def _draw_plano_placeholder(c: canvas.Canvas, top_y: float) -> None:
    x0 = 20 * mm
    w = PAGE_W - 40 * mm
    h = 70 * mm
    c.setDash(3, 3)
    c.rect(x0, top_y - h, w, h, stroke=1, fill=0)
    c.setDash()
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.grey)
    c.drawCentredString(PAGE_W / 2, top_y - h / 2, "(plano — placeholder, no forma parte del dato a extraer)")
    c.setFillColor(colors.black)


def render(record: dict, out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=A4)
    _draw_watermark(c)
    y = _draw_header(c, record)
    y = _draw_tabla_datos(c, record, y)
    _draw_plano_placeholder(c, y)
    c.showPage()
    c.save()
    return out_path
