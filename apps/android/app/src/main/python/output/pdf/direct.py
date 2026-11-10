from pathlib import Path


def render_direct(source_docx: Path, out_pdf: Path) -> Path:
    """Minimal real PDF: render text of docx if possible, else blank page."""
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas

    text = ""
    try:
        import zipfile, re
        with zipfile.ZipFile(source_docx) as z:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
        text = re.sub(r"<[^>]+>", " ", xml)
    except Exception:
        text = source_docx.stem

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=LETTER)
    width, height = LETTER
    y = height - 72
    for line in text.split():
        if y < 72:
            c.showPage()
            y = height - 72
        c.drawString(72, y, line[:100])
        y -= 14
    c.save()
    return out_pdf
