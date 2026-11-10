"""Every desktop tool and its visible controls, in one place."""
from dataclasses import dataclass, field


@dataclass
class Field:
    key: str
    label: str
    kind: str = 'text'
    default: object = ''
    options: list = field(default_factory=list)
    hint: str = ''
    required: bool = False


@dataclass
class Tool:
    key: str
    title: str
    group: str
    description: str
    button: str
    fields: list
    note: str = ''


def file(key='input', label='Resume', extensions='DOCX / PDF / TXT'):
    return Field(key, label, 'file', hint=extensions, required=True)


def choice(key, label, values, default=None):
    return Field(key, label, 'choice', default or values[0], values)


MODE = choice('mode', 'Injection mode', ['safe', 'aggressive', 'nuclear'])
LANG = choice('lang', 'Metadata language', ['en', 'hi', 'es', 'fr', 'de', 'ja', 'ar', 'zh'])
ATS = choice('ats', 'ATS profile', ['unknown', 'greenhouse', 'lever', 'workday', 'workable', 'smartrecruiters', 'icims', 'taleo', 'jobvite', 'linkedin'])
PDF = Field('pdf', 'Also export a PDF', 'bool', False)
CHANNELS = ['metadata', 'hidden_text', 'comments', 'zero_width', 'headers_footers', 'fields', 'split_payload', 'base64', 'acrostic', 'fake_recruiter', 'whitespace', 'image', 'audio', 'qr', 'font']
CHANNEL_INFO = {
    'metadata': ('DOCX metadata', 'Subject, description, keywords and category in core.xml.'),
    'hidden_text': ('Hidden text', 'Hidden and white-text runs inside document paragraphs.'),
    'comments': ('Document comments', 'Instructions stored in the DOCX comments part.'),
    'zero_width': ('Zero-width Unicode', 'The existing zero-width character encoding.'),
    'headers_footers': ('Headers and footers', 'Hidden runs in existing header and footer parts.'),
    'fields': ('Word field codes', 'Instructions stored in Word field-code runs.'),
    'split_payload': ('Split payloads', 'The existing instruction fragments in hidden runs.'),
    'base64': ('Base64 injection', 'The encoded instruction inside a hidden document run.'),
    'acrostic': ('Acrostic injection', 'The existing acrostic lines in hidden text.'),
    'fake_recruiter': ('Recruiter-note fixture', 'The existing simulated recruiter-note payload.'),
    'whitespace': ('Whitespace encoding', 'The existing space/tab encoding in document text.'),
    'image': ('Image metadata', 'JPEG EXIF/XMP, PNG text chunks, WebP EXIF and DOCX image alt-text.'),
    'audio': ('Audio / video metadata', 'Metadata in existing MP3, MP4/M4A, FLAC, OGG and WebM parts.'),
    'qr': ('QR code injection', 'Create and embed the existing QR instruction image.'),
    'font': ('Font metadata', 'Name-table metadata in existing embedded obfuscated fonts.'),
}
DEEP_CHANNELS = ['theme', 'numbering', 'settings', 'custom_properties', 'zip_comment']
CHECKS = Field('channels', 'Channels', 'checks', ['metadata'], CHANNELS)
TOOLS = [
    Tool('review', 'Resume review', 'WORKSPACE', 'See your score, writing suggestions and extracted text in one review.', 'Analyze resume', [file()], 'Scores are local heuristics, not a prediction of hiring outcomes.'),
    Tool('inspect', 'Document inspector', 'WORKSPACE', 'Read document text, metadata, hidden runs, images, audio and fonts.', 'Inspect document', [file()]),
    Tool('inject', 'Injection studio', 'INJECTION TOOLS', 'All 15 original injection channels, selectable individually or together.', 'Create injected copy', [file(extensions='DOCX'), MODE, LANG, Field('custom', 'Use individual channel selection', 'bool', False), CHECKS, PDF], 'All channels selects nuclear mode and all 15 channels. Audio, fonts and headers need matching document parts. Language applies to core metadata.'),
    Tool('full', 'Full pipeline', 'WORKSPACE', 'Analyze, suggest, inject, verify and export a complete local report.', 'Run full pipeline', [file(extensions='DOCX'), MODE, LANG, PDF]),
    Tool('pdf', 'PDF export', 'WORKSPACE', 'Turn a Word document into a portable PDF with text and embedded images.', 'Export PDF', [file(extensions='DOCX'), Field('metadata', 'Preserve metadata and hidden metadata text', 'bool', True)], 'Standalone export reflows content. Complex Word layout, tables, headers and fonts may differ.'),
    Tool('cover', 'Cover letter', 'WORKSPACE', 'Draft a cover letter from your resume and a pasted job description.', 'Generate draft', [file(), Field('jd', 'Job description', 'area', hint='Job title: …\nCompany: …\nResponsibilities and requirements', required=True), choice('template', 'Writing style', ['professional', 'short', 'career_change']), PDF], 'Uses the existing template engine, not an online AI model. Review inferred details and claims before using the draft.'),
    Tool('cover_inject', 'Cover-letter injection', 'WORKSPACE', 'Apply cover-letter metadata, hidden runs and comments to a copy.', 'Create test cover letter', [file(label='Cover letter', extensions='DOCX'), MODE]),
    Tool('batch', 'Batch processor', 'WORKSPACE', 'Review and inject every DOCX directly inside a selected folder.', 'Process folder', [Field('folder', 'Input folder', 'folder', required=True), MODE, LANG, PDF]),
    Tool('diff', 'Compare documents', 'WORKSPACE', 'Compare internal document parts and readable text between two versions.', 'Compare versions', [file('input', 'Original', 'DOCX'), file('second', 'Changed version', 'DOCX')]),
    Tool('stealth', 'Randomized plan', 'DOCUMENT LAB', 'Select and apply a randomized subset of the existing channels.', 'Build randomized copy', [file(extensions='DOCX'), MODE, LANG, PDF]),
    Tool('deep', 'Deep metadata', 'DOCUMENT LAB', 'Choose theme, numbering, settings, custom properties and ZIP metadata.', 'Create deep-metadata copy', [file(extensions='DOCX'), Field('deep_channels', 'Deep metadata channels', 'checks', DEEP_CHANNELS[:], DEEP_CHANNELS)]),
    Tool('font', 'Embedded test font', 'DOCUMENT LAB', 'Generate a minimal font fixture and embed its name-table metadata.', 'Embed test font', [file(extensions='DOCX')], 'This fixture is not a replacement font for resume body text.'),
    Tool('lsb', 'Image encoding', 'DOCUMENT LAB', 'Encode or decode UTF-8 text in image pixels, or the first DOCX image.', 'Process image', [file(label='Image or DOCX', extensions='PNG / JPEG / WebP / DOCX'), choice('operation', 'Operation', ['encode', 'decode']), Field('text', 'Text to encode', 'area', 'Local test message')], 'Encoding changes pixel values slightly. Image outputs are lossless PNG files.'),
    Tool('merge', 'Merge documents', 'DOCUMENT LAB', 'Combine a cover letter and resume, preserving linked images and styles.', 'Merge documents', [file('input', 'Cover letter', 'DOCX'), file('second', 'Resume', 'DOCX')]),
    Tool('style', 'Font styling', 'DOCUMENT LAB', 'Apply a consistent font to a copy, or draw a randomized style seed.', 'Create styled copy', [file(extensions='DOCX'), choice('font', 'Font', ['Random', 'Calibri', 'Arial', 'Times New Roman', 'Georgia', 'Verdana', 'Tahoma', 'Cambria'])], 'Only font styling is applied. A random seed’s section order and color are suggestions.'),
    Tool('payloads', 'Payload library', 'DOCUMENT LAB', 'Inspect language packs, variants, encodings and script transformations.', 'Generate payload reference', [LANG, choice('variant', 'Variant', ['A', 'B', 'C', 'D']), choice('encoding', 'Text transformation', ['plain', 'base64', 'whitespace', 'cyrillic', 'devanagari', 'combining']), Field('text', 'Optional custom text', 'area')]),
    Tool('notes', 'Portal notes', 'DOCUMENT LAB', 'Generate the toolkit’s note variants for manual review.', 'Generate note', [choice('variant', 'Variant', ['A', 'B', 'C', 'D']), choice('style', 'Length', ['brief', 'full', 'minimal'])]),
    Tool('ats', 'ATS fingerprint', 'RESEARCH', 'Identify the platform from a URL and public page markup.', 'Identify platform', [Field('url', 'Job or company URL', hint='https://…', required=True)], 'Profile weights are assumptions in the toolkit, not measured success rates.'),
    Tool('probe', 'Browser inspection', 'RESEARCH', 'Load one public page in the bundled browser and inspect visible controls.', 'Inspect page · read only', [Field('url', 'Public job page URL', hint='https://…', required=True)], 'Never clicks Apply, fills fields, uploads files or submits. Stops on login or payment pages. No account session is used.'),
    Tool('extraction', 'Extraction analysis', 'RESEARCH', 'Check text you obtained from a controlled parser test for channel markers.', 'Analyze extracted text', [Field('text', 'Extracted text', 'area', required=True)], 'Marker detection proves text survived extraction; it does not prove an AI system followed it.'),
    Tool('tuning', 'ATS tuning', 'RESEARCH', 'View heuristic channel weights or update them from a saved local probe report.', 'Load or update weights', [ATS, Field('report', 'Optional probe JSON', 'file', hint='JSON')], 'Weights are local experimental settings. Importing a report changes only your local tuning file.'),
    Tool('track', 'Outcome tracker', 'RESEARCH', 'Keep a local journal of tests and outcomes. This never sends an application.', 'Save / load journal', [choice('operation', 'Action', ['view', 'record', 'update']), Field('company', 'Company'), Field('role', 'Role'), ATS, MODE, choice('variant', 'Variant', ['A', 'B', 'C', 'D']), Field('record_id', 'Record ID for update'), choice('status', 'Outcome', ['pending', 'screen', 'interview', 'rejected', 'offer']), Field('notes', 'Notes', 'area')]),
]
DEDICATED_CHANNELS = {'channel_'+name: name for name in CHANNELS}
dedicated_tools = [
    Tool('channel_'+name, CHANNEL_INFO[name][0], 'INJECTION TOOLS', CHANNEL_INFO[name][1],
         'Run '+CHANNEL_INFO[name][0].lower(),
         [file(extensions='DOCX')] +
         ([LANG] if name == 'metadata' else []) +
         ([choice('mode', 'Media detail level', ['aggressive', 'nuclear'])] if name == 'image' else []) + [PDF],
         'Only this channel is applied to a new copy. Existing media or header/footer parts are required where applicable.')
    for name in CHANNELS
]
studio = next(t for t in TOOLS if t.key == 'inject')
remaining = [t for t in TOOLS if t.key != 'inject']
TOOLS = [studio] + dedicated_tools + remaining
TOOLS.append(Tool('addon_checks', 'Addon verification', 'DOCUMENT LAB', 'Check local recovery, encryption and fresh database behavior using synthetic data.', 'Run local checks', [], 'Seven smoke checks; not the full audit or proof of live ATS recovery.'))
BY_KEY = {t.key: t for t in TOOLS}
