"""
pdf_exporter.py — DOCX → PDF

Strategy:
1. Prefer docx2pdf (Word COM) on Windows — preserves all layout/images
2. Fallback to reportlab with image preservation
"""

from pathlib import Path

try:
    from docx2pdf import convert as docx2pdf_convert
    HAS_DOCX2PDF = True
except ImportError:
    HAS_DOCX2PDF = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.colors import white
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class PDFExporter:
    def __init__(self, docx_path, pdf_path, keep_metadata=True):
        self.docx = Path(docx_path)
        self.pdf = Path(pdf_path)
        self.keep_metadata = keep_metadata

    def run(self):
        # preferred: docx2pdf via Word COM (preserves everything)
        if HAS_DOCX2PDF:
            try:
                docx2pdf_convert(str(self.docx), str(self.pdf))
                # verify
                size = self.pdf.stat().st_size if self.pdf.exists() else 0
                if size > 1000:
                    return {'pdf': str(self.pdf), 'engine': 'word-com',
                            'paragraphs': 0, 'images': 0, 'size': size,
                            'note': 'Word COM — exact layout preserved'}
            except Exception as e:
                # store error for diagnostics but don't fail
                pass

        # fallback: reportlab — preserves images in order, loses layout
        if not HAS_REPORTLAB:
            raise ImportError("pip install docx2pdf OR reportlab")
        return self._reportlab_export()

    def _reportlab_export(self):
        import zipfile
        import re
        from xml.sax.saxutils import unescape
        import io
        from PIL import Image as PILImage

        with zipfile.ZipFile(self.docx, 'r') as z:
            metadata = {}
            if 'docProps/core.xml' in z.namelist():
                core = z.read('docProps/core.xml').decode('utf-8', errors='ignore')
                for tag in ['title', 'subject', 'description', 'keywords',
                            'category', 'creator', 'lastModifiedBy']:
                    m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', core, flags=re.S)
                    if m:
                        metadata[tag] = unescape(m.group(1))

            body_xml = ''
            if 'word/document.xml' in z.namelist():
                body_xml = z.read('word/document.xml').decode('utf-8', errors='ignore')

            # collect images in order of appearance
            image_rids = []
            for m in re.finditer(r'r:embed="([^"]+)"', body_xml):
                image_rids.append(m.group(1))
            print(f"  [debug] found {len(image_rids)} image references")

            image_bytes_by_rid = {}
            if 'word/_rels/document.xml.rels' in z.namelist():
                rels = z.read('word/_rels/document.xml.rels').decode('utf-8', errors='ignore')
                for rid in image_rids:
                    mm = re.search(
                        rf'Id="{re.escape(rid)}"[^>]*Target="(media/[^"]+)"', rels)
                    if mm:
                        target = 'word/' + mm.group(1)
                        if target in z.namelist():
                            image_bytes_by_rid[rid] = z.read(target)
            print(f"  [debug] resolved {len(image_bytes_by_rid)} images to bytes")

        # build PDF
        doc = SimpleDocTemplate(
            str(self.pdf), pagesize=letter,
            leftMargin=0.7*inch, rightMargin=0.7*inch,
            topMargin=0.7*inch, bottomMargin=0.7*inch,
            title=metadata.get('title', '') or 'Resume',
            subject=metadata.get('subject', '') or 'Resume',         # fix #9
            author=metadata.get('creator', '') or 'Candidate',
            keywords=metadata.get('keywords', '') or 'resume',       # fix #9
            creator='PhantomResume',
        )

        styles = getSampleStyleSheet()
        body = ParagraphStyle('B', parent=styles['Normal'], fontSize=10,
                              leading=14, spaceAfter=6, alignment=TA_LEFT)
        hidden = ParagraphStyle('HID', parent=styles['Normal'], fontSize=0.5,
                                leading=1, textColor=white)

        flow = []

        # hidden metadata at top
        if self.keep_metadata:
            for v in metadata.values():
                if v:
                    flow.append(Paragraph(unescape(v), hidden))

        # body content in order, with images interleaved
        image_idx = 0
        for m in re.finditer(r'<w:p[ >].*?</w:p>|<w:r[ >].*?</w:r>', body_xml, flags=re.S):
            chunk = m.group(0)
            # image?
            rid_match = re.search(r'r:embed="([^"]+)"', chunk)
            if rid_match and rid_match.group(1) in image_bytes_by_rid:
                try:
                    img_bytes = image_bytes_by_rid[rid_match.group(1)]
                    img = PILImage.open(io.BytesIO(img_bytes))
                    w, h = img.size
                    # scale to max 2 inch
                    max_inch = 1.5
                    scale = min(max_inch*inch / w, max_inch*inch / h, 1.0)
                    flow.append(Image(io.BytesIO(img_bytes),
                                      width=int(w*scale), height=int(h*scale)))
                    flow.append(Spacer(1, 6))
                except Exception:
                    pass
                continue
            # text?
            texts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', chunk, flags=re.S)
            if texts:
                p = ''.join(unescape(t) for t in texts)
                if p.strip():
                    flow.append(Paragraph(unescape(p), body))

        paragraphs_count = len([f for f in flow if isinstance(f, Paragraph)])
        images_count = len([f for f in flow if isinstance(f, Image)])
        doc.build(flow)
        return {
            'pdf': str(self.pdf),
            'engine': 'reportlab',
            'paragraphs': paragraphs_count,
            'images': images_count,
            'size': self.pdf.stat().st_size if self.pdf.exists() else 0,
        }
