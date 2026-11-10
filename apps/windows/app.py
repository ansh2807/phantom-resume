"""PhantomResume Desktop executable entry point."""
import os
import sys
from pathlib import Path


def main():
    if '--worker' in sys.argv:
        from desktop.jobs import worker_main
        return worker_main(sys.argv[sys.argv.index('--worker')+1])
    # Windowed executables have no standard streams; libraries still print diagnostics.
    for name in ('stdout', 'stderr'):
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, 'w', encoding='utf-8'))
    if '--self-test' in sys.argv:
        from desktop.selftest import run
        index = sys.argv.index('--self-test')
        target = Path(sys.argv[index+1]) if len(sys.argv) > index+1 else Path.home()/'Documents'/'PhantomResume Test'
        return run(target)
    from PySide6.QtWidgets import QApplication
    from desktop.window import Window
    app = QApplication(sys.argv)
    app.setApplicationName('PhantomResume Desktop')
    app.setOrganizationName('PhantomResume')
    app.setStyle('Fusion')
    instance_lock = None
    if '--lifecycle-fixture' not in sys.argv and '--screenshot' not in sys.argv:
        from PySide6.QtCore import QLockFile
        from PySide6.QtWidgets import QMessageBox
        from desktop.engine import data_root
        instance_lock = QLockFile(str(data_root()/'desktop-instance.lock'))
        if not instance_lock.tryLock(0):
            QMessageBox.information(None, 'PhantomResume is already open', 'Use the existing PhantomResume window. A second copy was not started.')
            return 0
        app.aboutToQuit.connect(instance_lock.unlock)
    window = Window()
    app.aboutToQuit.connect(window.shutdown)
    window.show()
    from PySide6.QtCore import Qt
    window.setFocusPolicy(Qt.StrongFocus)
    window.setFocus(Qt.OtherFocusReason)
    if '--lifecycle-fixture' in sys.argv:
        # Automated local-only acceptance harness; never used in normal launch.
        import json
        from PySide6.QtCore import QTimer
        config = json.loads(Path(sys.argv[sys.argv.index('--lifecycle-fixture')+1]).read_text(encoding='utf-8'))
        window.output = config['output']
        if config.get('url'):
            window.select_tool('probe')
            window.widgets['url'].setText(config['url'])
            QTimer.singleShot(100, window.start_job)
        def ready():
            Path(config['ready']).write_text(json.dumps({'pid': os.getpid(), 'hwnd': int(window.winId()), 'worker': int(window.worker.process.processId()) if window.worker else None}), encoding='utf-8')
        QTimer.singleShot(1200, ready)
    if '--screenshot' in sys.argv:
        from PySide6.QtCore import QTimer
        index = sys.argv.index('--screenshot')
        target = Path(sys.argv[index+1])
        target.parent.mkdir(parents=True, exist_ok=True)
        def capture():
            window.grab().save(str(target))
            app.quit()
        QTimer.singleShot(1000, capture)
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
