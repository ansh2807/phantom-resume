"""Desktop service layer. Every write goes to a unique output directory."""
from pathlib import Path
import base64
import difflib
import hashlib
import html
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import uuid
import zipfile
from datetime import datetime
from xml.etree import ElementTree as ET

from .catalog import BY_KEY, DEDICATED_CHANNELS, DEEP_CHANNELS, CHANNELS

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'


def data_root():
    p = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'PhantomResume Desktop'
    p.mkdir(parents=True, exist_ok=True)
    return p


def default_output():
    return Path.home() / 'Documents' / 'PhantomResume Exports'


def resource_root():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))


def scratch_root(required_bytes):
    """Prefer the user temp location; use a local fixed drive if it is full."""
    import tempfile
    default = Path(tempfile.gettempdir())
    if shutil.disk_usage(default).free >= required_bytes:
        return default
    if os.name == 'nt':
        import ctypes
        for letter in 'DEFGHIJKLMNOPQRSTUVWXYZC':
            volume = f'{letter}:/'
            if ctypes.windll.kernel32.GetDriveTypeW(volume) == 3 and shutil.disk_usage(volume).free >= required_bytes:
                root = Path(volume)/'PhantomResume Temporary'
                root.mkdir(exist_ok=True)
                return root
    raise OSError('Not enough temporary disk space. Free at least 1 GB for browser inspection, or 20 MB for document tools.')


def serialize(value):
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def checked_file(params, key='input', suffix=None):
    path = Path(params.get(key, '')).expanduser()
    if not path.is_file():
        raise ValueError(f'Choose an existing file for {key.replace("_", " ")}.')
    if suffix and path.suffix.lower() not in suffix:
        raise ValueError('This tool requires ' + ', '.join(suffix) + ' files.')
    if path.stat().st_size > 128*1024*1024:
        raise ValueError('File exceeds the 128 MB desktop limit. Split it into smaller documents.')
    if path.suffix.lower() == '.docx':
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > 5000 or sum(i.file_size for i in entries) > 512*1024*1024:
                raise ValueError('DOCX expands beyond the desktop processing limit (512 MB or 5,000 parts).')
    return path.resolve()


def validate_url(value):
    from urllib.parse import urlsplit
    parts = urlsplit(value)
    if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password:
        raise ValueError('Enter a complete http:// or https:// URL without account credentials.')
    return value


def inspect_document(path):
    from core.resume_verifier import ResumeVerifier
    if path.suffix.lower() != '.docx':
        return ResumeVerifier(path).extract()
    from PIL import Image, ExifTags
    result = {'all_text': '', 'metadata': {}, 'hidden_text': '', 'comments': [], 'images': [], 'audio': [], 'fonts': [], 'qr_codes': [], 'other_parts': []}
    with zipfile.ZipFile(path) as z:
        if 'docProps/core.xml' in z.namelist():
            result['metadata'] = {e.tag.split('}')[-1]: e.text or '' for e in ET.fromstring(z.read('docProps/core.xml'))}
        root = ET.fromstring(z.read('word/document.xml'))
        result['all_text'] = '\n'.join(''.join(t.text or '' for t in p.iter(W+'t')) for p in root.iter(W+'p'))
        hidden = []
        for run in root.iter(W+'r'):
            prop = run.find(W+'rPr')
            if prop is not None and (prop.find(W+'vanish') is not None or any(c.tag == W+'color' and c.get(W+'val', '').upper() == 'FFFFFF' for c in prop)):
                hidden.extend(t.text or '' for t in run.iter(W+'t'))
        result['hidden_text'] = '\n'.join(hidden)
        if 'word/comments.xml' in z.namelist():
            result['comments'] = [t.text or '' for t in ET.fromstring(z.read('word/comments.xml')).iter(W+'t')]
        result['zip_comment'] = z.comment.decode('utf-8', 'replace')
        for name in z.namelist():
            if name.startswith('word/media/'):
                if Path(name).suffix.lower() in ('.mp3', '.mp4', '.wav', '.ogg', '.flac', '.webm', '.m4a'):
                    audio_item = {'part': name, 'bytes': len(z.read(name))}
                    try:
                        import mutagen
                        from mutagen.id3 import ID3
                        raw_audio = io.BytesIO(z.read(name))
                        tags = ID3(raw_audio) if name.lower().endswith('.mp3') else mutagen.File(raw_audio)
                        audio_item['tags'] = {str(k): str(v)[:2000] for k, v in tags.items()} if tags else {}
                    except Exception as e:
                        audio_item['metadata_read_error'] = str(e)
                    result['audio'].append(audio_item)
                    continue
                try:
                    with Image.open(io.BytesIO(z.read(name))) as image:
                        result['images'].append({'part': name, 'format': image.format, 'size': image.size,
                            'exif': {ExifTags.TAGS.get(k, str(k)): str(v)[:2000] for k, v in image.getexif().items()},
                            'info': {k: str(v)[:2000] for k, v in image.info.items()},
                            'pixels_sha256': hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()})
                        if image.format == 'PNG':
                            try:
                                from pyzbar.pyzbar import decode
                                for code in decode(image):
                                    result['qr_codes'].append({'part': name, 'type': code.type, 'text': code.data.decode('utf-8', 'replace')})
                            except Exception as e:
                                result['images'][-1]['code_decode_error'] = str(e)
                except Exception as e:
                    result['images'].append({'part': name, 'error': str(e)})
            elif name.startswith('word/fonts/'):
                result['fonts'].append({'part': name, 'bytes': len(z.read(name))})
            elif name not in ('word/document.xml', 'docProps/core.xml'):
                result['other_parts'].append(name)
        # Validate XML without claiming schema validation or Word compatibility.
        errors = []
        for name in z.namelist():
            if name.endswith(('.xml', '.rels')):
                try:
                    ET.fromstring(z.read(name))
                except ET.ParseError as e:
                    errors.append(f'{name}: {e}')
        result['xml_parse_errors'] = errors
    return result


def export_pdf(source, destination, keep_metadata=True):
    """Portable export, preserving text + images without needing Microsoft Word."""
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor, white
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PIL import Image as PILImage
    from docx import Document
    doc = Document(source)
    font = 'Helvetica'
    for fontpath in (Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/'arial.ttf',):
        if fontpath.exists():
            if 'DesktopArial' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('DesktopArial', str(fontpath)))
            font = 'DesktopArial'
            break
    normal = ParagraphStyle('body', fontName=font, fontSize=10, leading=15, spaceAfter=7, textColor=HexColor('#253044'), splitLongWords=True)
    heading = ParagraphStyle('heading', parent=normal, fontSize=15, leading=20, spaceBefore=9)
    hidden = ParagraphStyle('hidden', parent=normal, fontSize=1, leading=1, textColor=white, spaceAfter=0)
    metadata = inspect_document(source)['metadata'] if keep_metadata else {}
    pdf = SimpleDocTemplate(str(destination), leftMargin=48, rightMargin=48, topMargin=42, bottomMargin=42,
        title=metadata.get('title', '') or source.stem, author=metadata.get('creator', ''),
        subject=metadata.get('subject', ''), keywords=metadata.get('keywords', ''), creator='PhantomResume Desktop')
    flow, paragraphs, images, warnings = [], 0, 0, []
    if keep_metadata:
        for value in metadata.values():
            if value:
                flow.append(Paragraph(html.escape(value), hidden))
    for p in doc.element.body.iter(W+'p'):
        fragments, visible_text = [], []
        for run in p.iter(W+'r'):
            value = ''.join(t.text or '' for t in run.iter(W+'t'))
            prop = run.find(W+'rPr')
            is_hidden = prop is not None and (prop.find(W+'vanish') is not None or any(c.tag == W+'color' and c.get(W+'val', '').upper() == 'FFFFFF' for c in prop))
            if is_hidden:
                if keep_metadata and value:
                    fragments.append('<font color="#ffffff" size="1">'+html.escape(value)+'</font>')
            else:
                fragments.append(html.escape(value))
                visible_text.append(value)
        text = ''.join(fragments)
        if text.strip():
            pstyle = p.find(W+'pPr/'+W+'pStyle')
            style = heading if pstyle is not None and ('Heading' in pstyle.get(W+'val', '') or pstyle.get(W+'val') == 'Title') else normal
            if not ''.join(visible_text).strip():
                style = hidden
            flow.append(Paragraph(text, style))
            paragraphs += 1
        for blip in p.iter(A+'blip'):
            rid = blip.get(R+'embed')
            if not rid:
                continue
            try:
                data = doc.part.related_parts[rid].blob
                image = PILImage.open(io.BytesIO(data))
                width, height = image.size
                scale = min(144/width, 144/height, 1)
                flow.append(Image(io.BytesIO(data), width=width*scale, height=height*scale, hAlign='LEFT'))
                flow.append(Spacer(1, 8))
                images += 1
            except Exception as e:
                warnings.append(f'Image {rid} could not be exported: {e}')
    if not flow:
        flow.append(Paragraph('Empty document', normal))
    pdf.build(flow)
    return {'engine': 'Portable ReportLab', 'paragraphs': paragraphs, 'images': images, 'bytes': destination.stat().st_size, 'warnings': warnings,
        'layout_note': 'Reflowed layout; not a pixel-exact Word rendering. Unsupported glyphs may not render.'}


def normalize_document(path):
    """Wrap legacy body-level runs in paragraphs; keep section properties last."""
    from lxml import etree
    with zipfile.ZipFile(path) as z:
        parts = {n: z.read(n) for n in z.namelist()}
        comment = z.comment
    for name in list(parts):
        if name != 'word/document.xml' and not re.match(r'word/(header|footer)\d+\.xml$', name):
            continue
        root = etree.fromstring(parts[name])
        containers = list(root.iter(W+'body')) if name == 'word/document.xml' else [root]
        for parent in containers:
            for child in list(parent):
                if child.tag == W+'r':
                    index = parent.index(child)
                    parent.remove(child)
                    paragraph = etree.Element(W+'p')
                    paragraph.append(child)
                    parent.insert(index, paragraph)
            for section in list(parent.findall(W+'sectPr')):
                parent.remove(section)
                parent.append(section)
        parts[name] = etree.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, value in parts.items():
            z.writestr(name, value)
        z.comment = comment


def browser_inspect(url, output):
    from playwright.sync_api import sync_playwright
    from core.ats_fingerprint import detect_ats_from_url
    archive = resource_root()/'browser-bundle.zip'
    own_temporary = None
    bundled = resource_root() / 'browser' / 'chrome.exe'
    if archive.exists():
        import tempfile
        context_dir = os.environ.get('PHANTOM_JOB_TEMP')
        if context_dir:
            unpack = Path(context_dir)/'browser'
        else:
            own_temporary = tempfile.TemporaryDirectory(prefix='phantom-browser-', dir=scratch_root(1024*1024*1024))
            unpack = Path(own_temporary.name)
        try:
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(unpack)
        except Exception:
            if own_temporary:
                own_temporary.cleanup()
            raise
        bundled = unpack/'chrome.exe'
    with sync_playwright() as pw:
        opts = {'headless': True}
        if bundled.exists():
            opts['executable_path'] = str(bundled)
        browser = pw.chromium.launch(**opts)
        try:
            context = browser.new_context(viewport={'width': 1280, 'height': 850})
            page = context.new_page()
            response = page.goto(validate_url(url), wait_until='domcontentloaded', timeout=25000)
            page.wait_for_timeout(800)
            body = page.locator('body').inner_text(timeout=5000)
            title = page.title()
            stopped = bool(page.locator('input[type=password], input[autocomplete="cc-number"]').count())
            stopped = stopped or bool(re.search(r'/(login|signin|sign-in|checkout|payment|sso)(?:[/?.]|$)', page.url, re.I))
            stopped = stopped or bool(re.search(r'^(sign in|log in|payment|checkout)', title, re.I))
            controls = []
            if not stopped:
                controls = page.locator('a, button, input, select, textarea').evaluate_all("els => els.filter(e => e.getBoundingClientRect().width && e.getBoundingClientRect().height).slice(0,150).map(e => ({tag:e.tagName,type:e.type||'',text:(e.innerText||e.getAttribute('aria-label')||e.placeholder||'').slice(0,160),href:e.href||''}))")
            shot = output / 'page-preview.png'
            page.screenshot(path=str(shot))
            return {'title': title, 'final_url': page.url, 'status': response.status if response else None,
                'ats': detect_ats_from_url(page.url) or 'unknown', 'stopped': stopped,
                'message': 'Stopped: account or payment page detected.' if stopped else 'Read-only inspection complete. No controls clicked or fields filled.',
                'controls': controls, 'page_text': '' if stopped else body[:30000], 'screenshot': str(shot)}
        finally:
            browser.close()
            if own_temporary:
                own_temporary.cleanup()


def encode_docx(source, destination, text):
    from PIL import Image
    from core.lsb_stego import encode_image, decode_image
    with zipfile.ZipFile(source) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    for name, content in parts.items():
        if not name.startswith('word/media/'):
            continue
        try:
            Image.open(io.BytesIO(content)).verify()
        except Exception:
            continue
        encoded = encode_image(content, text)
        # Keep the part path and declare its actual PNG media type explicitly.
        parts[name] = encoded
        ns = 'http://schemas.openxmlformats.org/package/2006/content-types'
        root = ET.fromstring(parts['[Content_Types].xml'])
        for element in list(root):
            if element.get('PartName') == '/'+name:
                root.remove(element)
        ET.SubElement(root, '{'+ns+'}Override', PartName='/'+name, ContentType='image/png')
        parts['[Content_Types].xml'] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as z:
            for n, b in parts.items():
                z.writestr(n, b)
        if decode_image(encoded) != text:
            raise ValueError('Image round-trip verification failed.')
        return {'part': name, 'verified_text': text, 'format': 'PNG', 'pixel_values_changed': True}
    raise ValueError('No supported embedded image found in this DOCX.')


def run_tool(key, params, progress=lambda x: None, state_dir=None):
    """Shared by UI and tests. No current-directory dependence or shell calls."""
    tool = BY_KEY[key]
    for field in tool.fields:
        if field.required and not str(params.get(field.key, '')).strip():
            raise ValueError(f'{field.label} is required.')
    output = Path(params.get('output') or default_output()).expanduser()
    output.mkdir(parents=True, exist_ok=True)
    run_id = params.get('_job_id')
    if run_id is not None and not re.fullmatch(r'[0-9a-f]{32}', run_id):
        raise ValueError('Invalid internal run identifier.')
    job = output / (run_id or (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + key + '-' + uuid.uuid4().hex[:6]))
    job.mkdir()
    incomplete = job/'INCOMPLETE.txt'
    incomplete.write_text('This run has not completed. If cancelled or interrupted, files here may be partial. Original inputs are unchanged.\n', encoding='utf-8')
    state = Path(state_dir) if state_dir else data_root()
    state.mkdir(parents=True, exist_ok=True)
    progress('Preparing '+tool.title.lower())
    data, files, warnings = {}, [], []
    mode, lang = params.get('mode', 'safe'), params.get('lang', 'en')
    selected_channel = DEDICATED_CHANNELS.get(key)
    if selected_channel:
        mode = params.get('mode') or 'aggressive'
    from core.resume_analyzer import ResumeAnalyzer
    from core.resume_improver import ResumeImprover
    from core.resume_injector import ResumeInjector

    def inject(source, destination, plan=None):
        obj = ResumeInjector(source, destination, mode=mode, lang=lang)
        obj.channel_plan = plan
        report = obj.run()
        normalize_document(destination)
        warnings.extend(report.get('errors', []))
        with zipfile.ZipFile(destination) as z:
            if z.testzip():
                raise ValueError('Output failed archive integrity validation.')
        return report

    if key == 'addon_checks':
        from desktop.addon_checks import run_checks
        data = run_checks()
        if data['failed']:
            raise RuntimeError('Addon verification failed: '+serialize(data))
    elif key in ('review', 'full'):
        source = checked_file(params, suffix=('.docx',) if key == 'full' else ('.docx', '.pdf', '.txt'))
        analysis = ResumeAnalyzer(source).run()
        data = {'analysis': analysis, 'suggestions': ResumeImprover(analysis).generate()}
        if key == 'review':
            data['inspection'] = inspect_document(source)
    if key in ('inject', 'full', 'stealth') or selected_channel:
        source = checked_file(params, suffix=('.docx',))
        destination = job / (source.stem + '-test.docx')
        plan = params.get('channels', []) if params.get('custom') else None
        if selected_channel:
            plan = [selected_channel]
        if key == 'stealth':
            from core.stealth_mode import randomize_injection_plan
            plan = randomize_injection_plan(mode, lang)
        progress('Creating document copy and running selected channels')
        data['injection'] = inject(source, destination, plan)
        data['channel_plan'] = plan if plan is not None else 'Mode defaults'
        data['inspection'] = inspect_document(destination)
        selected = plan if plan is not None else [c for c in CHANNELS if ResumeInjector(source, destination, mode)._should(c)]
        inventory = data['inspection']
        missing = []
        if 'audio' in selected and not inventory['audio']:
            missing.append('Audio/video: no matching embedded media was found.')
        if 'font' in selected and not inventory['fonts']:
            missing.append('Font metadata: no embedded font was found. Use Embedded test font to create a fixture first.')
        if 'headers_footers' in selected and not any(n.startswith(('word/header', 'word/footer')) for n in inventory['other_parts']):
            missing.append('Headers/footers: the document has no existing header or footer parts.')
        data['skipped_channels'] = missing
        warnings.extend(data['inspection']['xml_parse_errors'])
        files.append(destination)
        if params.get('pdf'):
            progress('Exporting PDF')
            pdf = destination.with_suffix('.pdf')
            data['pdf'] = export_pdf(destination, pdf)
            warnings.extend(data['pdf']['warnings'])
            files.append(pdf)
    elif key == 'inspect':
        data = inspect_document(checked_file(params, suffix=('.docx', '.pdf', '.txt')))
    elif key == 'pdf':
        source = checked_file(params, suffix=('.docx',))
        pdf = job / (source.stem + '.pdf')
        data = export_pdf(source, pdf, params.get('metadata', True))
        warnings.extend(data['warnings'])
        files.append(pdf)
    elif key == 'cover':
        from core.cover_generator import generate_cover_letter
        from docx import Document
        source = checked_file(params, suffix=('.docx', '.pdf', '.txt'))
        letter = generate_cover_letter(ResumeAnalyzer(source).run(), params['jd'], params.get('template', 'professional'))
        doc = Document()
        doc.core_properties.author = 'PhantomResume Desktop'
        for paragraph in letter.split('\n\n'):
            doc.add_paragraph(paragraph.strip())
        dest = job/'cover-letter-draft.docx'
        doc.save(dest)
        text = job/'cover-letter-draft.txt'
        text.write_text(letter, encoding='utf-8')
        files.extend([dest, text])
        data = {'draft': letter, 'template': params.get('template', 'professional')}
        warnings.append('Review this template-generated draft: inferred names, years, skills and claims may need correction.')
        if params.get('pdf'):
            pdf = dest.with_suffix('.pdf')
            data['pdf'] = export_pdf(dest, pdf, False)
            files.append(pdf)
    elif key == 'cover_inject':
        from core.cover_letter import CoverLetterInjector
        source = checked_file(params, suffix=('.docx',))
        dest = job/(source.stem+'-test.docx')
        data = CoverLetterInjector(source, dest, mode).run()
        normalize_document(dest)
        data['inspection'] = inspect_document(dest)
        files.append(dest)
    elif key == 'batch':
        folder = Path(params['folder'])
        if not folder.is_dir():
            raise ValueError('Choose an existing input folder.')
        sources = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == '.docx' and not p.name.startswith('~$'))
        if not sources:
            raise ValueError('No DOCX files found directly inside that folder.')
        rows = []
        for i, source in enumerate(sources):
            progress(f'Processing {i+1} of {len(sources)}: {source.name}')
            try:
                checked_file({'input': str(source)}, suffix=('.docx',))
                analysis = ResumeAnalyzer(source).run()
                dest = job/(source.stem+'-test.docx')
                report = inject(source, dest)
                files.append(dest)
                row = {'file': source.name, 'score': analysis['score'], 'issues': analysis['issues'], 'suggestions': ResumeImprover(analysis).generate(), 'injection': report}
                if params.get('pdf'):
                    pdf = dest.with_suffix('.pdf')
                    row['pdf'] = export_pdf(dest, pdf)
                    files.append(pdf)
                rows.append(row)
            except Exception as e:
                rows.append({'file': source.name, 'error': str(e)})
                warnings.append(source.name+': '+str(e))
        data = {'processed': len(rows), 'results': rows}
    elif key == 'diff':
        from core.diff_reporter import diff_docx
        first = checked_file(params, suffix=('.docx',))
        second = checked_file(params, 'second', ('.docx',))
        data = {'parts': diff_docx(first, second), 'text_diff': '\n'.join(difflib.unified_diff(inspect_document(first)['all_text'].splitlines(), inspect_document(second)['all_text'].splitlines(), fromfile=first.name, tofile=second.name, lineterm=''))}
    elif key in ('deep', 'font', 'style'):
        source = checked_file(params, suffix=('.docx',))
        dest = job/(source.stem+'-'+key+'.docx')
        shutil.copy2(source, dest)
        if key == 'deep':
            from core import deep_metadata
            selected = params.get('deep_channels', DEEP_CHANNELS)
            unknown = set(selected) - set(DEEP_CHANNELS)
            if unknown:
                raise ValueError('Unknown deep metadata channels: '+', '.join(sorted(unknown)))
            # ZIP comment must be last: other channels rebuild the archive.
            steps = {name: getattr(deep_metadata, 'inject_'+name)(str(dest)) for name in DEEP_CHANNELS if name in selected}
            data = {'steps': steps, 'skipped_channels': [name for name, applied in steps.items() if not applied]}
        elif key == 'font':
            from core.custom_font import embed_font_in_docx, make_font_with_injection
            embed_font_in_docx(dest)
            fontfile = job/'ScreenInject.ttf'
            fontfile.write_bytes(make_font_with_injection())
            files.append(fontfile)
            data = {'embedded': True, 'font': 'ScreenInject'}
        else:
            from core.template_library import generate_random_template_seed
            from docx import Document
            seed = generate_random_template_seed()
            font = params.get('font', 'Random')
            if font == 'Random':
                font = seed['font']
            document = Document(dest)
            for style in document.styles:
                if hasattr(style, 'font'):
                    style.font.name = font
            for paragraph in document.paragraphs:
                for run in paragraph.runs:
                    run.font.name = font
            for table in document.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            for run in p.runs:
                                run.font.name = font
            document.save(dest)
            data = {'applied_font': font, 'optional_style_seed': seed}
        data['inspection'] = inspect_document(dest)
        warnings.extend(data['inspection']['xml_parse_errors'])
        files.append(dest)
    elif key == 'lsb':
        from core.lsb_stego import encode_image, decode_image
        source = checked_file(params, suffix=('.docx', '.png', '.jpg', '.jpeg', '.webp', '.bmp'))
        if params.get('operation', 'encode') == 'decode':
            if source.suffix.lower() == '.docx':
                found = []
                with zipfile.ZipFile(source) as z:
                    for name in z.namelist():
                        if name.startswith('word/media/'):
                            try:
                                value = decode_image(z.read(name))
                                if value is not None:
                                    found.append({'part': name, 'text': value})
                            except Exception:
                                continue
                data = {'decoded': found, 'found': bool(found)}
            else:
                value = decode_image(source.read_bytes())
                data = {'decoded': value, 'found': value is not None}
        elif source.suffix.lower() == '.docx':
            dest = job/(source.stem+'-encoded.docx')
            data = encode_docx(source, dest, params.get('text', ''))
            files.append(dest)
        else:
            dest = job/(source.stem+'-encoded.png')
            dest.write_bytes(encode_image(source.read_bytes(), params.get('text', '')))
            data = {'verified_text': decode_image(dest.read_bytes()), 'format': 'PNG'}
            files.append(dest)
    elif key == 'merge':
        from docx import Document
        from docxcompose.composer import Composer
        first, second = checked_file(params, suffix=('.docx',)), checked_file(params, 'second', ('.docx',))
        master = Document(first)
        master.add_page_break()
        composer = Composer(master)
        composer.append(Document(second))
        dest = job/'merged-documents.docx'
        composer.save(str(dest))
        data = inspect_document(dest)
        files.append(dest)
    elif key == 'payloads':
        from core.payloads_i18n import get_instructions, get_soft_skills
        from core.variants import get_variant
        from core.payloads import whitespace_encode
        from core.script_obfuscation import inject_script_variant
        value = params.get('text') or get_variant(params.get('variant', 'A'))
        encoding = params.get('encoding', 'plain')
        transformed = value
        if encoding == 'base64':
            transformed = base64.b64encode(value.encode('utf-8')).decode('ascii')
        elif encoding == 'whitespace':
            transformed = whitespace_encode(value)
        elif encoding != 'plain':
            transformed = inject_script_variant(value, encoding)
        data = {'language': lang, 'instructions': get_instructions(lang), 'soft_skills': get_soft_skills(lang), 'variant': value, 'encoding': encoding, 'transformed': transformed}
        dest = job/'payload.txt'
        dest.write_text(transformed, encoding='utf-8')
        files.append(dest)
    elif key == 'notes':
        from core.portal_notes import generate_notes
        text = generate_notes(params.get('variant', 'A'), params.get('style', 'brief'))
        data = {'note': text}
        dest = job/'portal-note.txt'
        dest.write_text(text, encoding='utf-8')
        files.append(dest)
    elif key == 'ats':
        import requests
        from core.ats_fingerprint import detect_ats_from_url
        from core.ats_profiles import get_profile
        url = validate_url(params['url'])
        response = requests.get(url, timeout=20, headers={'User-Agent': 'PhantomResume-Desktop/1.0'})
        response.raise_for_status()
        detected = detect_ats_from_url(response.url)
        evidence = 'URL hostname'
        if not detected:
            from core.ats_profiles import ATS_PROFILES
            for name, profile in ATS_PROFILES.items():
                if any(alias in response.text.lower() for alias in profile.get('aliases', [])):
                    detected = name
                    evidence = 'Page markup reference (may be a third-party link)'
                    break
        data = {'ats': detected or 'unknown', 'final_url': response.url, 'evidence': evidence if detected else 'No known signature', 'profile': get_profile(detected or 'unknown'), 'profile_note': 'Unvalidated heuristic settings; not measured effectiveness.'}
    elif key == 'probe':
        progress('Loading public page in a fresh, read-only browser session')
        data = browser_inspect(params['url'], job)
        files.append(Path(data['screenshot']))
        if data['stopped']:
            warnings.append(data['message'])
    elif key == 'extraction':
        from core.ats_extraction_analyzer import analyze_extraction
        data = analyze_extraction(params['text'])
    elif key == 'tuning':
        from core.ats_tuning import ATSTuning
        weights_path = state/'ats-tuning.json'
        obj = ATSTuning(weights_path)
        if params.get('report'):
            report = json.loads(checked_file(params, 'report', ('.json',)).read_text(encoding='utf-8'))
            report = report.get('data', report)
            if not isinstance(report.get('ats_extraction_analysis'), dict) or not isinstance(report.get('log'), list):
                raise ValueError('Probe JSON must contain ats_extraction_analysis and a log list. Read-only page reports cannot update extraction weights.')
            # Publish the tuning update atomically if the worker is interrupted.
            obj.path = job/'tuning-pending.json'
            obj.update_from_probe(params['ats'], report)
            temporary = state/('ats-tuning-'+uuid.uuid4().hex+'.tmp')
            shutil.copyfile(obj.path, temporary)
            temporary.replace(weights_path)
            obj.path.unlink()
        data = {'ats': params['ats'], 'weights': obj.get(params['ats']), 'recommended_mode': obj.recommended_mode(params['ats']), 'meaning': 'Heuristic experimental settings, not validated success probabilities.'}
    elif key == 'track':
        from core.tracker import SubmissionTracker
        db = state/'outcomes.db'
        tracker = SubmissionTracker(str(db))
        operation = params.get('operation', 'view')
        if operation == 'record':
            if not params.get('company', '').strip() or not params.get('role', '').strip():
                raise ValueError('Company and role are required to record an outcome.')
            tracker.record(params['company'], params['role'], params.get('ats', 'unknown'), mode, params.get('variant', 'A'), '', '', params.get('notes', ''))
        elif operation == 'update':
            try:
                record_id = int(params.get('record_id', ''))
            except ValueError:
                raise ValueError('Enter a numeric record ID from the journal.') from None
            if record_id not in [r[0] for r in tracker.list_submissions()]:
                raise ValueError('That record ID does not exist.')
            tracker.update_status(record_id, params.get('status', 'pending'), params.get('notes', ''))
        with sqlite3.connect(db) as conn:
            conn.row_factory = sqlite3.Row
            records = [dict(row) for row in conn.execute('SELECT * FROM submissions ORDER BY id DESC')]
        data = {'records': records, 'statistics': tracker.effectiveness_report()}

    result = {'tool': tool.title, 'created': datetime.now().isoformat(timespec='seconds'), 'data': data, 'warnings': warnings, 'output_directory': str(job), 'files': [str(p) for p in files]}
    progress('Saving results and report')
    report = job/'report.html'
    report.write_text(render_report(result), encoding='utf-8')
    result['files'].extend([str(report), str(job/'result.json')])
    result_tmp = job/'result.json.tmp'
    result_tmp.write_text(serialize(result), encoding='utf-8')
    result_tmp.replace(job/'result.json')
    incomplete.unlink()
    progress('Complete' if not warnings else 'Complete with notes')
    return result


def render_report(result):
    title = html.escape(result['tool'])
    data = result['data']
    overview = ''
    if 'analysis' in data:
        analysis = data['analysis']
        overview += f'<div class="score">{analysis["score"]}<span> / 100</span></div><p>Local resume quality score</p>'
        overview += '<h2>Issues</h2><pre>'+html.escape(serialize(analysis.get('issues', [])))+'</pre>'
        overview += '<h2>Writing suggestions</h2>'
        for item in data.get('suggestions', []):
            overview += '<article><b>'+html.escape(str(item.get('type', 'Suggestion')))+'</b><p>'+html.escape(str(item.get('before', '')))+' → '+html.escape(str(item.get('after', '')))+'</p><small>'+html.escape(str(item.get('reason', '')))+'</small></article>'
    for key in ('draft', 'note', 'text_diff', 'transformed'):
        if key in data:
            overview += '<h2>'+html.escape(key.replace('_', ' ').title())+'</h2><pre>'+html.escape(str(data[key]))+'</pre>'
    warnings = ''.join('<p class="notice">'+html.escape(w)+'</p>' for w in result['warnings'])
    return '<!doctype html><html><head><meta charset="utf-8"><title>'+title+' · PhantomResume</title><style>body{font:15px/1.65 Segoe UI,sans-serif;background:#f3f5f8;color:#253044;margin:40px auto;max-width:960px;padding:24px}h1{font-size:34px;letter-spacing:-1px}h2{font-size:21px}.brand{font-size:12px;letter-spacing:2px;color:#56806e}.score{font-size:72px;font-weight:700}.score span{font-size:20px;color:#718090}article,pre{background:white;padding:20px;border-radius:12px;border:1px solid #dde3e8;white-space:pre-wrap;overflow-wrap:anywhere}.notice{background:#fff1cf;padding:16px;border-radius:10px}small{color:#647486}summary{cursor:pointer;font-size:20px;margin-top:24px}</style></head><body><p class="brand">PHANTOMRESUME / DESKTOP</p><h1>'+title+'</h1><p>'+html.escape(result['created'])+'</p>'+warnings+overview+'<details '+('open' if not overview else '')+'><summary>Complete results</summary><pre>'+html.escape(serialize(data))+'</pre></details></body></html>'
