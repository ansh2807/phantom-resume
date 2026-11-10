"""Shutdown acceptance using only owned fixture processes and localhost."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def run(target, test, check):
    import psutil
    import win32gui
    import win32con
    from PySide6.QtWidgets import QApplication
    from PySide6.QtTest import QTest
    from .window import Window
    from .jobs import Worker, compact_preview
    from .engine import checked_file
    from examples.create_demo import create_demo
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    source = create_demo(target/'fixtures')

    def wait_until(predicate, seconds=12):
        deadline = time.monotonic()+seconds
        while time.monotonic() < deadline:
            if predicate():
                return True
            QTest.qWait(50)
        return bool(predicate())

    def repeat_jobs():
        window = Window()
        window.output = str(target/'repeat')
        window.show()
        initial_children = {p.pid for p in psutil.Process().children(recursive=True)}
        for key in ['review', 'inspect', 'full', 'pdf']:
            window.select_tool(key)
            window.set_input(source)
            window.start_job()
            worker = window.worker
            check(wait_until(lambda: not worker.isRunning(), 40), 'Worker did not finish')
            check(key in window.results, 'Worker failed: '+window.overview.toPlainText())
            check(worker.lease is None and worker.temp_dir is None, 'Worker resources were retained')
            check(len(window.results) <= 3, 'Preview cache grew past limit')
        check(wait_until(lambda: not ({p.pid for p in psutil.Process().children(recursive=True)}-initial_children)), 'Completed jobs left child processes')
        QTest.qWait(2300)
        check(not window.orbit.timer.isActive(), 'Idle animation is still waking CPU')
        window.select_tool('payloads')
        window.showMinimized()
        QTest.qWait(150)
        check(not window.orbit.timer.isActive(), 'Minimized animation still running')
        window.close()
    test('Repeated isolated runs release workers; cache is bounded; idle timers stop', repeat_jobs)
    test('Preview caps large strings and lists', lambda: check(len(json.dumps(compact_preview({'items':['x'*100000]*1000}))) < 300000, 'Preview exceeds budget'))

    def archive_limits():
        import zipfile
        p = target/'too-many-parts.docx'
        with zipfile.ZipFile(p, 'w', zipfile.ZIP_DEFLATED) as z:
            for i in range(5001):
                z.writestr(str(i), '')
        try:
            checked_file({'input':str(p)}, suffix=('.docx',))
        except ValueError:
            return
        raise AssertionError('Oversized document archive accepted')
    test('Oversized document archive rejected before processing', archive_limits)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            time.sleep(20)
            try:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'<title>Local delayed test</title>')
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/slow'

    def cancel_browser():
        worker = Worker('probe', {'url':url, 'output':str(target/'cancel')})
        worker.start()
        check(wait_until(lambda: worker.process.processId() != 0), 'Worker failed to start')
        pid = int(worker.process.processId())
        def owned():
            try:
                return [psutil.Process(pid)]+psutil.Process(pid).children(recursive=True)
            except psutil.NoSuchProcess:
                return []
        check(wait_until(lambda: any('chrome' in p.name().lower() for p in owned()), 120), 'Browser did not start')
        children = owned()
        worker.cancel()
        check(wait_until(lambda: not worker.isRunning()), 'Cancellation did not finish')
        check(wait_until(lambda: not any(p.is_running() for p in children)), 'Cancel left an owned browser/worker alive')
        check((worker.job_directory/'INCOMPLETE.txt').is_file(), 'Cancelled run is not marked incomplete')
    test('Cancel kills owned browser tree and marks partial output', cancel_browser)

    def external_fixture(kind):
        directory = target/kind
        directory.mkdir()
        ready = directory/'ready.json'
        config = directory/'config.json'
        config.write_text(json.dumps({'ready':str(ready.resolve()), 'output':str((directory/'exports').resolve()), 'url':url if kind != 'idle' else ''}), encoding='utf-8')
        args = [sys.executable]
        if not getattr(sys, 'frozen', False):
            args.append(str(Path(__file__).resolve().parents[1]/'app.py'))
        args.extend(['--lifecycle-fixture', str(config.resolve())])
        proc = subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW)
        owned = []
        try:
            check(wait_until(ready.exists, 35), 'Fixture UI did not start')
            info = json.loads(ready.read_text())
            ui = psutil.Process(info['pid'])
            if kind != 'idle':
                check(wait_until(lambda: any('chrome' in p.name().lower() for p in ui.children(recursive=True)), 120), 'Owned browser never started')
            owned = [ui]+ui.children(recursive=True)
            if kind == 'idle':
                QTest.qWait(2500)
                t0 = time.monotonic()
                cpu0 = sum(sum(p.cpu_times()[:2]) for p in owned)
                QTest.qWait(3000)
                elapsed = time.monotonic()-t0
                rss = sum(p.memory_info().rss for p in owned)
                cpu = (sum(sum(p.cpu_times()[:2]) for p in owned)-cpu0)/elapsed*100
                metrics = {'version':'1.3.0','sample_seconds':round(elapsed,2),'rss_mb':round(rss/1024**2,1),'cpu_one_core_percent':round(cpu,2),'child_processes':len(owned)-1, 'process_names':[p.name() for p in owned]}
                (target/'idle-metrics.json').write_text(json.dumps(metrics,indent=2))
                check(not any('chrome' in p.name().lower() or 'node' in p.name().lower() or p.name().lower() in ('python.exe','phantomresume desktop.exe') for p in owned[1:]), 'Idle app retained worker or browser')
            if kind == 'crash':
                ui.kill()
            else:
                win32gui.PostMessage(info['hwnd'], win32con.WM_CLOSE, 0, 0)
            check(wait_until(lambda: not any(p.is_running() for p in owned), 10), kind+' left owned processes running')
            proc.wait(timeout=5)
        finally:
            # Clean up only explicitly recorded test processes if an assertion failed.
            for p in reversed(owned):
                try:
                    if p.is_running():
                        p.kill()
                except psutil.NoSuchProcess:
                    pass
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)
    test('Fresh idle app measurement and normal close leaves no processes', lambda: external_fixture('idle'))
    test('Close during browser work stops worker and browser descendants', lambda: external_fixture('close'))
    test('Unexpected UI process death kills its owned browser job', lambda: external_fixture('crash'))
    server.shutdown()
