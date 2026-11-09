# Command reference

Run `python phantom_resume.py --help` or append `--help` to a subcommand. The CLI currently exposes 16 commands.

| Command | Purpose | Example arguments |
| --- | --- | --- |
| `analyze` | Heuristic resume score and issues | `resume.docx` |
| `improve` | Suggest textual rewrites and metrics | `resume.docx` |
| `inspect` | Local text and selected metadata | `resume.docx` |
| `inject` | Write an experimental DOCX copy | `resume.docx --mode aggressive --output output.docx --pdf` |
| `full` | Analyze, suggest, inject, inspect, report | `resume.docx --mode aggressive --output-dir output --pdf` |
| `batch` | Process top-level DOCX files in a folder | `input-folder --output-dir output --mode safe` |
| `cover` | Generate from a job description, or inject an existing letter | `resume.docx --jd job-description.txt --template professional --output cover.txt` |
| `ats` | URL/HTML fingerprint and heuristic profile | `https://your-authorized-test-board.example` |
| `diff` | Compare ZIP entries and uncompressed byte sizes | `original.docx changed.docx` |
| `stealth` | Random channel subset and file hash | `resume.docx --mode aggressive --output variant.docx` |
| `track` | Record local submission outcomes | `--db submissions.db` |
| `notes` | Generate experimental portal-note text | `--variant A --style brief` |
| `deep` | Modify theme, numbering, settings, custom properties and ZIP comment | `copy.docx` |
| `langs` | List eight payload languages | no arguments |
| `probe` | Inspect a supported form, or use legacy submission path | `greenhouse resume.docx --url URL --probe-only` |
| `tuning` | Display/reset stored heuristic channel weights | `greenhouse` or `--reset` |

## Cover letters

With `--jd`, `cover` generates text. Templates are `professional`, `short`, and `career_change`. Optional `--inject safe|aggressive|nuclear` creates a DOCX and a separate injected copy. Without `--jd`, `cover` follows the legacy existing-cover-letter path; specify `--mode` for that path.

## Tracking

```bash
# Synthetic record; this command records data, it does not submit anything.
python phantom_resume.py track --db demo-output/experiments.db --add "Example Company" "Test Role" unknown safe A
python phantom_resume.py track --db demo-output/experiments.db --status 1 screen
python phantom_resume.py track --db demo-output/experiments.db
```

The parent folder must already exist. Positive statuses in the current implementation are `screen` and `interview`. The report summarizes entered records; it does not establish causation or train a machine-learning model.

## Destructive-to-copy operations

`deep` and some Python helpers modify the path supplied to them. Run them on copies. `inject`, `stealth`, and legacy cover injection require different input and output paths. Batch outputs should be kept outside the input directory.

## Probe behavior

`--probe-only` is the documented inspection path. It stops before field filling, file upload, and submission, does not update tuning, and saves a JSON report on a successful form inspection. A normal non-probe-only run can automatically submit. No interactive confirmation prompt is built into that legacy path. Do not mistake a URL containing `demo` for permission to submit.

## Standalone verification scripts

```bash
python test_all_injections.py demo-output/test-candidate-injected.docx
python test_images.py demo-output/test-candidate-injected.docx --original demo-output/test-candidate.docx
```

`make_test_photo.py` and `test_photo_resume.py` are preserved legacy fixture generators. They write synthetic files in the current directory. The `examples/create_demo.py` generator groups files under `demo-output/`.
