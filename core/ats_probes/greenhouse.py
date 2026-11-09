"""
greenhouse.py — probe Greenhouse ATS via the official demo board.

Test board: https://boards.greenhouse.io/greenhousetest
Safe to submit test data. Refuses non-demo URLs.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from .base import BaseATSProbe


class GreenhouseProbe(BaseATSProbe):
    name = 'greenhouse'
    is_test_portal = True   # class declares itself a demo-only probe

    def submit(self):
        result = {
            'submitted': False,
            'confirmation_text': '',
            'confirmation_email_hint': '',
            'errors': [],
            'final_url': None,
        }

        if not self.probe_only and ('greenhousetest' not in self.portal_url and 'demo' not in self.portal_url):
            result['errors'].append(
                'SAFETY: only submit to demo portals. '
                'Use https://boards.greenhouse.io/greenhousetest'
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

                # find first job link
                self._info("finding first job listing")
                job_links = page.query_selector_all('a[href*="/jobs/"]')
                if not job_links:
                    # try alternate — some demo boards redirect
                    job_links = page.query_selector_all('a')
                    job_links = [l for l in job_links if l.get_attribute('href') and '/jobs/' in (l.get_attribute('href') or '')]

                if not job_links:
                    result['errors'].append('no job listings found')
                    browser.close()
                    return result

                job_url = job_links[0].get_attribute('href')
                if job_url and not job_url.startswith('http'):
                    job_url = 'https://boards.greenhouse.io' + job_url
                self._info(f"opening job: {job_url}")
                page.goto(job_url, timeout=30000)
                page.wait_for_timeout(2000)

                # click Apply
                apply_btn = page.query_selector('a[href*="#app"]') or \
                            page.query_selector('a:has-text("Apply")')
                if apply_btn:
                    self._info("clicking Apply")
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

                # fill form
                self._info("filling form")
                for selector, value in [
                    ('input[name="first_name"]', 'Test'),
                    ('input[name="last_name"]', 'Candidate'),
                    ('input[name="email"]', 'test@example.com'),
                    ('input[name="phone"]', '+15550000000'),
                ]:
                    try:
                        el = page.query_selector(selector)
                        if el:
                            el.fill(value)
                    except Exception:
                        pass

                # upload resume
                self._info("uploading resume")
                file_input = page.query_selector('input[type="file"]')
                if not file_input:
                    result['errors'].append('no file input found')
                    browser.close()
                    return result
                file_input.set_input_files(str(self.resume_path))
                page.wait_for_timeout(3000)

                # submit
                self._info("clicking submit")
                submit_btn = page.query_selector('button[type="submit"]') or \
                             page.query_selector('button:has-text("Submit")') or \
                             page.query_selector('input[type="submit"]')
                if not submit_btn:
                    result['errors'].append('no submit button found')
                    browser.close()
                    return result
                submit_btn.click()

                self._info("waiting for confirmation")
                page.wait_for_timeout(8000)

                body_text = page.inner_text('body')
                result['confirmation_text'] = body_text[:3000]
                result['submitted'] = True
                result['confirmation_email_hint'] = 'Check test@example.com'
                result['final_url'] = page.url

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
            'note': (
                'Greenhouse does not expose parsed resume text to candidates. '
                'Full extraction requires a Greenhouse recruiter demo account.'
            ),
        }
