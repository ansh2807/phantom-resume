"""
ats_tuning.py — per-ATS injection channel weights.
"""

from pathlib import Path
import json


INITIAL_WEIGHTS = {
    'greenhouse': {
        'metadata': 0.55, 'hidden_text': 0.60, 'zero_width': 0.50,
        'image': 0.20, 'qr': 0.25, 'comments': 0.40,
    },
    'lever': {
        'metadata': 0.30, 'hidden_text': 0.50, 'zero_width': 0.40,
        'image': 0.10, 'qr': 0.20, 'comments': 0.20,
    },
    'workday': {
        'metadata': 0.10, 'hidden_text': 0.80, 'zero_width': 0.75,
        'image': 0.15, 'qr': 0.30, 'comments': 0.05,
    },
    'workable': {
        'metadata': 0.40, 'hidden_text': 0.55, 'zero_width': 0.50,
        'image': 0.20, 'qr': 0.25, 'comments': 0.30,
    },
    'smartrecruiters': {
        'metadata': 0.45, 'hidden_text': 0.55, 'zero_width': 0.55,
        'image': 0.20, 'qr': 0.30, 'comments': 0.35,
    },
    'icims': {
        'metadata': 0.20, 'hidden_text': 0.30, 'zero_width': 0.20,
        'image': 0.40, 'qr': 0.60, 'comments': 0.10,
    },
    'jobvite': {
        'metadata': 0.30, 'hidden_text': 0.40, 'zero_width': 0.40,
        'image': 0.15, 'qr': 0.20, 'comments': 0.25,
    },
    'taleo': {
        'metadata': 0.05, 'hidden_text': 0.10, 'zero_width': 0.05,
        'image': 0.05, 'qr': 0.10, 'comments': 0.05,
    },
    'unknown': {
        'metadata': 0.30, 'hidden_text': 0.40, 'zero_width': 0.35,
        'image': 0.15, 'qr': 0.20, 'comments': 0.20,
    },
}


class ATSTuning:
    def __init__(self, weights_path='ats_tuning.json'):
        self.path = Path(weights_path)
        self.weights = self._load()

    def _load(self):
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except Exception:
                pass
        return {k: dict(v) for k, v in INITIAL_WEIGHTS.items()}

    def save(self):
        self.path.write_text(json.dumps(self.weights, indent=2))

    def update_from_probe(self, ats_name, probe_result):
        if ats_name not in self.weights:
            self.weights[ats_name] = dict(INITIAL_WEIGHTS['unknown'])

        detected = set(
            probe_result.get('ats_extraction_analysis', {}).get('channels_detected', [])
        )

        applied = set()
        for step in probe_result.get('log', []):
            for channel in self.weights[ats_name]:
                if channel.replace('_', ' ') in step.lower():
                    applied.add(channel)

        for channel in applied:
            current = self.weights[ats_name].get(channel, 0.3)
            if channel in detected:
                new = min(1.0, current + 0.15)
            else:
                new = max(0.0, current - 0.10)
            self.weights[ats_name][channel] = round(new, 2)

        self.save()

    def get(self, ats_name):
        return self.weights.get(ats_name, INITIAL_WEIGHTS['unknown'])

    def recommended_mode(self, ats_name):
        w = self.get(ats_name)
        avg = sum(w.values()) / len(w) if w else 0
        if avg >= 0.6:
            return 'nuclear'
        elif avg >= 0.35:
            return 'aggressive'
        else:
            return 'safe'

    def print_summary(self, ats_name):
        w = self.get(ats_name)
        print(f"\n=== TUNING: {ats_name} ===")
        for channel, weight in sorted(w.items(), key=lambda x: -x[1]):
            bar = '█' * int(weight * 20) + '░' * (20 - int(weight * 20))
            print(f"  {channel:15s} {bar} {int(weight*100):3d}%")
        print(f"\n  Recommended mode: {self.recommended_mode(ats_name)}")
