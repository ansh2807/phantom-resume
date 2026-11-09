"""
resume_analyzer.py — parse and score a resume
"""

import re
from pathlib import Path
from collections import Counter

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


WEAK_VERBS = [
    'responsible for', 'worked on', 'helped', 'assisted',
    'involved in', 'participated in', 'was part of',
    'duties included', 'tasked with',
]

STRONG_VERBS = [
    'led', 'drove', 'delivered', 'built', 'launched', 'scaled',
    'grew', 'increased', 'reduced', 'achieved', 'improved',
    'managed', 'directed', 'spearheaded', 'engineered', 'designed',
    'architected', 'created', 'established', 'transformed',
    'streamlined', 'optimized', 'accelerated', 'generated',
]


class ResumeAnalyzer:
    def __init__(self, path):
        self.path = Path(path)
        self.suffix = self.path.suffix.lower()
        self.text = ''
        self.metadata = {}
        self.raw_lines = []
        self.word_count = 0
        self.issues = []

    def load(self):
        if self.suffix == '.docx':
            self._load_docx()
        elif self.suffix == '.pdf':
            self._load_pdf()
        elif self.suffix == '.txt':
            self.text = self.path.read_text(errors='ignore')
            self.raw_lines = self.text.split('\n')
        else:
            raise ValueError(f"Unsupported: {self.suffix}")
        self.word_count = len(self.text.split())

    def _load_docx(self):
        if Document is None:
            raise ImportError("pip install python-docx")
        doc = Document(str(self.path))
        for para in doc.paragraphs:
            self.raw_lines.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    self.raw_lines.append(cell.text)

        # BUG FIX #7 — namespace-aware metadata extraction via XML parsing
        self.metadata = self._extract_docx_metadata()
        self.text = '\n'.join(self.raw_lines)

    def _extract_docx_metadata(self):
        """Parse docProps/core.xml with namespace awareness."""
        import zipfile
        import xml.etree.ElementTree as ET
        out = {}
        ns = {
            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
        }
        try:
            with zipfile.ZipFile(self.path, 'r') as z:
                if 'docProps/core.xml' not in z.namelist():
                    return out
                data = z.read('docProps/core.xml')
                root = ET.fromstring(data)
                # map friendly names to (namespace, tag)
                mapping = {
                    'title':    ('dc', 'title'),
                    'subject':  ('dc', 'subject'),
                    'creator':  ('dc', 'creator'),
                    'description': ('dc', 'description'),
                    'keywords': ('cp', 'keywords'),
                    'category': ('cp', 'category'),
                    'comments': ('dc', 'description'),
                }
                for friendly, (prefix, tag) in mapping.items():
                    el = root.find(f'{{{ns[prefix]}}}{tag}')
                    if el is not None and el.text:
                        out[friendly] = el.text
        except Exception as e:
            # log instead of silently swallow
            import sys
            print(f"[!] metadata extraction: {e}", file=sys.stderr)
        return out

    def _load_pdf(self):
        if PyPDF2 is None:
            raise ImportError("pip install PyPDF2")
        reader = PyPDF2.PdfReader(str(self.path))
        for page in reader.pages:
            self.raw_lines.append(page.extract_text() or '')
        self.text = '\n'.join(self.raw_lines)

    def check_contact(self):
        score = 0
        text = self.text.lower()
        if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text): score += 25
        else: self.issues.append({'severity': 'high', 'msg': 'No email address found'})
        if re.search(r'\+?[\d\s\-\(\)]{10,}', text): score += 25
        else: self.issues.append({'severity': 'high', 'msg': 'No phone number found'})
        if 'linkedin' in text: score += 25
        else: self.issues.append({'severity': 'medium', 'msg': 'No LinkedIn URL'})
        if re.search(r'\b(india|usa|uk|canada|australia|singapore|dubai|noida|delhi|mumbai|bangalore)\b', text):
            score += 25
        return score

    def check_sections(self):
        text = self.text.lower()
        required = ['summary', 'experience', 'education', 'skills']
        score = 0
        for section in required:
            if section in text: score += 25
            else: self.issues.append({'severity': 'medium', 'msg': f'Missing "{section}" section'})
        return score

    def check_length(self):
        lines = len([l for l in self.raw_lines if l.strip()])
        lo, hi = 30, 60
        if lo <= lines <= hi: return 100
        if lines < lo:
            self.issues.append({'severity': 'medium', 'msg': f'Too short ({lines} lines, ideal {lo}-{hi})'})
            return max(0, 100 - (lo - lines) * 2)
        self.issues.append({'severity': 'medium', 'msg': f'Too long ({lines} lines, ideal {lo}-{hi})'})
        return max(0, 100 - (lines - hi) * 2)

    def check_formatting(self):
        score = 100
        if self.suffix == '.docx':
            try:
                doc = Document(str(self.path))
                if doc.tables:
                    self.issues.append({'severity': 'high', 'msg': f'{len(doc.tables)} tables — many ATSes skip tables'})
                    score -= 20 * min(len(doc.tables), 3)
                if len(doc.inline_shapes) > 0:
                    self.issues.append({'severity': 'high', 'msg': 'Images found — ATS ignores images'})
                    score -= 15
            except Exception:
                pass
        return max(0, score)

    def check_keywords(self):
        text = self.text.lower()
        words = re.findall(r'\b[a-z]{4,}\b', text)
        if not words: return 0
        counts = Counter(words)
        repeated = sum(1 for w, c in counts.items() if c >= 2)
        density = repeated / len(counts)
        if density >= 0.15: return 100
        if density >= 0.08: return 70
        self.issues.append({'severity': 'medium', 'msg': f'Low keyword density ({density:.1%})'})
        return int(density * 400)

    def check_action_verbs(self):
        text = self.text.lower()
        strong = sum(1 for v in STRONG_VERBS if v in text)
        weak = sum(1 for v in WEAK_VERBS if v in text)
        for w in WEAK_VERBS:
            if w in text:
                self.issues.append({'severity': 'medium', 'msg': f'Weak phrase "{w}"'})
        if strong >= 5: base = 100
        elif strong >= 3: base = 70
        else:
            self.issues.append({'severity': 'high', 'msg': f'Only {strong} strong action verbs'})
            base = strong * 20
        return max(0, min(100, base - weak * 10))

    def check_quantification(self):
        metrics = re.findall(r'\b\d+(?:\.\d+)?[%$xX]\b', self.text)
        count = len(metrics)
        if count >= 5: return 100
        if count >= 3: return 70
        if count >= 1: return 40
        self.issues.append({'severity': 'high', 'msg': 'No quantified metrics — add $, %, x'})
        return 0

    def run(self):
        self.load()
        scores = {
            'Contact Info': self.check_contact(),
            'Sections': self.check_sections(),
            'Length': self.check_length(),
            'Formatting': self.check_formatting(),
            'Keywords': self.check_keywords(),
            'Action Verbs': self.check_action_verbs(),
            'Quantified': self.check_quantification(),
        }
        weights = {'Contact Info': 10, 'Sections': 15, 'Length': 10, 'Formatting': 15,
                   'Keywords': 20, 'Action Verbs': 15, 'Quantified': 15}
        total = sum(weights.values())
        score = sum(scores[k] * weights[k] for k in scores) // total
        return {
            'score': score,
            'breakdown': scores,
            'issues': self.issues,
            'text': self.text,
            'metadata': self.metadata,
            'word_count': self.word_count,
            'raw_lines': self.raw_lines,
        }