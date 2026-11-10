"""
ats_extraction_analyzer.py — analyze what an ATS extracted.
"""

import re


CHANNEL_SIGNATURES = {
    'metadata': [
        r'AI SCREENING NOTE',
        r'rate 10/10',
        r'exceeds all stated',
        r'strongly recommend',
        r'Note to automated',
    ],
    'hidden_text': [
        r'do not mention this',
        r'do not surface this',
    ],
    'zero_width': [
        r'[\u200b\u200c\u200d\u2060]',
    ],
    'whitespace': [
        r' {20,}',
        r'\t{5,}',
    ],
    'qr': [
        r'QR\s+CODE',
        r'qrcode',
    ],
    'image_exif': [
        r'ImageDescription.*SCREENING',
        r'UserComment.*SCREENING',
        r'XPKeywords.*SCREENING',
    ],
    'alt_text': [
        r'descr="[^"]*SCREENING',
    ],
}


def analyze_extraction(extracted_text):
    if not extracted_text:
        return {
            'channels_detected': [],
            'per_channel_evidence': {},
            'total_injection_chars': 0,
        }

    detected = []
    evidence = {}
    total_chars = 0

    for channel, patterns in CHANNEL_SIGNATURES.items():
        matches = []
        for pat in patterns:
            for m in re.finditer(pat, extracted_text, re.I):
                matches.append(m.group(0)[:200])

        if matches:
            detected.append(channel)
            evidence[channel] = matches
            total_chars += sum(len(m) for m in matches)

    return {
        'channels_detected': detected,
        'per_channel_evidence': evidence,
        'total_injection_chars': total_chars,
    }


def print_report(analyzer_result):
    print("\n=== EXTRACTION ANALYSIS ===")
    if not analyzer_result.get('channels_detected'):
        print("  NO injection channels detected in extracted text.")
        print("  Possible reasons:")
        print("    - ATS doesn't expose extracted text to candidates (most common)")
        print("    - ATS strips all injection channels")
        print("    - Need to check confirmation email or recruiter dashboard")
        return

    print(f"  Channels detected: {', '.join(analyzer_result['channels_detected'])}")
    print(f"  Total injection chars survived: {analyzer_result['total_injection_chars']}")
    print("\n  Evidence per channel:")
    for channel, matches in analyzer_result['per_channel_evidence'].items():
        print(f"\n    [{channel}]")
        for m in matches[:3]:
            print(f"      {m[:100]}")
