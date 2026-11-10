import secrets
import sqlite3
from datetime import datetime, timezone


class DecoyWriter:
    def __init__(self, db_path: str, decoy_rate: float = 0.3) -> None:
        self.db_path = db_path
        self.decoy_rate = decoy_rate

    def maybe_write(self, real_row: dict) -> None:
        if secrets.randbelow(100) / 100 >= self.decoy_rate:
            return
        decoy = {
            "date": datetime.now(timezone.utc).isoformat(),
            "filename": "resume_" + secrets.token_hex(3) + ".docx",
            "payload_sha256": secrets.token_hex(32),
            "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
            "run_id": "decoy-" + secrets.token_hex(4),
        }
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO submissions"
                "(date, filename, payload_sha256, submitted_at_utc, run_id) "
                "VALUES (?,?,?,?,?)",
                (decoy["date"], decoy["filename"],
                 decoy["payload_sha256"], decoy["submitted_at_utc"],
                 decoy["run_id"]),
            )
