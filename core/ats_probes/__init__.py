"""
ats_probes — ATS-specific automation probes.

SAFETY: all probes refuse to run against non-demo URLs.
"""

from .greenhouse import GreenhouseProbe
from .lever import LeverProbe

PROBES = {
    'greenhouse': GreenhouseProbe,
    'lever': LeverProbe,
}


def get_probe(name):
    if name not in PROBES:
        raise ValueError(f"unknown probe: {name}. available: {list(PROBES.keys())}")
    return PROBES[name]
