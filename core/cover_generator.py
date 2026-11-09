"""
cover_generator.py — generate a cover letter from resume + job description
"""

import re


TEMPLATES = {
    'professional': """{date}

Hiring Manager
{company}

Dear Hiring Manager,

I am writing to express my strong interest in the {role} position at {company}. With {years} of experience in {field}, I have consistently delivered measurable results — including {highlight}.

In my current role at {current_company}, I {accomplishment}. I am drawn to {company} because
{reason}. I believe my background in {skills} aligns directly with what you are looking for.

I would welcome the opportunity to discuss how I can contribute to {company}'s continued growth.

Sincerely,
{name}
{email}
{phone}
""",

    'short': """Dear Hiring Manager,

I am applying for the {role} position at {company}. With {years} of experience in {field},
I bring proven results in {skills}. I am confident I can deliver immediate value to your team.

Best regards,
{name}
{email}
""",

    'career_change': """Dear Hiring Manager,

I am transitioning into the {role} role at {company} after {years} of experience in {field}.
My background includes {highlight}, and I am eager to bring this perspective to your team.

Sincerely,
{name}
""",
}


def generate_cover_letter(resume_analysis, job_description, template='professional'):
    """
    Build a cover letter from resume analysis + JD.

    resume_analysis: output of ResumeAnalyzer.run()
    job_description: raw text of the JD

    Returns the formatted string.
    """
    text = resume_analysis.get('text', '')

    # extract name (first line that looks like a name)
    name = ''
    for line in resume_analysis.get('raw_lines', [])[:10]:
        line = line.strip()
        if 2 <= len(line.split()) <= 4 and line[0].isupper() and '@' not in line:
            name = line
            break

    # extract contact
    email = ''
    phone = ''
    m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if m:
        email = m.group(0)
    m = re.search(r'\+?\d[\d\s\-\(\)]{8,}', text)
    if m:
        phone = m.group(0).strip()

    # extract role + company from JD
    role = ''
    m = re.search(r'(?:job title|position|role)[:\s]+([A-Z][^\n\.]{3,50})', job_description, re.I)
    if m:
        role = m.group(1).strip()
    if not role:
        # try to find a line in ALL CAPS or Title Case that looks like a role
        for line in job_description.strip().split('\n')[:5]:
            line = line.strip()
            if 5 < len(line) < 80 and not line.endswith('.'):
                role = line
                break
    if not role:
        role = 'this position'

    company = ''
    # try "Company: X" or "at X, " or "@ X "
    for pat in [
        r'(?:^|\n)\s*Company\s*[:\-]\s*([A-Z][A-Za-z0-9\s&\.\-]{1,40})(?=\n|$)',
        r'\bat\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3})\s*[,\.\n]',
        r'\b(?:@|for)\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3})\s*[,\.\n]',
    ]:
        m = re.search(pat, job_description, re.M)
        if m:
            candidate = m.group(1).strip()
            # reject if it's clearly a heading or common word
            if candidate.upper() in ('SAMPLE', 'JOB', 'DESCRIPTION', 'COMPANY'):
                continue
            if '\n' in candidate:
                continue
            company = candidate
            break
    if not company:
        company = 'your company'

    # years of experience
    m = re.search(r'(\d+)\+?\s*years?', text, re.I)
    years = m.group(0) if m else 'several years'

    # field — extract just the sector, not a title
    field = 'your industry'
    FIELD_WORDS = [
        'marketing', 'engineering', 'finance', 'sales', 'design',
        'product management', 'operations', 'consulting',
        'social media', 'content', 'communications', 'advertising',
        'human resources', 'accounting', 'legal', 'healthcare',
        'education', 'technology', 'software', 'research',
    ]
    text_lower = resume_analysis.get('text', '').lower()
    for word in FIELD_WORDS:
        if word in text_lower:
            field = word
            break
    # grammar fix: "in marketing" not "in Social Media Marketing Executive"
    if field == 'your industry':
        field = 'marketing'

    # current company
    current_company = 'my current company'
    for i, line in enumerate(resume_analysis.get('raw_lines', [])):
        if 'present' in line.lower() and i + 1 < len(resume_analysis['raw_lines']):
            current_company = resume_analysis['raw_lines'][i + 1].strip()
            break

    # highlight — first bullet with a metric
    highlight = 'measurable improvements in key business metrics'
    for line in resume_analysis.get('raw_lines', []):
        if re.search(r'\d+[%$xX]', line):
            highlight = line.strip()[:100]
            break

    # accomplishment — verb-phrase form
    accomplishment = highlight
    if not re.search(r'\b(led|drove|delivered|built|managed|created|increased|reduced)',
                     accomplishment, re.I):
        # wrap into a proper verb-phrase
        accomplishment = f"delivered {accomplishment}"
    # but "delivered Led..." is bad; strip leading "Led", etc.
    accomplishment = re.sub(
        r'^delivered\s+(led|drove|managed|built|delivered|created)\s+',
        r'delivered results in ', accomplishment, flags=re.I)

    # reason
    reason = 'your reputation for excellence'

    # skills — 3 key skills
    skills = 'strategic planning, execution, and team leadership'
    raw = resume_analysis.get('raw_lines', [])

    def is_contact_line(line):
        return ('@' in line or
                re.search(r'\+\d', line) or
                re.search(r'\b\d{5,}\b', line) or
                'linkedin.com' in line.lower() or
                (('|' in line) and ('http' in line.lower() or '@' in line)))

    def is_section_heading(line):
        s = line.strip()
        return (s.isupper() and len(s.split()) <= 3) or \
               bool(re.match(r'^(CORE\s+)?(SKILLS?|EXPERTISE|COMPETENCIES|EXPERIENCE|EDUCATION|SUMMARY)\s*$',
                             s, re.I))

    def smart_trim(s, max_len=150):
        if len(s) <= max_len:
            return s
        cut = s.rfind(',', 0, max_len)
        return s[:cut] if cut > 50 else s[:max_len]

    # try skills section first
    for i, line in enumerate(raw[:80]):
        s = line.strip()
        if re.match(r'^(CORE\s+)?SKILLS?\s*[:\-]?$', s, re.I):
            for j in range(i + 1, min(i + 8, len(raw))):
                candidate = raw[j].strip()
                if not candidate:
                    continue
                if is_section_heading(candidate):
                    break
                if is_contact_line(candidate):
                    continue
                if candidate.count(',') >= 1 and len(candidate) < 250:
                    skills = smart_trim(candidate)
                    break
            if skills != 'strategic planning, execution, and team leadership':
                break

    # fallback
    if skills == 'strategic planning, execution, and team leadership':
        for line in raw[:80]:
            s = line.strip()
            if not s or is_contact_line(s) or is_section_heading(s):
                continue
            if s.count(',') >= 2 and len(s) < 250:
                skills = smart_trim(s)
                break

    # strip leading category label like "Content and social media: "
    if ':' in skills and skills.index(':') < 60:
        after = skills[skills.index(':') + 1:].strip()
        if after and len(after) > 20:
            skills = after

    import datetime
    date = datetime.datetime.now().strftime('%B %d, %Y')

    tmpl = TEMPLATES.get(template, TEMPLATES['professional'])
    return tmpl.format(
        date=date,
        role=role,
        company=company,
        years=years,
        field=field,
        highlight=highlight,
        current_company=current_company,
        accomplishment=accomplishment,
        reason=reason,
        skills=skills,
        name=name or 'Your Name',
        email=email,
        phone=phone,
    )
