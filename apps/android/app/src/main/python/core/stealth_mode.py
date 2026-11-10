"""
stealth_mode.py — randomized injection per submission

Same input → different output every time.
"""
import random
import hashlib
from pathlib import Path


def randomize_injection_plan(mode='aggressive', lang='en'):
    """
    Given a mode, return a randomized subset of channels to apply.
    """
    channels = {
        'safe': [
            'metadata',
        ],
        'aggressive': [
            'metadata', 'hidden_text', 'comments', 'zero_width',
            'image', 'qr',
        ],
        'nuclear': [
            'metadata', 'hidden_text', 'comments', 'zero_width',
            'headers_footers', 'fields', 'split_payload', 'base64',
            'acrostic', 'fake_recruiter', 'whitespace',
            'image', 'audio', 'qr', 'font',
        ],
    }

    pool = channels.get(mode, channels['aggressive'])

    if mode == 'safe':
        # safe = always full safe pool
        chosen = pool[:]
    elif mode == 'aggressive':
        # aggressive = random 60-100% of pool, always includes metadata + zero_width
        must_have = ['metadata', 'zero_width']
        others = [c for c in pool if c not in must_have]
        random.shuffle(others)
        n = random.randint(len(others) // 2, len(others))
        chosen = must_have + others[:n]
    else:  # nuclear
        # nuclear = random 70-100% of pool
        must_have = ['metadata', 'hidden_text', 'zero_width']
        others = [c for c in pool if c not in must_have]
        random.shuffle(others)
        n = random.randint(len(others) * 7 // 10, len(others))
        chosen = must_have + others[:n]

    return sorted(chosen)


def randomize_instruction_variant():
    """Return a random instruction variant index."""
    return random.randint(0, 3)


def randomize_padding(target_size_range=(0, 4096)):
    """Return random bytes to add to zip entries."""
    n = random.randint(*target_size_range)
    return bytes(random.getrandbits(8) for _ in range(n))


def compute_file_fingerprint(path):
    """SHA-256 of a file — used to verify randomness across runs."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()
