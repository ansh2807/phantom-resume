from pathlib import Path

from orchestration.injector import ResumeInjector
from orchestration.tracker import Tracker
from output.manifest import OutputMode
from intelligence.codebook import PrivateCodebook
from persistence.db import apply_migrations


def run(
    bundle: list[Path],
    ats: str,
    payload: bytes,
    passphrase: bytes,
    mode: OutputMode = OutputMode.DOCX,
    semantic_channels=None,
    multi_artifact_channels=None,
    submission_channels=None,
    db_path: str = "submissions.db",
    codebook: PrivateCodebook | None = None,
) -> None:
    apply_migrations(db_path)

    injector = ResumeInjector(
        channels=[],
        semantic_channels=semantic_channels or [],
        multi_artifact_channels=multi_artifact_channels or [],
        submission_channels=submission_channels or [],
        mode=mode,
        lang="en",
        ats=ats,
        passphrase=passphrase,
    )
    codebook = codebook or PrivateCodebook.derive(ats, "default", [])
    manifest = injector.inject_bundle(bundle, payload)
    manifest.payload_codec_id = codebook.channel_id("main")

    Tracker(db_path).record(manifest)
    print(f"manifest: {manifest.run_id}")
