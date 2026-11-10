# output/pdf/rendered.py
from pathlib import Path


def render_rendered(source_docx: Path, out_pdf: Path) -> Path:
    """docx -> LibreOffice -> pdf. You control nothing post-render."""
    import subprocess
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf",
         "--outdir", str(out_pdf.parent), str(source_docx)],
        check=True,
    )
    return out_pdf
