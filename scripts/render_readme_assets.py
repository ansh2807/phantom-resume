"""Render original geometric README artwork. Uses no user documents or screenshots."""
from pathlib import Path
import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
BG = '#0b1117'
WHITE = '#edf4f1'
MINT = '#98f5cc'
GRAY = '#8eaaa8'


def font(size, mono=False, bold=False):
    windir = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    names = ([windir / 'consola.ttf', Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')]
             if mono else [windir / ('segoeuib.ttf' if bold else 'segoeui.ttf'),
                           Path('/usr/share/fonts/truetype/dejavu/' + ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'))])
    for name in names:
        if name.exists():
            return ImageFont.truetype(str(name), size)
    return ImageFont.load_default(size=size)


def ghost(draw, x, y, size, fill=MINT):
    draw.rounded_rectangle((x, y, x + size, y + size), radius=size * .48, fill=fill)
    draw.rectangle((x, y + size * .48, x + size, y + size * .9), fill=fill)
    for i in range(3):
        left = x + size * i / 3
        draw.polygon([(left, y + size * .85), (left + size / 6, y + size * 1.05),
                      (left + size / 3, y + size * .85)], fill=fill)
    for offset in [.28, .66]:
        draw.rounded_rectangle((x + size * offset, y + size * .35,
                                x + size * (offset + .1), y + size * .53), radius=size * .04, fill=BG)


def render():
    ASSETS.mkdir(exist_ok=True)
    hero = '''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="540" viewBox="0 0 1440 540" role="img" aria-labelledby="title desc">
<title id="title">PhantomResume</title><desc id="desc">See the document behind the resume. Python tools for local analysis, inspection, and controlled experiments.</desc>
<defs><pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="#1c2b32" stroke-width="1"/></pattern><linearGradient id="fade"><stop stop-color="#0b1117"/><stop offset="1" stop-color="#13262b"/></linearGradient></defs>
<rect width="1440" height="540" rx="24" fill="url(#fade)"/><rect x="890" width="550" height="540" fill="url(#grid)"/>
<path d="M62 70H84M62 70V92M1378 448V470H1356" stroke="#98f5cc" stroke-width="2" fill="none"/>
<g font-family="Segoe UI,Helvetica,Arial,sans-serif">
<text x="96" y="86" fill="#98f5cc" font-size="16" letter-spacing="4">DOCUMENT INTELLIGENCE / EXPERIMENTAL TOOLKIT</text>
<text x="92" y="226" fill="#edf4f1" font-size="103" font-weight="700" letter-spacing="-5">PhantomResume<tspan fill="#98f5cc">.</tspan></text>
<text x="98" y="289" fill="#b6c8c7" font-size="30">See the document behind the resume.</text>
<text x="98" y="333" fill="#789a99" font-size="21">Inspect text. Trace metadata. Verify local experiments.</text>
<path d="M98 386H820" stroke="#304249"/>
<text x="98" y="429" fill="#edf4f1" font-size="18" letter-spacing="2">PYTHON CLI</text>
<text x="295" y="429" fill="#789a99" font-size="18">/</text>
<text x="333" y="429" fill="#edf4f1" font-size="18" letter-spacing="2">16 COMMANDS</text>
<text x="560" y="429" fill="#789a99" font-size="18">/</text>
<text x="598" y="429" fill="#edf4f1" font-size="18" letter-spacing="2">OPEN SOURCE</text>
</g>
<circle cx="1170" cy="265" r="174" fill="none" stroke="#304f50"/><circle cx="1170" cy="265" r="147" fill="none" stroke="#223c40" stroke-dasharray="3 12"/>
<path d="M1070 300V216a100 100 0 0 1 200 0v131l-33-28-34 28-33-28-34 28-33-28-33 28Z" fill="#98f5cc"/>
<rect x="1122" y="226" width="17" height="32" rx="8" fill="#0b1117"/><rect x="1201" y="226" width="17" height="32" rx="8" fill="#0b1117"/>
<circle cx="1344" cy="265" r="6" fill="#98f5cc"/><circle cx="1047" cy="142" r="4" fill="#bcb2ff"/>
</svg>'''
    (ASSETS / 'hero.svg').write_text(hero, encoding='utf-8')
    stages = [
        ('01', 'Inspect the source.', 'Read the text and structure.',
         '$ phantom_resume.py inspect fixture.docx',
         [('DOCUMENT', 'test-candidate.docx'), ('IDENTITY', 'Test Candidate'), ('SECTIONS', 'Summary / Skills / Experience'), ('SOURCE', 'Synthetic fixture only')]),
        ('02', 'Map the channels.', 'Understand what changes.',
         '$ phantom_resume.py diff original.docx copy.docx',
         [('CORE', 'Document metadata'), ('BODY', 'Text + comments + Unicode'), ('MEDIA', 'EXIF / PNG / QR / alt-text'), ('SCOPE', 'Local document experiment')]),
        ('03', 'Verify the output.', 'Look for evidence in the file.',
         '$ python -m unittest discover -s tests',
         [('CHECK', 'Metadata and text extraction'), ('CHECK', 'PDF counters and image objects'), ('CHECK', 'Read-only probe control flow'), ('METHOD', 'Synthetic data + mock browsers')]),
        ('04', 'Know the boundary.', 'A file check is not an ATS result.',
         '$ phantom_resume.py probe ... --probe-only',
         [('INSPECT', 'Find form and file input'), ('NO', 'Field filling or file upload'), ('NO', 'Application submission'), ('RESULT', 'Automation check only')]),
    ]
    fsmall, fmono, fbody, ftitle = font(14, mono=True), font(18, mono=True), font(22), font(46, bold=True)
    frames = []
    total = 96
    for n in range(total):
        stage = n // 24
        local = (n % 24) / 23
        num, title, sub, command, rows = stages[stage]
        canvas = Image.new('RGB', (1200, 600), BG)
        d = ImageDraw.Draw(canvas)
        for x in range(690, 1200, 40):
            d.line((x, 0, x, 600), fill='#122029')
        for y in range(0, 600, 40):
            d.line((690, y, 1200, y), fill='#122029')
        d.text((42, 30), 'PHANTOMRESUME / LOCAL WORKFLOW', font=fsmall, fill=MINT)
        d.text((879, 30), 'ILLUSTRATED DEMO  /  LOOP', font=fsmall, fill=GRAY)
        d.line((42, 68, 1158, 68), fill='#27373f')
        d.text((44, 100), num, font=font(90, mono=True), fill='#24443f')
        d.text((43, 219), title, font=ftitle, fill=WHITE)
        d.text((46, 285), sub, font=fbody, fill=GRAY)
        ghost(d, 48, 360 + math.sin(n / total * math.tau * 4) * 7, 76)
        d.text((149, 376), 'Test Candidate', font=font(20, bold=True), fill=WHITE)
        d.text((149, 407), 'Synthetic inputs. Local outputs.', font=font(16), fill=GRAY)
        d.rounded_rectangle((550, 111, 1158, 480), radius=16, fill='#111d25', outline='#2a414a', width=1)
        for i, color in enumerate(['#98f5cc', '#bcb2ff', '#7fa4af']):
            d.ellipse((574 + i*18, 131, 582 + i*18, 139), fill=color)
        d.text((642, 127), 'phantom / workspace', font=fsmall, fill=GRAY)
        d.line((550, 157, 1158, 157), fill='#2a414a')
        # Commands are illustrative labels, not a fabricated execution transcript.
        typed = command[:max(1, int(len(command) * min(1, local * 3.5)))]
        d.text((574, 177), typed, font=font(14, mono=True), fill=MINT)
        for i, (label, value) in enumerate(rows):
            reveal = min(1, max(0, local * 4 - i * .28))
            if reveal <= 0:
                continue
            y = 234 + i*52
            color = tuple(int(v*reveal) for v in (237,244,241))
            d.text((574, y), label, font=fsmall, fill=GRAY)
            d.text((684, y - 3), value, font=font(17), fill=color)
            if i < 3:
                d.line((574, y + 30, 1134, y + 30), fill='#1d3039')
        labels = ['INSPECT', 'EXPERIMENT', 'VERIFY', 'UNDERSTAND']
        for i, label in enumerate(labels):
            x = 44 + i*287
            d.line((x, 531, x+247, 531), fill='#293a41', width=2)
            if i < stage:
                d.line((x, 531, x+247, 531), fill=MINT, width=2)
            elif i == stage:
                d.line((x, 531, x+int(247*local), 531), fill=MINT, width=2)
            d.text((x, 548), f'0{i+1}  {label}', font=fsmall, fill=MINT if i == stage else GRAY)
        frames.append(canvas)
    frames[70].save(ASSETS / 'workflow-still.png')
    palette = frames[70].quantize(colors=128)
    quantized = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in frames]
    quantized[0].save(ASSETS / 'workflow.gif', save_all=True, append_images=quantized[1:],
                      duration=125, loop=0, optimize=True, disposal=2)
    print(f'Created hero.svg, workflow.gif ({len(frames)} frames), and workflow-still.png')


if __name__ == '__main__':
    render()
