"""Fail if tracked files include private runtime artifacts or obvious credentials."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_SUFFIXES = {'.doc', '.docx', '.pdf', '.csv', '.xlsx', '.db', '.sqlite',
                    '.sqlite3', '.exe', '.apk', '.jks', '.keystore', '.zip', '.7z', '.pem', '.key', '.log'}
BLOCKED_DIRS = {'probe_runs', 'submitted', 'submitted-screenshots', 'screenshots',
                'output', 'outputs', 'demo-output', '__pycache__', '.venv'}



def is_output_source(path):
    """Allow only the five reviewed addon files inside an output package."""
    allowed = {
        ('output', '__init__.py'), ('output', 'manifest.py'),
        ('output', 'pdf', '__init__.py'), ('output', 'pdf', 'direct.py'),
        ('output', 'pdf', 'rendered.py'),
    }
    return 'output' in path.parts and path.parts[path.parts.index('output'):] in allowed


def check():
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    failures = []
    for name in filter(None, files):
        path = Path(name)
        if (path.suffix.lower() in BLOCKED_SUFFIXES or
                (BLOCKED_DIRS.intersection(path.parts) - ({'output'} if is_output_source(path) else set())) or
                path.name in {'.env', 'ats_tuning.json'}):
            failures.append(f'{name}: private/runtime artifact')
            continue
        data = (ROOT / path).read_bytes()
        if path.suffix in {'.gif', '.png'}:
            continue
        text = data.decode('utf-8', errors='replace')
        if re.search(r'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)', text):
            failures.append(f'{name}: credential-like content')
        if re.search(r'[A-Za-z]:[\\/]' + r'Users[\\/]', text):
            failures.append(f'{name}: absolute personal Windows path')
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f'Public-file checks passed for {len(list(filter(None, files)))} tracked files.')


if __name__ == '__main__':
    check()
