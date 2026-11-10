from pathlib import Path
from channel.base import SubmissionEvent
from orchestration.injector import ResumeInjector


class BatchProcessor:
    def __init__(self, injector: ResumeInjector) -> None:
        self.injector = injector
        self._sequence = 0

    def run(self, folder_in: Path, folder_out: Path) -> list:
        folder_out.mkdir(parents=True, exist_ok=True)
        manifests = []
        for sub in sorted(folder_in.iterdir()):
            if not sub.is_dir():
                continue
            bundle = sorted(sub.glob("*"))
            if not bundle:
                continue
            payload = sub.name.encode()
            manifest_path = folder_out / f"{sub.name}.manifest.json"
            manifest = self.injector.inject_bundle(
                bundle, payload, manifest_out=manifest_path
            )
            manifests.append(manifest)

            event = SubmissionEvent(
                filename=bundle[0].name,
                submitted_at_utc=manifest.at_utc,
                sequence=self._sequence,
                ats=manifest.ats_target or "unknown",
            )
            self.injector.inject_submission(event, payload)
            self._sequence += 1
        return manifests
