"""
resume_verifier.py — extract what ATS sees
"""

import zipfile
import re
from pathlib import Path

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


class ResumeVerifier:
    def __init__(self, path):
        self.path = Path(path)

    def extract(self):
        if self.path.suffix.lower() == '.docx':
            return self._extract_docx()
        if self.path.suffix.lower() == '.pdf':
            return self._extract_pdf()
        return {'all_text': self.path.read_text(errors='ignore'),
                'metadata': {}, 'hidden_text': ''}

    def _extract_docx(self):
        metadata, body, hidden = {}, [], []

        with zipfile.ZipFile(self.path, 'r') as z:
            if 'docProps/core.xml' in z.namelist():
                core = z.read('docProps/core.xml').decode('utf-8', errors='ignore')
                for tag in ['title', 'subject', 'description', 'keywords',
                            'category', 'comments', 'creator']:
                    m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', core, flags=re.S)
                    if m:
                        metadata[tag] = m.group(1)
            if 'word/comments.xml' in z.namelist():
                cc = z.read('word/comments.xml').decode('utf-8', errors='ignore')
                for m in re.finditer(r'<w:t[^>]*>(.*?)</w:t>', cc, flags=re.S):
                    hidden.append(m.group(1))

        doc = Document(str(self.path))
        for p in doc.paragraphs:
            body.append(p.text)
        for t in doc.tables:
            for r in t.rows:
                for c in r.cells:
                    body.append(c.text)

        return {
            'all_text': '\n'.join(body) + '\n\n' + '\n'.join(hidden),
            'metadata': metadata,
            'hidden_text': '\n'.join(hidden),
        }

    def _extract_pdf(self):
        reader = PyPDF2.PdfReader(str(self.path))
        text = '\n'.join((p.extract_text() or '') for p in reader.pages)
        return {'all_text': text, 'metadata': dict(reader.metadata or {}),
                'hidden_text': ''}
