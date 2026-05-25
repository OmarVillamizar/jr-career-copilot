"""
Conversor Markdown → DOCX con formato Harvard optimizado para ATS.
Usa python-docx + BeautifulSoup para mapear elementos Markdown a estilos Word.
"""

import os
from typing import Optional


def generate_docx(md_content: str, output_path: str) -> Optional[str]:
    """
    Convierte contenido Markdown a un archivo .docx con estilo Harvard ATS-friendly.

    Args:
        md_content (str): Contenido del CV en formato Markdown.
        output_path (str): Ruta donde guardar el archivo .docx.

    Returns:
        Optional[str]: Ruta del archivo generado, o None si falló.
    """
    try:
        import markdown
        from bs4 import BeautifulSoup
        from docx import Document
        from docx.shared import Pt, Cm
        from docx.oxml.ns import qn
    except ImportError as exc:
        print(f"[WARN] No se pudo generar DOCX — dependencias faltantes: {exc}")
        print("       Instala con: pip install markdown beautifulsoup4 python-docx")
        return None

    try:
        # 1. Markdown → HTML
        html_body = markdown.markdown(md_content, extensions=["extra"])
        soup = BeautifulSoup(f"<div>{html_body}</div>", "html.parser")

        # 2. Crear documento Word con estilos base
        doc = Document()

        # Márgenes de página
        for section in doc.sections:
            section.top_margin = Cm(2)
            section.bottom_margin = Cm(2)
            section.left_margin = Cm(2)
            section.right_margin = Cm(2)

        # Estilo Normal (base)
        style = doc.styles["Normal"]
        font = style.font
        font.name = "Calibri"
        font.size = Pt(11)
        font.color.rgb = None  # Negro puro
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.line_spacing = 1.15

        # 3. Recorrer elementos del HTML y mapearlos a Word
        _process_container(soup.div, doc)

        # 4. Asegurar que el directorio existe
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        doc.save(output_path)
        return output_path

    except Exception as exc:
        print(f"[WARN] Error al generar DOCX: {exc}")
        return None


def _process_container(container, doc) -> None:
    """
    Procesa recursivamente los hijos de un elemento HTML y los escribe en el documento Word.
    """
    from bs4 import Tag
    from bs4.element import NavigableString
    from docx.shared import Pt
    from docx.oxml.ns import qn

    for child in container.children:
        if isinstance(child, NavigableString):
            text = child.strip()
            if text:
                p = doc.add_paragraph(text)
            continue

        if not isinstance(child, Tag):
            continue

        tag = child.name

        if tag in ("h1", "h2", "h3"):
            # ── Encabezados ──
            level = int(tag[1])
            p = doc.add_paragraph()
            p.style = doc.styles[f"Heading {level}"]
            run = p.add_run(child.get_text(strip=True))
            run.font.name = "Calibri"
            if level == 1:
                run.font.size = Pt(16)
                run.bold = True
            elif level == 2:
                run.font.size = Pt(13)
                run.bold = True
                # Línea horizontal sutil debajo de H2 (estilo Harvard)
                p.paragraph_format.space_before = Pt(14)
                p.paragraph_format.space_after = Pt(6)
                _add_bottom_border(p)
            else:
                run.font.size = Pt(11)
                run.bold = True

        elif tag == "p":
            # ── Párrafos ──
            text = child.get_text(strip=True)
            if text:
                doc.add_paragraph(text)

        elif tag == "hr":
            # ── Separador horizontal → espacio ──
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)

        elif tag in ("ul", "ol"):
            # ── Listas ──
            for li in child.find_all("li", recursive=False):
                text = li.get_text(strip=True)
                if not text:
                    continue
                # Detectar si es negrita parcial (certificaciones)
                bold_text = ""
                normal_text = text
                strong = li.find("strong")
                if strong:
                    bold_text = strong.get_text(strip=True)
                    normal_text = text.replace(bold_text, "").strip()
                    if normal_text.startswith("—"):
                        normal_text = normal_text[1:].strip()

                p = doc.add_paragraph(style="List Bullet")
                if bold_text:
                    run_bold = p.add_run(bold_text)
                    run_bold.bold = True
                    run_bold.font.name = "Calibri"
                    run_bold.font.size = Pt(11)
                    if normal_text:
                        run_normal = p.add_run(f" — {normal_text}")
                        run_normal.font.name = "Calibri"
                        run_normal.font.size = Pt(11)
                else:
                    p.clear()
                    run = p.add_run(normal_text)
                    run.font.name = "Calibri"
                    run.font.size = Pt(11)

        elif tag in ("em", "strong"):
            # ── Énfasis inline (period, company info) ──
            p = doc.add_paragraph()
            run = p.add_run(child.get_text(strip=True))
            run.font.name = "Calibri"
            run.font.size = Pt(11)
            if tag == "strong":
                run.bold = True
            else:
                run.italic = True

        else:
            # ── Fallback: procesar hijos ──
            if child.contents:
                _process_container(child, doc)


def _add_bottom_border(paragraph) -> None:
    """Añade un borde inferior sutil a un párrafo (estilo Harvard)."""
    from docx.oxml.ns import qn
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.makeelement(qn("w:pBdr"), {})
    bottom = pBdr.makeelement(qn("w:bottom"), {
        qn("w:val"): "single",
        qn("w:sz"): "4",
        qn("w:space"): "4",
        qn("w:color"): "999999",
    })
    pBdr.append(bottom)
    pPr.append(pBdr)
