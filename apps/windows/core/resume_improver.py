"""
resume_improver.py — suggest rewrites
"""

import re


WEAK_TO_STRONG = {
    'responsible for': ['Led', 'Directed', 'Owned', 'Managed'],
    'worked on':       ['Built', 'Delivered', 'Shipped', 'Launched'],
    'helped':          ['Enabled', 'Supported', 'Drove', 'Facilitated'],
    'assisted':        ['Supported', 'Contributed to', 'Partnered on'],
    'involved in':     ['Drove', 'Led', 'Contributed to'],
    'participated in': ['Contributed to', 'Delivered'],
    'was part of':     ['Contributed to', 'Supported'],
    'duties included': ['Led', 'Managed', 'Delivered'],
    'tasked with':     ['Owned', 'Led', 'Delivered'],
}

VAGUE_TO_SPECIFIC = {
    'various':         'X (name specifics)',
    'several':         'X (name specifics)',
    'multiple':        'X (name specifics)',
    'good':            'quantified (30% improvement)',
    'great':           'quantified',
    'excellent':       'quantified',
    'dynamic':         'remove — says nothing',
    'proactive':       'show, don\'t tell',
    'results-driven':  'prove results, don\'t claim',
    'team player':     'describe collaboration',
    'detail-oriented': 'show attention to detail',
}


class ResumeImprover:
    def __init__(self, analyzer_result):
        self.result = analyzer_result
        self.suggestions = []

    def _check_summary(self):
        text = self.result['text'].lower()
        if 'summary' in text or 'profile' in text:
            return
        self.suggestions.append({
            'type': 'Missing Section',
            'before': '(no summary found)',
            'after': '[Role] with [X]+ years in [Industry]. Delivered [Y] at [Company]. '
                     'Expert in [Skill 1], [Skill 2], [Skill 3].',
            'reason': 'Add a 3-line professional summary — ATS ranks it highest.',
        })

    def _scan_bullets(self):
        for line in self.result['raw_lines']:
            line = line.strip()
            if not line or len(line) < 20:
                continue
            if line.isupper() or len(line.split()) < 5:
                continue
            self._check_bullet(line)

    def _check_bullet(self, line):
        lower = line.lower()
        for weak, strongs in WEAK_TO_STRONG.items():
            if weak in lower:
                new = re.sub(re.escape(weak), strongs[0], line, flags=re.I)
                self.suggestions.append({
                    'type': 'Weak Verb',
                    'before': line[:120],
                    'after': new[:120],
                    'reason': f'"{weak}" is passive → "{strongs[0]}" is active.',
                })
                break
        for vague, repl in VAGUE_TO_SPECIFIC.items():
            if vague in lower:
                self.suggestions.append({
                    'type': 'Vague Language',
                    'before': line[:120],
                    'after': line.replace(vague, repl)[:120],
                    'reason': f'"{vague}" is empty. Replace with specifics.',
                })
                break
        if not re.search(r'\d', line):
            self.suggestions.append({
                'type': 'Missing Metric',
                'before': line[:120],
                'after': line[:100] + ' [add metric]',
                'reason': 'No quantified outcome — add $, %, or volume.',
            })

    def generate(self):
        self._check_summary()
        self._scan_bullets()
        return self.suggestions
