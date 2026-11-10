"""
ats_fingerprint.py — detect which ATS a job URL uses

NOTE: effectiveness numbers in ats_profiles.py are heuristics, not measured
results. They represent expected injection success based on observed ATS
behavior patterns, but do not constitute empirical evidence.
"""


import re
import requests
from urllib.parse import urlparse

from .ats_profiles import ATS_PROFILES


def detect_ats_from_url(url):
    """Detect ATS purely from URL pattern."""
    host = urlparse(url).netloc.lower()
    for name, profile in ATS_PROFILES.items():
        if name == 'unknown':
            continue
        for alias in profile['aliases']:
            if alias in host:
                return name
    return None


def detect_ats_from_page(url, timeout=10):
    """Fetch page and look for ATS signatures in HTML/JS."""
    try:
        r = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        html = r.text.lower()
    except Exception:
        return None

    signatures = {
        'workday': ['workday', 'myworkdayjobs', 'wd1.myworkdaysite'],
        'greenhouse': ['greenhouse.io', 'boards.greenhouse', 'grnh.se'],
        'lever': ['lever.co', 'jobs.lever', 'lever-jobs'],
        'icims': ['icims.com', 'icims-'],
        'taleo': ['taleo.net', 'taleo.'],
        'workable': ['workable.com', 'workable-'],
        'smartrecruiters': ['smartrecruiters.com', 'smartrecruiters'],
        'jobvite': ['jobvite.com', 'jobvite.'],
    }
    for name, sigs in signatures.items():
        for sig in sigs:
            if sig in html:
                return name
    return None


def fingerprint(url):
    """Full fingerprint: URL → page → return ATS name."""
    ats = detect_ats_from_url(url)
    if ats:
        return ats
    ats = detect_ats_from_page(url)
    if ats:
        return ats
    return 'unknown'
