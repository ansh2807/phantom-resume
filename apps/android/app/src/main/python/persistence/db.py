import sqlite3
from pathlib import Path


ORIGINAL_SUBMISSIONS_DDL = """
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    company TEXT,
    role TEXT,
    ats TEXT,
    mode TEXT,
    variant TEXT,
    instruction_hash TEXT,
    file_hash TEXT,
    status TEXT,
    notes TEXT
);
"""


def apply_migrations(db_path: str) -> None:
    """Apply addon migrations idempotently. On a fresh DB, creates the
    original `submissions` schema first so ALTERs succeed."""
    here = Path(__file__).parent / "migrations"
    with sqlite3.connect(db_path) as conn:
        conn.execute(ORIGINAL_SUBMISSIONS_DDL)
        conn.commit()

        for sql_file in sorted(here.glob("*.sql")):
            for stmt in sql_file.read_text(encoding="utf-8").split(";"):
                stmt = stmt.strip()
                if not stmt:
                    continue
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as e:
                    msg = str(e).lower()
                    if "duplicate column" in msg or "already exists" in msg:
                        continue
                    raise
        conn.commit()
