"""
tracker.py — track submissions and outcomes, compute per-variant effectiveness
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime


class SubmissionTracker:
    def __init__(self, db_path='submissions.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
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
                status TEXT DEFAULT 'pending',
                notes TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def record(self, company, role, ats, mode, variant, instruction_hash, file_hash, notes=''):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO submissions (date, company, role, ats, mode, variant,
                                     instruction_hash, file_hash, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        ''', (datetime.now().isoformat(), company, role, ats, mode, variant,
              instruction_hash, file_hash, notes))
        conn.commit()
        conn.close()

    def update_status(self, submission_id, status, notes=''):
        conn = sqlite3.connect(self.db_path)
        conn.execute('UPDATE submissions SET status=?, notes=? WHERE id=?',
                     (status, notes, submission_id))
        conn.commit()
        conn.close()

    def effectiveness_report(self):
        """Return per-ATS / per-variant effectiveness."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # per-variant
        cur.execute('''
            SELECT variant,
                   COUNT(*) as total,
                   SUM(CASE WHEN status IN ('interview','screen') THEN 1 ELSE 0 END) as positives
            FROM submissions
            WHERE status != 'pending'
            GROUP BY variant
        ''')
        variants = [
            {'variant': r[0], 'total': r[1], 'positives': r[2] or 0,
             'rate': (r[2] or 0) / r[1] if r[1] else 0}
            for r in cur.fetchall()
        ]

        # per-mode
        cur.execute('''
            SELECT mode,
                   COUNT(*) as total,
                   SUM(CASE WHEN status IN ('interview','screen') THEN 1 ELSE 0 END) as positives
            FROM submissions
            WHERE status != 'pending'
            GROUP BY mode
        ''')
        modes = [
            {'mode': r[0], 'total': r[1], 'positives': r[2] or 0,
             'rate': (r[2] or 0) / r[1] if r[1] else 0}
            for r in cur.fetchall()
        ]

        # per-ATS
        cur.execute('''
            SELECT ats,
                   COUNT(*) as total,
                   SUM(CASE WHEN status IN ('interview','screen') THEN 1 ELSE 0 END) as positives
            FROM submissions
            WHERE status != 'pending'
            GROUP BY ats
        ''')
        ats_stats = [
            {'ats': r[0], 'total': r[1], 'positives': r[2] or 0,
             'rate': (r[2] or 0) / r[1] if r[1] else 0}
            for r in cur.fetchall()
        ]

        conn.close()
        return {'variants': variants, 'modes': modes, 'ats': ats_stats}

    def list_submissions(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('SELECT * FROM submissions ORDER BY id DESC')
        rows = cur.fetchall()
        conn.close()
        return rows
