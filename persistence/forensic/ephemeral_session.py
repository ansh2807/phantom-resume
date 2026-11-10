import atexit
import shutil
import tempfile
from pathlib import Path


class EphemeralSession:
    def __init__(self) -> None:
        self._dir = Path(tempfile.mkdtemp(prefix="phantom_"))
        atexit.register(self._cleanup)

    @property
    def path(self) -> Path:
        return self._dir

    def _cleanup(self) -> None:
        shutil.rmtree(self._dir, ignore_errors=True)
