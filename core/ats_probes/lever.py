"""
lever.py — probe Lever ATS via demo board.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from .base import BaseATSProbe


class LeverProbe(BaseATSProbe):
    name = 'lever'
    is_test_portal = True   # class declares itself a demo-only probe

    def submit(self):
        result = {
            'submitted': False,
            'confirmation_text': '',
            'confirmation_email_hint': '',
            'errors': [],
            'final_url': None,
        }

        if not self.probe_only and ('leverdemo' not in self.portal_url and 'demo' not in self.portal_url):
            result['errors'].append(
                'SAFETY: only submit to demo portals. '
                'Use https://jobs.lever.co/leverdemo'
            )
            return result

        self.is_test_portal = True

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                self._info(f"opening {self.portal_url}")
                page.goto(self.portal_url, timeout=30000)
                page.wait_for_timeout(2000)

                job_links = page.query_selector_all('a.posting-title, a[href*="/"]')
                job_links = [l for l in job_links if '/jobs/' not in (l.get_attribute('href') or '')]

                if not job_links:
                    result['errors'].append('no job listings found')
                    browser.close()
                    return result

                job_url = job_links[0].get_attribute('href')
                if job_url and not job_url.startswith('http'):
                    job_url = 'https://jobs.lever.co' + job_url
                self._info(f"opening job: {job_url}")
                page.goto(job_url, timeout=30000)
                page.wait_for_timeout(2000)

                apply_btn = page.query_selector('a:has-text("Apply")')
                if apply_btn:
                    apply_btn.click()
                    page.wait_for_timeout(3000)

                # Probe-only inspects controls without filling fields or uploading files.
                if self.probe_only:
                    self._info("PROBE-ONLY: locating form and file input")
                    form = page.query_selector('form')
                    file_input = page.query_selector('input[type="file"]')
                    result['submitted'] = False
                    result['note'] = 'PROBE ONLY — no fields filled, no files uploaded, no submission'
                    result['form_found'] = form is not None
                    result['file_input_found'] = file_input is not None
                    result['final_url'] = page.url
                    if form is None:
                        result['errors'].append('no form found')
                    if file_input is None:
                        result['errors'].append('no file input found')
                    self._info("PROBE-ONLY: stopping before form filling, upload, and submit")
                    browser.close()
                    return result

                self._info("filling form")
                for selector, value in [
                    ('input[name="name"]', 'Test Candidate'),
                    ('input[name="email"]', 'test@example.com'),
                    ('input[name="phone"]', '+15550000000'),
                    ('input[name="org"]', 'TestCorp'),
                ]:
                    try:
                        el = page.query_selector(selector)
                        if el:
                            el.fill(value)
                    except Exception:
                        pass

                self._info("uploading resume")
                file_input = page.query_selector('input[type="file"]')
                if not file_input:
                    result['errors'].append('no file input')
                    browser.close()
                    return result
                file_input.set_input_files(str(self.resume_path))
                page.wait_for_timeout(3000)

                self._info("submitting")
                submit_btn = page.query_selector('button[type="submit"]') or \
                             page.query_selector('button:has-text("Submit")')
                if submit_btn:
                    submit_btn.click()
                    page.wait_for_timeout(8000)
                    body_text = page.inner_text('body')
                    result['confirmation_text'] = body_text[:3000]
                    result['submitted'] = True
                    result['final_url'] = page.url
                    result['confirmation_email_hint'] = 'Check test@example.com'

                browser.close()

        except PWTimeout as e:
            result['errors'].append(f'timeout: {e}')
        except Exception as e:
            result['errors'].append(f'playwright error: {e}')

        return result

    def check_extraction(self):
        return {
            'extracted_text': None,
            'detected_channels': [],
            'note': 'Lever does not expose parsed text to candidates.',
        }
