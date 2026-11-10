"""One disposable, owned process tree per run; no resident worker service."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal


class WindowsJob:
    """The OS kills this job's descendants when its last owning handle closes."""
    def __init__(self, pid):
        import win32api
        import win32con
        import win32job
        import win32process
        self.handle = win32job.CreateJobObject(None, '')
        try:
            info = win32job.QueryInformationJobObject(self.handle, win32job.JobObjectExtendedLimitInformation)
            info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            win32job.SetInformationJobObject(self.handle, win32job.JobObjectExtendedLimitInformation, info)
            process = win32api.OpenProcess(win32con.PROCESS_SET_QUOTA | win32con.PROCESS_TERMINATE | win32con.PROCESS_SET_INFORMATION, False, pid)
            try:
                win32job.AssignProcessToJobObject(self.handle, process)
                win32process.SetPriorityClass(process, win32process.BELOW_NORMAL_PRIORITY_CLASS)
            finally:
                process.Close()
        except Exception:
            self.close()
            raise

    def close(self):
        if self.handle is not None:
            self.handle.Close()
            self.handle = None


def compact_preview(value, budget=None):
    """Bound UI retained data. Complete results stay in each run's JSON file."""
    if budget is None:
        budget = [180000]
    if isinstance(value, dict):
        return {str(k): compact_preview(v, budget) for k, v in list(value.items())[:200]}
    if isinstance(value, (list, tuple)):
        return [compact_preview(v, budget) for v in value[:200]]
    if isinstance(value, str):
        limit = max(0, min(24000, budget[0]))
        budget[0] -= min(len(value), limit)
        return value[:limit] + ('\n[Preview shortened; open result.json for full data.]' if len(value) > limit else '')
    return value


class Worker(QObject):
    progress = Signal(str)
    done = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, key, params, parent=None):
        super().__init__(parent)
        self.key, self.params = key, dict(params)
        self.params['_job_id'] = uuid.uuid4().hex
        from .engine import default_output
        self.job_directory = Path(self.params.get('output') or default_output()) / self.params['_job_id']
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.SeparateChannels)
        self.process.started.connect(self._started)
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.readyReadStandardError.connect(self._read_error)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.timeout.connect(lambda: self.cancel('Stopped after the 15-minute run limit. Split large batches into smaller folders.'))
        self.lease = None
        self.temp_dir = None
        self.buffer = b''
        self.stderr = b''
        self.active = False
        self.completed = False
        self.cancelled = False
        self.failure = None

    def isRunning(self):
        return self.active

    def start(self):
        from .engine import scratch_root
        self.temp_dir = Path(tempfile.mkdtemp(prefix='phantom-job-', dir=scratch_root(1024*1024*1024 if self.key == 'probe' else 20*1024*1024)))
        request = self.temp_dir/'request.json'
        request.write_text(json.dumps({'key': self.key, 'params': self.params}), encoding='utf-8')
        env = QProcessEnvironment.systemEnvironment()
        env.insert('PYTHONUTF8', '1')
        env.insert('PYTHONUNBUFFERED', '1')
        env.insert('PHANTOM_JOB_TEMP', str(self.temp_dir))
        # Child uses the already extracted one-file runtime. It does not unpack
        # a second copy or launch a new GUI.
        env.remove('PYINSTALLER_RESET_ENVIRONMENT')
        for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
            env.insert(name, '1')
        self.process.setProcessEnvironment(env)
        args = ['--worker', str(request)]
        if not getattr(sys, 'frozen', False):
            args.insert(0, str(Path(__file__).resolve().parents[1]/'app.py'))
        self.active = True
        self.process.start(sys.executable, args)
        self.timeout.start(15*60*1000)

    def _started(self):
        try:
            if os.name != 'nt':
                raise RuntimeError('This desktop build requires Windows process ownership support.')
            self.lease = WindowsJob(int(self.process.processId()))
            # No tool code or browser runs until ownership has succeeded.
            self.process.write(b'GO\n')
            self.process.closeWriteChannel()
        except Exception as e:
            self.failure = 'Could not create an owned background process: '+str(e)
            self.process.kill()

    def _read_error(self):
        self.stderr = (self.stderr + bytes(self.process.readAllStandardError()))[-8000:]

    def _read(self):
        self.buffer += bytes(self.process.readAllStandardOutput())
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            try:
                message = json.loads(line.decode('utf-8'))
            except (ValueError, UnicodeError):
                continue
            if message.get('kind') == 'progress':
                self.progress.emit(str(message.get('text', ''))[:500])
            elif message.get('kind') == 'error':
                self.failure = str(message.get('text', 'Run failed.'))
            elif message.get('kind') == 'complete':
                self.completed = True
        if len(self.buffer) > 65536:
            self.buffer = b''

    def _error(self, error):
        if error == QProcess.FailedToStart:
            self.failure = 'Could not start the background worker: '+self.process.errorString()
            self._finished(-1, QProcess.CrashExit)

    def _finished(self, exit_code, status):
        if not self.active:
            return
        self._read()
        self._read_error()
        self.timeout.stop()
        if self.lease:
            self.lease.close()
            self.lease = None
        self.active = False
        if not self.cancelled and exit_code == 0 and self.completed:
            try:
                path = self.job_directory/'preview.json'
                if path.stat().st_size > 1500000:
                    raise ValueError('Result preview exceeded its memory limit. Full result is saved in the run folder.')
                self.done.emit(json.loads(path.read_text(encoding='utf-8')))
            except Exception as e:
                self.failed.emit(str(e))
        elif self.cancelled:
            self.failed.emit(self.failure or 'Run cancelled. Partial output, if any, is marked incomplete. Your original files are unchanged.')
        else:
            self.failed.emit(self.failure or 'The background worker stopped unexpectedly. '+self.stderr.decode('utf-8', 'replace')[-1500:])
        if self.temp_dir:
            # This directory was created by this worker; it contains only its request.
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None
        self.finished.emit()

    def cancel(self, reason=None):
        if not self.active:
            return
        self.cancelled = True
        self.failure = reason
        if self.lease:
            self.lease.close()
            self.lease = None
        self.process.kill()

    def shutdown(self):
        self.cancel()
        if self.process.state() != QProcess.NotRunning:
            self.process.waitForFinished(3000)
        if self.active:
            self._finished(-1, QProcess.CrashExit)


def worker_main(request_file):
    """Executed in the disposable process, before importing Qt or tool libraries."""
    import contextlib
    import traceback
    if os.name == 'nt':
        import ctypes
        import msvcrt
        from ctypes import wintypes
        get_handle = ctypes.windll.kernel32.GetStdHandle
        get_handle.argtypes = [wintypes.DWORD]
        get_handle.restype = wintypes.HANDLE
        # PyInstaller --windowed sets sys streams to None; QProcess still supplies
        # inherited Windows pipe handles. Reconstruct only those worker streams.
        if sys.stdin is None:
            sys.stdin = os.fdopen(msvcrt.open_osfhandle(get_handle(-10), os.O_RDONLY), 'r', encoding='utf-8')
        if sys.stdout is None:
            sys.stdout = os.fdopen(msvcrt.open_osfhandle(get_handle(-11), os.O_WRONLY), 'w', encoding='utf-8', buffering=1)
    protocol = sys.stdout
    if sys.stdin.readline().strip() != 'GO':
        return 2
    def emit(kind, text=''):
        protocol.write(json.dumps({'kind': kind, 'text': text}, ensure_ascii=True)+'\n')
        protocol.flush()
    try:
        request = json.loads(Path(request_file).read_text(encoding='utf-8'))
        # QtCore provides process plumbing; no Widgets or GUI is loaded in workers.
        from .engine import run_tool, data_root
        with open(os.devnull, 'w') as quiet, contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            result = run_tool(request['key'], request['params'], lambda text: emit('progress', text))
            preview = dict(result)
            preview['data'] = compact_preview(result['data'])
            preview['files'] = result['files'][:200]
            preview['preview_limited'] = True
            destination = Path(result['output_directory'])/'preview.json'
            temporary = destination.with_suffix('.tmp')
            temporary.write_text(json.dumps(preview, ensure_ascii=False, default=str), encoding='utf-8')
            temporary.replace(destination)
        emit('complete')
        return 0
    except Exception as e:
        from .engine import data_root
        (data_root()/'last-error.log').write_text(traceback.format_exc(), encoding='utf-8')
        emit('error', str(e))
        return 1
