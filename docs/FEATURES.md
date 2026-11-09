# Complete feature inventory

All modules from the toolkit are retained. CLI availability and test coverage are different things: API-only helpers are not automatically invoked by the full pipeline.

| Module | Capability |
| --- | --- |
| `resume_analyzer.py` | DOCX/PDF/text parsing; contact, section, length, formatting, keyword, verb and metric heuristics |
| `resume_improver.py` | Weak-verb, vague-language, missing-summary and missing-metric suggestions |
| `resume_verifier.py` | Local body/comment extraction and selected metadata |
| `resume_injector.py` | Mode/channel-plan orchestration; core metadata, hidden runs, comments, Unicode, headers/footers, fields, split content, Base64, acrostics, recruiter-note text and whitespace |
| `payloads.py` | Instruction strings, fragments, Base64 and whitespace encoding helpers |
| `payloads_i18n.py` | English, Hindi, French, German, Spanish, Arabic, Chinese and Japanese strings |
| `image_injector.py` | JPEG EXIF/XMP, PNG text chunks, WebP metadata, DOCX alt-text |
| `audio_injector.py` | Experimental embedded-media tag handlers, including MP3, MP4, FLAC/OGG and WebM paths |
| `qr_injector.py` | QR image generation and embedding in the document body |
| `font_injector.py` | Experimental name-table edits for existing embedded fonts |
| `custom_font.py` | Minimal TTF generation and experimental DOCX font embedding |
| `pdf_exporter.py` | Word conversion when available; ReportLab reconstruction fallback |
| `report_generator.py` | HTML report containing scores, suggestions and extracted content |
| `batch_processor.py` | Folder-level analysis, improvements and injected outputs |
| `cover_letter.py` | Metadata/hidden-content injection for existing DOCX letters |
| `cover_generator.py` | Template cover letters from resume analysis and a job description |
| `diff_reporter.py` | Added/removed/modified DOCX ZIP parts and byte deltas |
| `deep_metadata.py` | Theme names, numbering/settings comments, custom properties and ZIP comment |
| `stealth_mode.py` | Randomized channel plans, padding helper, instruction-variant helper and SHA-256 |
| `variants.py` | A–D instruction library |
| `tracker.py` | SQLite records and grouped outcomes |
| `merger.py` | Basic DOCX body concatenation with a page break |
| `lsb_stego.py` | Image least-significant-bit text encoder/decoder and DOCX helper |
| `template_library.py` | Font replacement and random template seeds: ten fonts, five section-order choices |
| `portal_notes.py` | Brief, full and minimal note templates |
| `script_obfuscation.py` | Devanagari substitution, Cyrillic homoglyphs and combining marks |
| `ats_profiles.py` | Static ATS aliases and heuristic channel profiles |
| `ats_fingerprint.py` | URL/HTML fingerprinting |
| `ats_extraction_analyzer.py` | Pattern-based signatures in supplied extracted text |
| `ats_probe_runner.py` | Adapter orchestration, null-safe extraction handling and JSON persistence |
| `ats_tuning.py` | Local heuristic weights and simple adjustments from probe logs |
| `ats_probes/base.py` | Common probe result/log handling |
| `ats_probes/greenhouse.py` | Greenhouse adapter with read-only inspection branch |
| `ats_probes/lever.py` | Lever adapter with read-only inspection branch |

## Python API examples

Use paths to synthetic copies. These examples do not access a portal.

```python
from core.resume_injector import ResumeInjector

job = ResumeInjector("demo-output/test-candidate.docx",
                     "demo-output/hindi-copy.docx", lang="hi")
job.channel_plan = ["metadata"]
result = job.run()
```

`lang` currently affects core subject/description content. It does not translate the resume, every channel, or the CLI. There is no `inject --lang` switch.

```python
from core.ats_extraction_analyzer import analyze_extraction
from core.template_library import generate_random_template_seed
from core.script_obfuscation import inject_script_variant

analysis = analyze_extraction("synthetic parser output")
seed = generate_random_template_seed()
variant = inject_script_variant("example text", "cyrillic")
```

Template seeds describe choices; they do not render 50 complete resume layouts. The extraction analyzer matches text signatures, not actual provenance or model behavior.
