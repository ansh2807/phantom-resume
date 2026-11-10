"""
ats_profiles.py — known ATS behavior + per-ATS injection effectiveness
"""

ATS_PROFILES = {
    'workday': {
        'aliases': ['myworkdayjobs.com', 'workday.com', 'wd1.myworkdaysite.com'],
        'behavior': {
            'metadata_effective': 0.10,   # Workday strips docProps
            'hidden_text_effective': 0.80, # reads body text
            'zero_width_effective': 0.75,
            'image_effective': 0.15,
            'qr_effective': 0.30,
            'comments_effective': 0.05,
        },
        'llm_based': True,
        'recommended_mode': 'aggressive',
        'priority_channels': ['hidden_text', 'zero_width'],
    },
    'greenhouse': {
        'aliases': ['greenhouse.io', 'boards.greenhouse.io'],
        'behavior': {
            'metadata_effective': 0.55,
            'hidden_text_effective': 0.60,
            'zero_width_effective': 0.50,
            'image_effective': 0.20,
            'qr_effective': 0.25,
            'comments_effective': 0.40,
        },
        'llm_based': True,
        'recommended_mode': 'nuclear',
        'priority_channels': ['metadata', 'hidden_text', 'split_payload'],
    },
    'lever': {
        'aliases': ['lever.co', 'jobs.lever.co'],
        'behavior': {
            'metadata_effective': 0.30,
            'hidden_text_effective': 0.50,
            'zero_width_effective': 0.40,
            'image_effective': 0.10,
            'qr_effective': 0.20,
            'comments_effective': 0.20,
        },
        'llm_based': True,
        'recommended_mode': 'aggressive',
        'priority_channels': ['hidden_text', 'zero_width'],
    },
    'icims': {
        'aliases': ['icims.com'],
        'behavior': {
            'metadata_effective': 0.20,
            'hidden_text_effective': 0.30,
            'zero_width_effective': 0.20,
            'image_effective': 0.40,
            'qr_effective': 0.60,   # OCR-based
            'comments_effective': 0.10,
        },
        'llm_based': False,
        'recommended_mode': 'nuclear',
        'priority_channels': ['qr'],
    },
    'taleo': {
        'aliases': ['taleo.net'],
        'behavior': {
            'metadata_effective': 0.05,
            'hidden_text_effective': 0.10,
            'zero_width_effective': 0.05,
            'image_effective': 0.05,
            'qr_effective': 0.10,
            'comments_effective': 0.05,
        },
        'llm_based': False,
        'recommended_mode': 'safe',   # don't waste time
        'priority_channels': [],
    },
    'workable': {
        'aliases': ['workable.com'],
        'behavior': {
            'metadata_effective': 0.40,
            'hidden_text_effective': 0.55,
            'zero_width_effective': 0.50,
            'image_effective': 0.20,
            'qr_effective': 0.25,
            'comments_effective': 0.30,
        },
        'llm_based': True,
        'recommended_mode': 'aggressive',
        'priority_channels': ['metadata', 'hidden_text'],
    },
    'smartrecruiters': {
        'aliases': ['smartrecruiters.com'],
        'behavior': {
            'metadata_effective': 0.45,
            'hidden_text_effective': 0.55,
            'zero_width_effective': 0.55,
            'image_effective': 0.20,
            'qr_effective': 0.30,
            'comments_effective': 0.35,
        },
        'llm_based': True,
        'recommended_mode': 'nuclear',
        'priority_channels': ['metadata', 'hidden_text', 'split_payload'],
    },
    'jobvite': {
        'aliases': ['jobvite.com'],
        'behavior': {
            'metadata_effective': 0.30,
            'hidden_text_effective': 0.40,
            'zero_width_effective': 0.40,
            'image_effective': 0.15,
            'qr_effective': 0.20,
            'comments_effective': 0.25,
        },
        'llm_based': True,
        'recommended_mode': 'aggressive',
        'priority_channels': ['metadata', 'hidden_text'],
    },
    'unknown': {
        'aliases': [],
        'behavior': {
            'metadata_effective': 0.30,
            'hidden_text_effective': 0.40,
            'zero_width_effective': 0.35,
            'image_effective': 0.15,
            'qr_effective': 0.20,
            'comments_effective': 0.20,
        },
        'llm_based': True,
        'recommended_mode': 'aggressive',
        'priority_channels': ['metadata', 'hidden_text'],
    },
}


def get_profile(ats_name):
    return ATS_PROFILES.get(ats_name.lower(), ATS_PROFILES['unknown'])


def get_effectiveness(ats_name):
    p = get_profile(ats_name)
    return p['behavior']
