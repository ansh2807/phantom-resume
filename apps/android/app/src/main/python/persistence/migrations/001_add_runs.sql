-- Add missing columns to the existing submissions table.
-- Uses the existing schema: date (NOT NULL), plus what the addon needs.
ALTER TABLE submissions ADD COLUMN run_id TEXT;
ALTER TABLE submissions ADD COLUMN output_mode TEXT;
ALTER TABLE submissions ADD COLUMN filename TEXT;
ALTER TABLE submissions ADD COLUMN submitted_at_utc TEXT;
ALTER TABLE submissions ADD COLUMN sequence INTEGER;
ALTER TABLE submissions ADD COLUMN payload_sha256 TEXT;

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    at_utc TEXT NOT NULL,
    ats_target TEXT,
    payload_sha256 TEXT NOT NULL,
    manifest_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS channel_verifications (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    channel TEXT NOT NULL,
    survived INTEGER NOT NULL,
    bits_recovered INTEGER NOT NULL,
    corruption REAL NOT NULL,
    PRIMARY KEY (run_id, channel)
);

CREATE INDEX IF NOT EXISTS idx_sub_run ON submissions(run_id);
