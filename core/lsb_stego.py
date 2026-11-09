"""
lsb_stego.py — encode text in image pixel LSBs

Keeps image visually identical to a human (LSB changes are imperceptible).
ATS OCR won't decode it, but sophisticated steganography detectors would.
"""

from PIL import Image
import io
from pathlib import Path


MAGIC = b'\xAA\xBB\xCC\xDD'  # start marker


def text_to_bits(text):
    data = text.encode('utf-8')
    # header: 4-byte magic + 4-byte length
    header = MAGIC + len(data).to_bytes(4, 'big')
    payload = header + data
    return ''.join(format(b, '08b') for b in payload)


def encode_image(image_bytes, text):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    pixels = img.load()
    w, h = img.size

    bits = text_to_bits(text)
    bit_idx = 0
    total_bits = len(bits)

    for y in range(h):
        for x in range(w):
            if bit_idx >= total_bits:
                break
            r, g, b = pixels[x, y]
            if bit_idx < total_bits:
                r = (r & ~1) | int(bits[bit_idx]); bit_idx += 1
            if bit_idx < total_bits:
                g = (g & ~1) | int(bits[bit_idx]); bit_idx += 1
            if bit_idx < total_bits:
                b = (b & ~1) | int(bits[bit_idx]); bit_idx += 1
            pixels[x, y] = (r, g, b)
        if bit_idx >= total_bits:
            break

    out = io.BytesIO()
    img.save(out, format='PNG')
    return out.getvalue()


def decode_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    pixels = img.load()
    w, h = img.size

    bits = []
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            bits.append(str(r & 1))
            bits.append(str(g & 1))
            bits.append(str(b & 1))

    by = bytes(int(''.join(bits[i:i+8]), 2) for i in range(0, len(bits)-7, 8))
    if by[:4] != MAGIC:
        return None
    length = int.from_bytes(by[4:8], 'big')
    if len(by) < 8 + length:
        return None
    return by[8:8+length].decode('utf-8', errors='ignore')


def stego_image_in_docx(docx_path, text):
    """Replace one image in the DOCX with its stego-encoded version."""
    import zipfile
    tmp = str(docx_path) + '.tmp'
    with zipfile.ZipFile(docx_path, 'r') as z:
        contents = {n: z.read(n) for n in z.namelist()}

    count = 0
    for name in list(contents.keys()):
        if not name.startswith('word/media/'):
            continue
        lower = name.lower()
        if not lower.endswith(('.png', '.jpg', '.jpeg')):
            continue
        try:
            stego = encode_image(contents[name], text)
            contents[name] = stego
            count += 1
        except Exception:
            continue

    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, b in contents.items():
            z.writestr(n, b)
    Path(docx_path).unlink()
    Path(tmp).rename(docx_path)
    return count
