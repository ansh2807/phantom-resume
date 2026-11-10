import dataclasses
import json
import sqlite3

from output.manifest import RunManifest
from persistence.forensic.decoy_writer import DecoyWriter


class Tracker:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.decoys = DecoyWriter(db_path)

    def record(self, manifest: RunManifest) -> None:
        # dataclasses.asdict recursively converts ChannelVerification
        # to plain dicts — JSON-serializable without default=str.
        manifest_dict = dataclasses.asdict(manifest)

        with sqlite3.connect(self.db_path) as conn:
            # real submission row (original schema requires `date`)
            if manifest.input_bundle:
                filename = manifest.input_bundle[0]
                conn.execute(
                    "INSERT INTO submissions "
                    "(date, filename, payload_sha256, submitted_at_utc, "
                    " run_id, output_mode, sequence) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (
                        manifest.at_utc,
                        filename,
                        manifest.payload_sha256,
                        manifest.at_utc,
                        manifest.run_id,
                        manifest.output_mode,
                        0,
                    ),
                )

            # run row
            conn.execute(
                "INSERT OR REPLACE INTO runs "
                "(run_id, at_utc, ats_target, payload_sha256, manifest_json) "
                "VALUES (?,?,?,?,?)",
                (
                    manifest.run_id,
                    manifest.at_utc,
                    manifest.ats_target,
                    manifest.payload_sha256,
                    json.dumps(manifest_dict),
                ),
            )

            # per-channel verification rows
            for name, v in manifest.verifier.items():
                conn.execute(
                    "INSERT OR REPLACE INTO channel_verifications "
                    "(run_id, channel, survived, bits_recovered, corruption) "
                    "VALUES (?,?,?,?,?)",
                    (
                        manifest.run_id,
                        name,
                        int(v.survived),
                        v.bits_recovered,
                        v.corruption,
                    ),
                )

        # decoy noise for forensic denial
        self.decoys.maybe_write({
            "filename": manifest.input_bundle[0] if manifest.input_bundle else "",
            "payload_sha256": manifest.payload_sha256,
            "submitted_at_utc": manifest.at_utc,
            "run_id": manifest.run_id,
        })
