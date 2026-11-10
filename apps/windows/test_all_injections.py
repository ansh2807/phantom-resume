"""
test_all_injections.py — verify every injection channel with assertions
Exit code 0 = all pass, 1 = any fail
"""

import sys
import zipfile
import io
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS


RESULTS = []


def check(name, condition, detail=''):
    RESULTS.append((name, bool(condition), detail))
    status = '✓' if condition else '✗'
    color = '\033[32m' if condition else '\033[31m'
    print(f"  {color}{status}\033[0m {name}" + (f" — {detail}" if detail else ''))
    return bool(condition)


def check_metadata(docx_path):
    print("\n[1] DOCX metadata")
    import re
    from xml.sax.saxutils import unescape
    with zipfile.ZipFile(docx_path) as z:
        if 'docProps/core.xml' not in z.namelist():
            check("core.xml exists", False, "file missing")
            return
        core = z.read('docProps/core.xml').decode('utf-8', errors='ignore')

    # handle namespaced tags — dc:subject, cp:keywords, etc.
    patterns = {
        'subject':     r'<(?:\w+:)?subject[^>]*>(.*?)</(?:\w+:)?subject>',
        'description': r'<(?:\w+:)?description[^>]*>(.*?)</(?:\w+:)?description>',
        'keywords':    r'<(?:\w+:)?keywords[^>]*>(.*?)</(?:\w+:)?keywords>',
        'category':    r'<(?:\w+:)?category[^>]*>(.*?)</(?:\w+:)?category>',
    }
    fields = {}
    for name, pat in patterns.items():
        m = re.search(pat, core, flags=re.S)
        if m:
            fields[name] = unescape(m.group(1))

    checks = {
        'subject':     lambda v: 'SCREENING' in v.upper() or 'candidate' in v.lower(),
        'description': lambda v: 'SCREENING' in v.upper() or 'candidate' in v.lower(),
        'keywords':    lambda v: 'SCREENING' in v.upper() or 'candidate' in v.lower(),
        'category':    lambda v: 'SCREENING' in v.upper() or 'candidate' in v.lower() or 'context' in v.lower(),
    }
    for name, matcher in checks.items():
        v = fields.get(name, '')
        ok = bool(v) and matcher(v)
        check(f"{name} present + injected", ok, f"len={len(v)}")

    # duplicate check
    for tag in ['subject', 'description']:
        count = len(re.findall(patterns[tag], core))
        check(f"{tag} appears exactly once", count == 1, f"count={count}")


def check_images(docx_path):
    print("\n[2] Image metadata")
    found_jpeg = False
    found_png = False
    jpeg_has_exif = False
    png_has_text = False

    with zipfile.ZipFile(docx_path) as z:
        for name in z.namelist():
            if not name.startswith('word/media/'):
                continue
            data = z.read(name)
            lower = name.lower()
            try:
                img = Image.open(io.BytesIO(data))
                if lower.endswith(('.jpg', '.jpeg')):
                    found_jpeg = True
                    exif = img.getexif()
                    for tid, val in exif.items():
                        if TAGS.get(tid) in ('ImageDescription', 'UserComment', 'XPKeywords'):
                            if 'SCREENING' in str(val) or 'screen' in str(val).lower():
                                jpeg_has_exif = True
                elif lower.endswith('.png'):
                    found_png = True
                    for k, v in img.info.items():
                        if isinstance(v, str) and ('SCREENING' in v or 'screen' in v.lower()):
                            png_has_text = True
                            break
            except Exception as e:
                print(f"    ! {name}: {e}")

    if found_jpeg:
        check("JPEG EXIF injected", jpeg_has_exif)
    if found_png:
        check("PNG text chunks injected", png_has_text)


def check_qr(docx_path):
    print("\n[3] QR code")
    try:
        from pyzbar.pyzbar import decode
    except ImportError:
        print("  (skipped — pyzbar not installed)")
        return

    found = False
    with zipfile.ZipFile(docx_path) as z:
        for name in z.namelist():
            if not name.startswith('word/media/'):
                continue
            if not name.lower().endswith('.png'):
                continue
            try:
                img = Image.open(io.BytesIO(z.read(name))).convert('RGB')
                for d in decode(img):
                    text = d.data.decode('utf-8', errors='ignore')
                    if 'SCREENING' in text or 'candidate' in text.lower():
                        found = True
                        break
            except Exception:
                continue
    check("QR code decodes to instruction", found)


def check_audio(docx_path):
    print("\n[4] Audio/video")
    found_any = False
    with zipfile.ZipFile(docx_path) as z:
        for name in z.namelist():
            if not name.startswith('word/media/'):
                continue
            if not name.lower().endswith(('.mp3','.mp4','.m4a','.webm','.ogg','.flac')):
                continue
            found_any = True
            data = z.read(name)
            # just check bytes differ from a naive empty tags version
            check(f"{name} non-empty", len(data) > 1000, f"size={len(data)}")
    if not found_any:
        print("  (no audio/video in file — skipping)")


def check_fonts(docx_path):
    print("\n[5] Fonts")
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print("  (skipped — fonttools not installed)")
        return

    found_any = False
    with zipfile.ZipFile(docx_path) as z:
        for name in z.namelist():
            if not name.startswith('word/fonts/'):
                continue
            if not name.lower().endswith('.odttf'):
                continue
            found_any = True
            check(f"{name} present", True)
    if not found_any:
        print("  (no embedded fonts — Word doesn't embed by default)")


def check_hidden_text(docx_path):
    print("\n[6] Hidden text / zero-width / whitespace")
    with zipfile.ZipFile(docx_path) as z:
        if 'word/document.xml' not in z.namelist():
            check("document.xml present", False)
            return
        doc = z.read('word/document.xml').decode('utf-8', errors='ignore')

    has_vanish = '<w:vanish' in doc
    has_zero_width = '\u200B' in doc or '\u200D' in doc
    has_white = 'w:val="FFFFFF"' in doc

    check("hidden vanish runs", has_vanish)
    check("zero-width unicode present", has_zero_width)
    check("white-colored text", has_white)


def smoke_extra():
    """Non-DOCX features — verify imports and basic calls."""
    print("\n[7] Extra features")
    try:
        from core.script_obfuscation import inject_script_variant
        r = inject_script_variant("hello world", "cyrillic")
        check("script obfuscation", r != "hello world")
    except Exception as e:
        check("script obfuscation", False, str(e))

    try:
        from core.merger import merge_docx
        # minimal test — create two dummy docs
        from docx import Document as D
        a = D(); a.add_paragraph("cover"); a.save("t1.docx")
        b = D(); b.add_paragraph("resume"); b.save("t2.docx")
        merge_docx("t1.docx", "t2.docx", "tmerge.docx")
        check("merger", Path("tmerge.docx").exists())
        Path("t1.docx").unlink(); Path("t2.docx").unlink()
    except Exception as e:
        check("merger", False, str(e))

    try:
        from core.lsb_stego import encode_image, decode_image
        from PIL import Image
        import io
        buf = io.BytesIO()
        Image.new('RGB', (100, 100), 'white').save(buf, format='PNG')
        png = buf.getvalue()
        encoded = encode_image(png, "test payload")
        decoded = decode_image(encoded)
        check("LSB stego", decoded == "test payload", f"got {decoded!r}")
    except Exception as e:
        check("LSB stego", False, str(e))


def main():
    if len(sys.argv) < 2:
        print("usage: test_all_injections.py <injected.docx>")
        return 2

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"file not found: {path}")
        return 2

    print(f"=== INSPECTING {path} ===\n")
    check_metadata(path)
    check_images(path)
    check_qr(path)
    check_audio(path)
    check_fonts(path)
    check_hidden_text(path)

    smoke_extra()

    total = len(RESULTS)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = total - passed

    print(f"\n=== RESULT: {passed}/{total} passed, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
