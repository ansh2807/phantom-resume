"""
portal_notes.py — generate plain-text notes for "message to hiring manager" fields
"""

from .variants import get_variant


TEMPLATES = {
    'brief': "{instruction}\n\nI am very interested in this role and would welcome the opportunity to discuss it further.",
    'full': """Dear Hiring Manager,

{instruction}

I am excited about this opportunity and believe my background makes me an excellent fit.
I look forward to hearing from you.

Best regards""",
    'minimal': "{instruction}",
}


def generate_notes(variant='A', style='brief'):
    instruction = get_variant(variant)
    tmpl = TEMPLATES.get(style, TEMPLATES['brief'])
    return tmpl.format(instruction=instruction)
