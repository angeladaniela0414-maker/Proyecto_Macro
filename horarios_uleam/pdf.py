"""PDF del horario semanal (reportlab)."""
import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import consultas

AZUL, AZUL_CLARO, GRIS = colors.HexColor("#2f6fe0"), colors.HexColor("#e5eefe"), colors.HexColor("#5f6f8c")


def horario_pdf(bloques, titulo, subtitulo, mostrar_grupo=False):
    """Devuelve los bytes de un PDF A4 horizontal con la matriz semanal."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm, title=titulo)
    base = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=base["Title"], fontSize=17, alignment=0, textColor=colors.HexColor("#16213a"))
    sub = ParagraphStyle("sub", parent=base["Normal"], fontSize=9.5, textColor=GRIS, spaceAfter=8)
    celda = ParagraphStyle("celda", parent=base["Normal"], fontSize=8, leading=10)
    cab = ParagraphStyle("cab", parent=base["Normal"], fontSize=9, textColor=colors.white, alignment=1, fontName="Helvetica-Bold")

    historia = [Paragraph(escape(titulo), h1), Paragraph(escape(subtitulo), sub)]
    if not bloques:
        historia.append(Paragraph("No hay clases registradas para esta selección.", base["Normal"]))
    else:
        franjas, celdas = consultas.matriz(bloques)
        filas = [[Paragraph("Hora", cab)] + [Paragraph(d, cab) for d in consultas.DIAS.values()]]
        for f in franjas:
            fila = [Paragraph("<b>%s - %s</b>" % f, celda)]
            for dia in range(1, 6):
                partes = []
                for b in celdas.get((f, dia), []):
                    linea = "<b>%s</b>" % escape(b["asignatura"])
                    if mostrar_grupo:
                        linea += "<br/>Nivel %s · Par. %s" % (b["nivel"], escape(b["paralelo"]))
                    if b["docente"]:
                        linea += "<br/>%s" % escape(b["docente"])
                    if b["salon"]:
                        linea += "<br/>%s" % escape(b["salon"])
                    partes.append(Paragraph(linea, celda))
                fila.append(partes or "")
            filas.append(fila)
        ancho = (landscape(A4)[0] - 24 * mm)
        tabla = Table(filas, colWidths=[28 * mm] + [(ancho - 28 * mm) / 5] * 5, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL), ("BACKGROUND", (0, 1), (0, -1), AZUL_CLARO),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d7ee")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.HexColor("#f6f9ff")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        historia.append(tabla)
    historia += [Spacer(1, 6), Paragraph("Generado el %s · ULEAM" % datetime.now().strftime("%d/%m/%Y %H:%M"), sub)]
    doc.build(historia)
    return buf.getvalue()
