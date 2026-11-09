"""
ats_probe_runner.py — orchestrate a full probe run + analysis.
"""

from pathlib import Path
import json

from .ats_probes import get_probe
from .ats_extraction_analyzer import analyze_extraction


def run_probe(ats_name, resume_path, portal_url, verbose=True, probe_only=False):
    probe_class = get_probe(ats_name)
    probe = probe_class(resume_path, portal_url, verbose=verbose)
    probe.probe_only = probe_only

    result = probe.run()

    # null-safe extraction check — extraction is None when probe errors
    extraction = result.get('extraction') or {}
    ats_extraction = extraction.get('extracted_text') or ''
    if ats_extraction:
        result['ats_extraction_analysis'] = analyze_extraction(ats_extraction)
    else:
        result['ats_extraction_analysis'] = {
            'channels_detected': [],
            'per_channel_evidence': {},
            'total_injection_chars': 0,
        }

    return result


def save_probe_run(result, output_path):
    Path(output_path).write_text(
        json.dumps(result, indent=2, default=str),
        encoding='utf-8'
    )
