"""Offline regression tests with generated fixtures and mocked browser adapters."""
from contextlib import redirect_stdout
from pathlib import Path
import importlib
import io
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET
import zipfile

from docx import Document
from PIL import Image
from PyPDF2 import PdfReader

from examples.create_demo import create_demo
from core.resume_analyzer import ResumeAnalyzer
from core.resume_injector import ResumeInjector
from core.cover_generator import generate_cover_letter
from core.deep_metadata import run_all, INSTRUCTION
from core.diff_reporter import diff_docx
from core.pdf_exporter import PDFExporter
from core.payloads_i18n import get_combined_instructions
from core.lsb_stego import encode_image, decode_image
from core.ats_probe_runner import run_probe
from core.ats_probes.greenhouse import GreenhouseProbe
from core.ats_probes.lever import LeverProbe

ROOT = Path(__file__).resolve().parents[1]


class DocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.resume = create_demo(self.folder)

    def test_analysis_and_cover_use_synthetic_content(self):
        analysis = ResumeAnalyzer(self.resume).run()
        self.assertGreaterEqual(analysis['score'], 0)
        self.assertLessEqual(analysis['score'], 100)
        letter = generate_cover_letter(analysis, (self.folder / 'job-description.txt').read_text())
        self.assertIn('Example Company', letter)
        import re
        skills = re.search(r'background in (.+?) aligns', letter).group(1)
        self.assertIn('Editorial planning', skills)
        self.assertNotIn('@', skills)
        self.assertNotIn('Content:', skills)

    def test_metadata_only_plan_preserves_other_parts(self):
        output = self.folder / 'metadata.docx'
        job = ResumeInjector(self.resume, output, mode='nuclear')
        job.channel_plan = ['metadata']
        job.run()
        with zipfile.ZipFile(self.resume) as a, zipfile.ZipFile(output) as b:
            changed = [n for n in a.namelist() if a.read(n) != b.read(n)]
        self.assertEqual(changed, ['docProps/core.xml'])

    def test_empty_plan_preserves_contents(self):
        output = self.folder / 'empty.docx'
        job = ResumeInjector(self.resume, output, mode='nuclear')
        job.channel_plan = []
        self.assertEqual(job.run()['steps'], [])
        self.assertEqual(self.resume.read_bytes(), output.read_bytes())

    def test_i18n_subject_round_trip(self):
        output = self.folder / 'translated.docx'
        ResumeInjector(self.resume, output, lang='hi').run()
        with zipfile.ZipFile(output) as z:
            core = ET.fromstring(z.read('docProps/core.xml'))
        self.assertEqual(core.find('{http://purl.org/dc/elements/1.1/}subject').text,
                         get_combined_instructions('hi')[0])

    def test_aggressive_output_and_diff(self):
        output = self.folder / 'aggressive.docx'
        ResumeInjector(self.resume, output, mode='aggressive').run()
        Document(output)
        change = diff_docx(self.resume, output)
        self.assertTrue(any('qr_' in item['name'] for item in change['added']))
        with zipfile.ZipFile(output) as z:
            for name in z.namelist():
                if name.endswith(('.xml', '.rels')):
                    ET.fromstring(z.read(name))

    def test_full_legacy_verifier_on_photo_fixture(self):
        output = self.folder / 'injected.docx'
        ResumeInjector(self.resume, output, mode='aggressive').run()
        result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'test_all_injections.py'), str(output)],
                                cwd=self.folder, capture_output=True, text=True,
                                encoding='utf-8', timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('0 failed', result.stdout)
        self.assertIn('JPEG EXIF injected', result.stdout)
        self.assertIn('QR code decodes', result.stdout)

    def test_reportlab_counts_and_image_objects(self):
        output = self.folder / 'test.pdf'
        with patch('core.pdf_exporter.HAS_DOCX2PDF', False), redirect_stdout(io.StringIO()):
            result = PDFExporter(self.resume, output).run()
        self.assertGreater(result['paragraphs'], 0)
        self.assertEqual(result['images'], 1)
        self.assertEqual(result['size'], output.stat().st_size)
        reader = PdfReader(output)
        count = 0
        for page in reader.pages:
            objects = page.get('/Resources', {}).get('/XObject', {})
            if hasattr(objects, 'get_object'):
                objects = objects.get_object()
            count += sum(ref.get_object().get('/Subtype') == '/Image' for ref in objects.values())
        self.assertEqual(count, 1)

    def test_deep_metadata_keeps_zip_comment(self):
        result = run_all(str(self.resume))
        self.assertTrue(result['zip_comment'])
        with zipfile.ZipFile(self.resume) as z:
            self.assertEqual(z.comment.decode('utf-8'), INSTRUCTION)
            self.assertIn('docProps/custom.xml', z.namelist())

    def test_lsb_round_trip_with_capacity(self):
        buffer = io.BytesIO()
        Image.new('RGB', (100, 100), 'white').save(buffer, format='PNG')
        self.assertEqual(decode_image(encode_image(buffer.getvalue(), 'synthetic payload')), 'synthetic payload')


class ProbeTests(unittest.TestCase):
    def test_null_extraction_preserves_failure(self):
        for extraction in [None, {}]:
            fake = MagicMock()
            fake.run.return_value = {'error': 'no job listings found', 'extraction': extraction}
            with patch('core.ats_probe_runner.get_probe', return_value=lambda *a, **k: fake):
                result = run_probe('greenhouse', 'unused', 'unused', probe_only=True)
            self.assertEqual(result['error'], 'no job listings found')
            self.assertEqual(result['ats_extraction_analysis']['channels_detected'], [])

    def test_probe_only_returns_before_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            resume = Path(folder) / 'fixture.docx'
            resume.write_bytes(b'never uploaded')
            for name, cls in [('greenhouse', GreenhouseProbe), ('lever', LeverProbe)]:
                with self.subTest(provider=name):
                    url = 'https://example.com/authorized-board'
                    page = MagicMock()
                    page.url = url
                    link = MagicMock()
                    link.get_attribute.return_value = url + '/position'
                    page.query_selector_all.return_value = [link]
                    form, file_input = MagicMock(), MagicMock()
                    page.query_selector.side_effect = lambda s: form if s == 'form' else file_input if s == 'input[type="file"]' else None
                    browser = MagicMock()
                    browser.new_page.return_value = page
                    context = MagicMock()
                    context.__enter__.return_value.chromium.launch.return_value = browser
                    with patch(f'core.ats_probes.{name}.sync_playwright', return_value=context):
                        probe = cls(resume, url, verbose=False)
                        probe.probe_only = True
                        result = probe.run()
                    self.assertNotIn('error', result)
                    self.assertTrue(result['submit']['file_input_found'])
                    self.assertFalse(result['submit']['submitted'])
                    file_input.set_input_files.assert_not_called()
                    form.fill.assert_not_called()
                    form.click.assert_not_called()
                    self.assertFalse(any('input[name=' in call.args[0] or 'type="submit"' in call.args[0] for call in page.query_selector.call_args_list))

    def test_non_demo_non_inspection_path_rejects_before_browser(self):
        for name, cls in [('greenhouse', GreenhouseProbe), ('lever', LeverProbe)]:
            with self.subTest(provider=name), patch(f'core.ats_probes.{name}.sync_playwright') as browser:
                result = cls('unused', 'https://example.com/production', verbose=False).submit()
                self.assertTrue(result['errors'])
                browser.assert_not_called()


if __name__ == '__main__':
    unittest.main()
