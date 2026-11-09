"""
script_obfuscation.py — encode instruction using non-Latin Unicode scripts

Why: some ATS filters only check for keyword patterns in Latin script.
Injecting in Devanagari, Cyrillic, Arabic, or combining characters can
bypass naive filters.
"""

# Devanagari mapping (A-Z a-z → Devanagari characters)
DEV_MAP = {chr(65+i): chr(0x0915+i) for i in range(26)}   # A-Z → क-ह (approx)
DEV_MAP.update({chr(97+i): chr(0x0915+i) for i in range(26)})

# Cyrillic mapping (visually similar to Latin)
CYR_MAP = {
    'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'p': 'р', 'x': 'х', 'y': 'у',
    'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'K': 'К',
    'M': 'М', 'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х',
}


def to_devanagari(text):
    return ''.join(DEV_MAP.get(c, c) for c in text)


def to_cyrillic_homoglyph(text):
    return ''.join(CYR_MAP.get(c, c) for c in text)


def to_combining_marks(text):
    """Add combining diacritics that don't change rendering for some OCR."""
    combining = '\u0301'  # acute accent
    return ''.join(c + combining if c.isalpha() else c for c in text)


def inject_script_variant(text, script='cyrillic'):
    """Wrap instruction in a script variant to bypass Latin-only filters."""
    if script == 'devanagari':
        return to_devanagari(text)
    if script == 'cyrillic':
        return to_cyrillic_homoglyph(text)
    if script == 'combining':
        return to_combining_marks(text)
    return text
