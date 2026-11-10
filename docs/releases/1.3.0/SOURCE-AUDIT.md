# Historical source audit

Public copy: workstation paths replaced. This is not a rerun against the GitHub checkout or app packages.

# Full current-project test run

**166 passed, 0 failed, 7 not run.**

Tested the current original project after the supplied add-on and Path A PDF/font/audio repairs. No further repair patches were applied. All generated fixtures used temporary folders and synthetic data. Implementation hashes are checked before and after.

Counts include import, syntax, artifact and functional checks; they are not a count of independently verified features. The original test assertions are listed separately from their harness-execution check. Fixture-generator scripts are not assertion suites; this run generated equivalent documents using the authorized Test Candidate identity.

The prior audit blocks were reused where their contracts are unchanged. Split tests use the new 159-byte limit and explicit-length single-chunk API. Historical results were not overwritten. Add-on API success with empty channel lists or a short payload does not prove payload recovery.

## Failures

## Coverage limits

- Word COM PDF export and visual Word/phone UI: Only local headless tests run; existing desktop/mobile builds are outside the original-project scope
- LibreOffice rendered PDF: soffice is unavailable on PATH
- Live ATS submissions and screening success: No external applications submitted; local extraction tests cannot establish real screening outcomes
- Missing add-on implementation: channel/semantic/acrostic_verbs.py: No implementation supplied
- Missing add-on implementation: channel/semantic/synonym_sets.py: No implementation supplied
- Missing add-on implementation: channel/submission/attention_path.py: No implementation supplied
- Missing add-on implementation: intelligence/calibrator.py: No implementation supplied

## All checks

| Category | Check | Result |
|---|---|---|
| addon | FEC: three replicas recover | PASS |
| addon | FEC: single replica rejected | PASS |
| addon | FEC: one tampered body ignored | PASS |
| addon | FEC: invalid digest headers rejected | PASS |
| addon | FEC: conflicting payloads without a majority rejected | PASS |
| addon | FEC: two survivors recover after first replica loss | PASS |
| addon | FEC: two distinct replicas recover (0,1) | PASS |
| addon | FEC: two distinct replicas recover (0,2) | PASS |
| addon | FEC: same replica twice provides no redundancy | PASS |
| addon | FEC: replica 1 alone rejected | PASS |
| addon | FEC: replica 2 alone rejected | PASS |
| addon | FEC: two clean plus one corrupted recover | PASS |
| addon | FEC: one clean plus one corrupted rejected | PASS |
| addon | FEC: corrupted replica alone rejected | PASS |
| addon | Shares: 159-byte nonconsecutive recovery | PASS |
| addon | Shares: insufficient shares rejected | PASS |
| addon | Shares: duplicate indices rejected | PASS |
| addon | Shares: malformed share length rejected | PASS |
| addon | Shares: small secret exact round trip | PASS |
| addon | Single chunk: explicit length preserves leading zeros | PASS |
| addon | Guide: 500-byte chunked round trip | PASS |
| addon | Shares: arbitrary high-byte chunks round trip | PASS |
| addon | Shares: chunked leading zero bytes preserved | PASS |
| addon | Shares: encrypted payload exact recovery | PASS |
| addon | Shares: small encrypted FEC shard recovery | PASS |
| addon | Wiring: small-payload distribution and manifest chunk count | PASS |
| addon | Wiring: captured shares reconstruct a valid FEC shard | PASS |
| addon | Cipher: round trip | PASS |
| addon | Cipher: same-prefix messages use distinct nonces | PASS |
| addon | Cipher: rejects short passphrase | PASS |
| addon | Cipher: wrong ATS rejected | PASS |
| addon | Cipher: altered ciphertext rejected | PASS |
| addon | Cipher: distant bucket header rejected | PASS |
| addon | Cipher: adjacent bucket header tampering rejected | PASS |
| addon | Schema: original date column is NOT NULL | PASS |
| addon | Migration: existing original schema | PASS |
| addon | Migration: helper reruns without error | PASS |
| addon | Migration: all six new columns exist | PASS |
| addon | Decoy: insert satisfies original schema | PASS |
| addon | Migration: fresh empty database works (guide assertion) | PASS |
| addon | Manifest: identifier round trip | PASS |
| addon | Manifest: typed verification round trip | PASS |
| addon | Tracker: records loaded manifest and verification | PASS |
| addon | Tracker: records a real submissions row | PASS |
| addon | Tracker: stored manifest verification remains structured | PASS |
| addon | Ordering: round trip symbol 0 | PASS |
| addon | Ordering: round trip symbol 1 | PASS |
| addon | Ordering: round trip symbol 2 | PASS |
| addon | Ordering: round trip symbol 3 | PASS |
| addon | Timestamp: round trip b'ABC' | PASS |
| addon | Timestamp: round trip b'hello' | PASS |
| addon | Filename: all four separators round trip | PASS |
| addon | Timing: returns new event without mutating original | PASS |
| addon | Timing: payload symbol round trip | PASS |
| addon | Injector: empty bundle rejected explicitly | PASS |
| addon | Injector: channel calls, verification and manifest end-to-end | PASS |
| addon | Batch: empty subdirectory skipped | PASS |
| addon | Batch: nonempty bundle writes output manifest | PASS |
| addon | Direct PDF: actual parseable PDF contains fixture text | PASS |
| addon | API: fresh database end-to-end | PASS |
| addon | API: initialized database writes run | PASS |
| addon | Add-on CLI: help | PASS |
| addon | Add-on CLI: profile writes correct value | PASS |
| addon | Add-on CLI: injection executes successfully | PASS |
| addon | Add-on CLI: old cli.py relocated | PASS |
| integrity | All implementation Python files parse | PASS |
| imports | Import core.ats_fingerprint | PASS |
| imports | Import core.ats_profiles | PASS |
| imports | Import core.audio_injector | PASS |
| imports | Import core.batch_processor | PASS |
| imports | Import core.cover_generator | PASS |
| imports | Import core.cover_letter | PASS |
| imports | Import core.custom_font | PASS |
| imports | Import core.deep_metadata | PASS |
| imports | Import core.diff_reporter | PASS |
| imports | Import core.font_injector | PASS |
| imports | Import core.image_injector | PASS |
| imports | Import core.lsb_stego | PASS |
| imports | Import core.merger | PASS |
| imports | Import core.payloads | PASS |
| imports | Import core.payloads_i18n | PASS |
| imports | Import core.pdf_exporter | PASS |
| imports | Import core.portal_notes | PASS |
| imports | Import core.qr_injector | PASS |
| imports | Import core.report_generator | PASS |
| imports | Import core.resume_analyzer | PASS |
| imports | Import core.resume_improver | PASS |
| imports | Import core.resume_injector | PASS |
| imports | Import core.resume_verifier | PASS |
| imports | Import core.script_obfuscation | PASS |
| imports | Import core.stealth_mode | PASS |
| imports | Import core.template_library | PASS |
| imports | Import core.tracker | PASS |
| imports | Import core.variants | PASS |
| imports | Import payload.codec | PASS |
| imports | Import payload.decoy | PASS |
| imports | Import payload.encrypt | PASS |
| imports | Import payload.fec | PASS |
| imports | Import payload.split | PASS |
| imports | Import output.manifest | PASS |
| imports | Import output.pdf.direct | PASS |
| imports | Import output.pdf.rendered | PASS |
| imports | Import persistence.db | PASS |
| imports | Import persistence.forensic.decoy_writer | PASS |
| imports | Import persistence.forensic.ephemeral_session | PASS |
| imports | Import persistence.forensic.silent_failure | PASS |
| imports | Import channel.base | PASS |
| imports | Import channel.multi_artifact.ordering_permutation | PASS |
| imports | Import channel.multi_artifact.timestamp_delta | PASS |
| imports | Import channel.submission.filename_charset | PASS |
| imports | Import channel.submission.timing_minute | PASS |
| imports | Import intelligence.ats_profile | PASS |
| imports | Import intelligence.codebook | PASS |
| imports | Import orchestration.batch | PASS |
| imports | Import orchestration.injector | PASS |
| imports | Import orchestration.tracker | PASS |
| imports | Import phantom_resume | PASS |
| imports | Import addon_cli | PASS |
| imports | Import api | PASS |
| original | Original CLI analyze | PASS |
| original | Original CLI improve | PASS |
| original | Original CLI inspect | PASS |
| original | Original injection safe | PASS |
| original | Original injection aggressive | PASS |
| original | Original injection nuclear | PASS |
| original_assertions | Original assertions: subject present + injected | PASS |
| original_assertions | Original assertions: description present + injected | PASS |
| original_assertions | Original assertions: keywords present + injected | PASS |
| original_assertions | Original assertions: category present + injected | PASS |
| original_assertions | Original assertions: subject appears exactly once | PASS |
| original_assertions | Original assertions: description appears exactly once | PASS |
| original_assertions | Original assertions: JPEG EXIF injected | PASS |
| original_assertions | Original assertions: PNG text chunks injected | PASS |
| original_assertions | Original assertions: QR code decodes to instruction | PASS |
| original_assertions | Original assertions: hidden vanish runs | PASS |
| original_assertions | Original assertions: zero-width unicode present | PASS |
| original_assertions | Original assertions: white-colored text | PASS |
| original_assertions | Original assertions: script obfuscation | PASS |
| original_assertions | Original assertions: merger | PASS |
| original_assertions | Original assertions: LSB stego | PASS |
| original | Original test_all_injections execution | PASS |
| original | Original image inspector and pixel preservation | PASS |
| original | Original full pipeline and HTML report | PASS |
| original | Original batch produces two readable documents | PASS |
| original | Original cover generation and injection | PASS |
| original | Original cover legacy | PASS |
| original | Original CLI notes | PASS |
| original | Original CLI langs | PASS |
| original | Original CLI diff | PASS |
| original | Original CLI ATS URL-only detection | PASS |
| original | Original CLI stealth | PASS |
| original | Original CLI deep metadata | PASS |
| original | Original tracking add/update/report | PASS |
| original | Original ReportLab PDF content and image export | PASS |
| original | Original PDF preserves injected subject metadata | PASS |
| original | Original custom font embedding and font walker | PASS |
| original | Original font walker reads embedRegular fontKey | PASS |
| original | Original audio mp3 metadata survives parser | PASS |
| original | Original audio m4a metadata survives parser | PASS |
| original | Original audio flac metadata survives parser | PASS |
| original | Original audio ogg metadata survives parser | PASS |
| original | Original audio webm metadata survives parser | PASS |
| original | Original JPEG metadata changes preserve pixels | PASS |
| original | Original PNG metadata changes preserve pixels | PASS |
| original | Original WEBP metadata changes preserve pixels | PASS |
| coverage | Word COM PDF export and visual Word/phone UI | NOT RUN |
| coverage | LibreOffice rendered PDF | NOT RUN |
| coverage | Live ATS submissions and screening success | NOT RUN |
| coverage | Missing add-on implementation: channel/semantic/acrostic_verbs.py | NOT RUN |
| coverage | Missing add-on implementation: channel/semantic/synonym_sets.py | NOT RUN |
| coverage | Missing add-on implementation: channel/submission/attention_path.py | NOT RUN |
| coverage | Missing add-on implementation: intelligence/calibrator.py | NOT RUN |
| integrity | Implementation files unchanged by test run | PASS |

Logs and machine-readable results: [full_20261111_010332](<[local-path] resume xx/PhantomResume/addon_audit/full_20261111_010332/results.json>)

## WebM targeted-check clarification

The original metadata-visibility gate passes: ffprobe exposes the instruction under format.tags["MOVIE/TITLE"]. The additional exact format.tags["title"] expectation from the latest attachment does not pass. This exact-key check is separate from the 166-check regression tally. One actual top-level Tags element remains in the synthetic output, and decoded audio matches the input. No code was changed to normalize the key.
