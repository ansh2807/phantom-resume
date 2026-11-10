"""Inspect embedded image metadata; optionally compare decoded pixels."""

import argparse
import io
import zipfile
from PIL import Image
from PIL.ExifTags import TAGS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', default=(
        'output/test-candidate-injected.docx'))
    parser.add_argument('--original', help='Original DOCX for decoded-pixel comparison')
    args = parser.parse_args()
    originals = None
    if args.original:
        with zipfile.ZipFile(args.original) as original:
            originals = {n: original.read(n) for n in original.namelist()
                         if n.startswith('word/media/')}
    image_count = 0
    with zipfile.ZipFile(args.path) as z:
        for name in z.namelist():
            if not name.startswith('word/media/'):
                continue
            print(f'\n=== {name} ===')
            try:
                with Image.open(io.BytesIO(z.read(name))) as img:
                    image_count += 1
                    img.load()
                    print(f'format: {img.format}, size: {img.size}')
                    exif = img.getexif()
                    for tag_id, value in exif.items():
                        print(f'  {TAGS.get(tag_id, tag_id)}: {str(value)[:200]}')
                    # UserComment belongs to the nested Exif IFD.
                    if 0x8769 in exif:
                        for tag_id, value in exif.get_ifd(0x8769).items():
                            print(f'  {TAGS.get(tag_id, tag_id)}: {str(value)[:200]}')
                    print(f'  info keys: {list(img.info.keys())}')
                    for key, value in img.info.items():
                        if isinstance(value, (str, bytes)):
                            print(f'  {key}: {str(value)[:200]}')
                    if originals is not None:
                        if name not in originals:
                            print('  pixel comparison: no original at this media path')
                        else:
                            with Image.open(io.BytesIO(originals[name])) as before:
                                same = (before.size == img.size and
                                        before.convert('RGBA').tobytes() ==
                                        img.convert('RGBA').tobytes())
                                print(f'  decoded pixels identical: {same}')
            except Exception as error:
                print(f'error: {error}')
    if not image_count:
        print('No readable embedded images found.')


if __name__ == '__main__':
    main()
