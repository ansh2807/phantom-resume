# Build with: python -m PyInstaller --noconfirm PhantomResume.spec
from pathlib import Path
import os
import sys
import zipfile
from PyInstaller.config import CONF
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules, copy_metadata
from playwright.sync_api import sync_playwright

root = Path(SPECPATH)
# Keep unrelated application runtimes on the host PATH out of the distribution.
os.environ['PATH'] = os.pathsep.join([str(Path(sys.executable).parent), str(Path(os.environ['WINDIR'])/'System32'), os.environ['WINDIR']])
with sync_playwright() as pw:
    browser = Path(os.environ.get('PHANTOM_BROWSER_DIR', str(Path(pw.chromium.executable_path).parent)))
if not any((browser / name).exists() for name in ('chrome.exe','chrome-headless-shell.exe')):
    raise RuntimeError('Install Chromium first: python -m playwright install chromium')
browser_archive = Path(CONF['workpath'])/'browser-bundle.zip'
browser_archive.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(browser_archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for item in browser.rglob('*'):
        if item.is_file():
            archive.write(item, item.relative_to(browser))
datas = [(str(root/'assets'), 'assets'), (str(root/'LICENSE'), '.'), (str(root/'THIRD_PARTY_NOTICES.txt'), '.'), (str(root/'licenses'), 'licenses'), (str(browser_archive), '.')]
for package in ('docx', 'docxcompose', 'reportlab', 'playwright', 'pyzbar'):
    datas += collect_data_files(package)
for package in ('python-docx', 'docxcompose', 'babel', 'playwright', 'pyzbar'):
    datas += copy_metadata(package)
hidden = collect_submodules('core') + collect_submodules('desktop') + collect_submodules('fontTools.ttLib.tables')
hidden += sum((collect_submodules(p) for p in ('payload','channel','output','persistence','intelligence','orchestration')), []) + ['api', 'addon_cli']
datas += [(str(root/'persistence'/'migrations'), 'persistence/migrations'), (str(root/'persistence'/'ats_profiles'), 'persistence/ats_profiles')]
hidden += ['examples.create_demo', 'PySide6.QtTest', 'PIL.ImageQt', 'mutagen.id3', 'mutagen.mp4', 'mutagen.flac', 'mutagen.oggvorbis']
a = Analysis([str(root/'app.py')], pathex=[str(root)], binaries=collect_dynamic_libs('pyzbar'), datas=datas,
    hiddenimports=hidden, hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'torch', 'pandas', 'numpy', 'IPython', 'jupyter', 'tkinter',
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick',
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets'],
    noarchive=False)
# Analyze Python sources first so all dependencies remain discoverable, then
# replace our application core bytecode with optional Cython native extensions.
native_root = Path(os.environ['PHANTOM_NATIVE_MODULES']) if os.environ.get('PHANTOM_NATIVE_MODULES') else None
if native_root:
    native_files = list(native_root.rglob('*.pyd'))
    if len(native_files) < 35:
        raise RuntimeError('Native hardening requested but compiled modules are incomplete.')
    native_names = {'.'.join(p.relative_to(native_root).parent.parts + (p.name.split('.')[0],)) for p in native_files}
    a.pure = [entry for entry in a.pure if entry[0] not in native_names]
    for p in native_files:
        a.binaries.append((str(p.relative_to(native_root)), str(p), 'EXTENSION'))
import PySide6
qt_dir = Path(PySide6.__file__).parent
# Qt requires a newer VC runtime than the one bundled with Python 3.12.5.
# Use one consistent, backward-compatible runtime at the executable root.
a.binaries = [entry for entry in a.binaries if not Path(entry[0]).name.lower().startswith('api-ms-win-') and Path(entry[0]).name.lower() != 'ucrtbase.dll']
for filename in ('vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll', 'msvcp140_codecvt_ids.dll', 'concrt140.dll'):
    a.binaries = [(dest, str(qt_dir/filename), kind) if Path(dest).name.lower() == filename else (dest, src, kind) for dest, src, kind in a.binaries]
    a.binaries = [entry for entry in a.binaries if entry[0].lower() != filename]
    a.binaries.append((filename, str(qt_dir/filename), 'BINARY'))
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='PhantomResume Desktop', debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False, console=False,
    disable_windowed_traceback=False, icon=str(root/'assets'/'phantom.ico'))
