"""
template_library.py — 50 template variations for A/B submission
"""

import random
import hashlib
from pathlib import Path


FONTS = [
    'Calibri', 'Arial', 'Times New Roman', 'Georgia', 'Helvetica',
    'Verdana', 'Tahoma', 'Trebuchet MS', 'Cambria', 'Garamond',
]

SECTION_ORDERS = [
    ['summary', 'experience', 'education', 'skills'],
    ['summary', 'skills', 'experience', 'education'],
    ['experience', 'education', 'skills', 'summary'],
    ['skills', 'summary', 'experience', 'education'],
    ['education', 'experience', 'skills', 'summary'],
]


def generate_template_id():
    return hashlib.md5(str(random.random()).encode()).hexdigest()[:8]


def randomize_font(docx_path, font):
    """Change base font in the DOCX."""
    import zipfile
    tmp = str(docx_path) + '.tmp'
    with zipfile.ZipFile(docx_path, 'r') as z:
        contents = {n: z.read(n) for n in z.namelist()}

    if 'word/styles.xml' in contents:
        styles = contents['word/styles.xml'].decode('utf-8', errors='ignore')
        # simple replace of common default fonts
        for old in ['Calibri', 'Arial', 'Times New Roman', 'Georgia']:
            styles = styles.replace(f'w:ascii="{old}"', f'w:ascii="{font}"')
            styles = styles.replace(f'w:hAnsi="{old}"', f'w:hAnsi="{font}"')
        contents['word/styles.xml'] = styles.encode('utf-8')

    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, b in contents.items():
            z.writestr(n, b)
    Path(docx_path).unlink()
    Path(tmp).rename(docx_path)


def generate_random_template_seed():
    return {
        'template_id': generate_template_id(),
        'font': random.choice(FONTS),
        'section_order': random.choice(SECTION_ORDERS),
        'accent_color': '%06X' % random.randint(0, 0xFFFFFF),
        'padding_bytes': random.randint(0, 2048),
    }
