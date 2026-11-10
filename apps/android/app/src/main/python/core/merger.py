"""
merger.py — merge cover letter + resume into one DOCX
"""

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


def merge_docx(cover_path, resume_path, output_path):
    """Concatenate bodies of two DOCX files with a page break."""
    with zipfile.ZipFile(cover_path, 'r') as z1:
        cover = {n: z1.read(n) for n in z1.namelist()}

    with zipfile.ZipFile(resume_path, 'r') as z2:
        resume = {n: z2.read(n) for n in z2.namelist()}

    # extract body content (everything between <w:body> and </w:body>)
    def get_body(contents):
        doc = contents['word/document.xml'].decode('utf-8', errors='ignore')
        m = __import__('re').search(r'<w:body>(.*)</w:body>', doc, flags=__import__('re').S)
        return m.group(1) if m else ''

    cover_body = get_body(cover)
    resume_body = get_body(resume)

    # remove <w:sectPr> from cover body (it's the last element, controls page setup)
    import re
    cover_body = re.sub(r'<w:sectPr[^>]*>.*?</w:sectPr>', '', cover_body, flags=re.S)

    merged_body = cover_body + '<w:p><w:r><w:br w:type="page"/></w:r></w:p>' + resume_body

    merged_doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<w:body>{merged_body}</w:body></w:document>'
    )

    # start from resume base (has images, fonts), replace document.xml body
    resume['word/document.xml'] = merged_doc.encode('utf-8')

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for n, b in resume.items():
            zout.writestr(n, b)

    return True
