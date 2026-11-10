# Version 1.3.0 — development release

This release provides Windows and Android applications plus their build sources.
The existing README animation and illustration assets are retained.

## Evidence

- Windows: 78 passing acceptance cases, including cancellation, idle resource
  sampling, window close and worker/browser cleanup. Idle sample: 145.7 MB RAM,
  0% of one CPU core over 3 seconds; this is a sample, not a resource guarantee.
- Android: 40 passing synthetic checks on ARM64, versionCode 13, same release
  signing certificate as the prior APK, no app process/service after Back.
  x86_64 is packaged but was not device-tested in this update.
- Seven addon smoke assertions run inside the new Addon verification tool.
- Historical source audit: 166 passed, 0 failed, 7 not run. Not rerun for these apps.

## Boundaries

No live ATS submissions or screening effectiveness were tested. The addon API
has no document channels configured. Acrostic-verbs, synonym-sets, attention-path
and calibrator implementations remain missing. Word COM, LibreOffice and all
possible media/file variants are not covered. WebM visibility uses MOVIE/TITLE
in the tested parser, not the separate exact lowercase-title contract.

The Windows binary is unsigned. Android uses the existing local release key.
Native compilation/obfuscation are not guarantees against reverse engineering.
Personal resumes, databases and signing credentials are excluded.

Application source retains platform adaptations and is not byte-identical to
the original CLI. The GitHub CLI retains its existing read-only probe features.
Version 1.3 merges the three repaired core modules and adds the addon packages.
Detailed acceptance records and artifact hashes are in the platform subfolders.
