"""
diff_reporter.py — show what changed between original and injected DOCX
"""

import zipfile
from pathlib import Path


def diff_docx(original_path, injected_path):
    """
    Compare two DOCX files at the zip-entry level.
    Returns dict with added/modified/removed entries and byte deltas.
    """
    with zipfile.ZipFile(original_path, 'r') as o:
        orig = {n: o.read(n) for n in o.namelist()}

    with zipfile.ZipFile(injected_path, 'r') as i:
        inj = {n: i.read(n) for n in i.namelist()}

    orig_names = set(orig.keys())
    inj_names = set(inj.keys())

    added = inj_names - orig_names
    removed = orig_names - inj_names
    common = orig_names & inj_names

    modified = []
    for n in common:
        if orig[n] != inj[n]:
            modified.append({
                'name': n,
                'old_size': len(orig[n]),
                'new_size': len(inj[n]),
                'delta': len(inj[n]) - len(orig[n]),
            })

    added_info = [{'name': n, 'size': len(inj[n])} for n in sorted(added)]
    removed_info = [{'name': n, 'size': len(orig[n])} for n in sorted(removed)]

    total_orig = sum(len(v) for v in orig.values())
    total_inj = sum(len(v) for v in inj.values())

    return {
        'original_size': total_orig,
        'injected_size': total_inj,
        'delta': total_inj - total_orig,
        'added': added_info,
        'removed': removed_info,
        'modified': modified,
    }


def print_diff(original_path, injected_path):
    d = diff_docx(original_path, injected_path)
    print(f"\n=== DIFF: {Path(original_path).name} → {Path(injected_path).name} ===")
    print(f"Total size: {d['original_size']:,} → {d['injected_size']:,} "
          f"({d['delta']:+,})")

    if d['added']:
        print(f"\nADDED ({len(d['added'])}):")
        for e in d['added']:
            print(f"  + {e['name']}  (+{e['size']:,} bytes)")

    if d['modified']:
        print(f"\nMODIFIED ({len(d['modified'])}):")
        for e in d['modified']:
            print(f"  ~ {e['name']}  {e['old_size']:,} → {e['new_size']:,} "
                  f"({e['delta']:+,})")

    if d['removed']:
        print(f"\nREMOVED ({len(d['removed'])}):")
        for e in d['removed']:
            print(f"  - {e['name']}")
