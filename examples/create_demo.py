"""Generate synthetic documents only; nothing is uploaded or submitted."""
from pathlib import Path
import argparse
import io

from docx import Document
from docx.shared import Inches
from PIL import Image, ImageDraw


def create_demo(output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGB', (400, 400), '#121e29')
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((45, 45, 355, 355), radius=65, fill='#92f5ce')
    draw.ellipse((132, 144, 163, 188), fill='#121e29')
    draw.ellipse((237, 144, 268, 188), fill='#121e29')
    draw.arc((135, 165, 265, 285), 15, 165, fill='#121e29', width=12)
    photo = io.BytesIO()
    image.save(photo, format='JPEG', quality=95)
    photo.seek(0)
    doc = Document()
    doc.core_properties.author = 'Test Candidate'
    doc.core_properties.last_modified_by = 'Test Candidate'
    doc.core_properties.title = 'Synthetic resume fixture'
    doc.core_properties.subject = 'Fictional content for local software tests'
    doc.add_heading('Test Candidate', 0)
    doc.add_paragraph('test@example.com | +15550000000')
    doc.add_paragraph('SYNTHETIC FIXTURE — NOT A REAL APPLICATION')
    doc.add_picture(photo, width=Inches(0.8))
    doc.add_heading('Summary', level=1)
    doc.add_paragraph('Fictional content specialist with 3 years of example experience in marketing.')
    doc.add_heading('Core Skills', level=1)
    doc.add_paragraph('Content: Editorial planning, SEO research, copywriting, accessibility, analytics')
    doc.add_heading('Experience', level=1)
    doc.add_paragraph('Content Specialist | Example Company | 2023–Present')
    doc.add_paragraph('Delivered 12 synthetic campaigns for parser testing.', style='List Bullet')
    doc.add_paragraph('Created 24 sample articles and reduced a fictional review cycle by 20%.', style='List Bullet')
    doc.add_heading('Education', level=1)
    doc.add_paragraph('Example degree | Example University | 2023')
    resume = output / 'test-candidate.docx'
    doc.save(resume)
    (output / 'job-description.txt').write_text(
        'Job title: Content Specialist\nCompany: Example Company\n'
        'SYNTHETIC JOB DESCRIPTION — NOT A LIVE VACANCY\n'
        'Write clear content, research keywords, edit articles, and measure performance.\n',
        encoding='utf-8')
    return resume


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', default='demo-output')
    args = parser.parse_args()
    print(f'Created: {create_demo(args.output_dir)}')
