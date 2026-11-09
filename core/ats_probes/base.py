"""
base.py — base ATS probe
"""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseATSProbe(ABC):
    name = 'unknown'
    is_test_portal = False

    def __init__(self, resume_path, portal_url, verbose=True):
        self.resume_path = Path(resume_path)
        self.portal_url = portal_url
        self.verbose = verbose
        self.probe_only = False
        self.log = []

    def _info(self, msg):
        if self.verbose:
            print(f"[{self.name}] {msg}")
        self.log.append(msg)

    @abstractmethod
    def submit(self):
        pass

    @abstractmethod
    def check_extraction(self):
        pass

    def run(self):
        self._info(f"target: {self.portal_url}")
        self._info(f"resume: {self.resume_path}")

        if not self.resume_path.exists():
            return {'error': f'resume not found: {self.resume_path}', 'log': self.log}

        submit_result = self.submit()
        if submit_result.get('errors'):
            return {
                'name': self.name,
                'submit': submit_result,
                'extraction': None,
                'error': submit_result['errors'][0],
                'log': self.log,
            }

        extraction_result = self.check_extraction()

        return {
            'name': self.name,
            'submit': submit_result,
            'extraction': extraction_result,
            'log': self.log,
        }
