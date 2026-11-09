# Validation scope and known limitations

This is an experimental document toolkit, not a validated hiring product. Preserve the distinction between file content, parser extraction, model behavior, and hiring outcomes.

## What automated checks establish

The repository suite checks synthetic DOCX processing, metadata selection, local image/QR inspection, ReportLab return counters, basic API behavior and mocked read-only probe control flow. Runtime fixtures live in temporary directories and do not become repository content.

It does not establish Microsoft Word schema compliance for every document, visual layout fidelity, audio playback, compatibility with arbitrary embedded fonts, or employer ATS behavior. A test count varies with the fixture: missing audio, fonts or photos may be skipped.

## Browser probes

- `--probe-only` inspects controls and returns before filling, attaching or submitting. Visiting a public page still makes normal network requests to the site.
- Without `--probe-only`, the inherited automation can fill forms, upload a document and click Submit without an interactive approval gate. That code is preserved as an experimental feature, not recommended for real hiring portals.
- The legacy substring check for `demo`/test-board names is **not an authorization boundary**. It does not verify hostname ownership, redirects, job destinations, or permission to test. Use only an environment you control or are explicitly authorized to test.
- The bundled test-board addresses may be inactive. Do not assume a board is maintained or public test submissions are accepted.
- Submission code can mark `submitted=True` after a click and delay without proving that the application was accepted. Confirmation requires independent review.
- The adapters return no actual parsed resume text. Read-only inspection does not establish extraction success. Missing extraction is unknown, not failure or success.
- Fingerprinting and tuning values are heuristics. Changes to these weights are not a statistical estimate of effectiveness.

## Document and media processing

- `safe` is a mode name for metadata-only injection; it still modifies instructions in the file.
- Resume scoring is a local heuristic. Date/skill digits can be mistaken for metrics; substring checks can flag proper nouns; headings may be mistaken for bullets.
- Cover-letter fallback content may imply accomplishments not present in the source. Review every generated statement and supply only truthful metrics.
- ReportLab reconstructs a document rather than preserving the original layout. The XML regexes are not a general DOCX parser, and namespaced metadata can fall back to generic PDF values. Word-mode paragraph/image counters are placeholders.
- A PDF reader's `page.images` list may omit images with certain filter combinations. Inspect image XObjects when validating image preservation.
- Image re-saving may alter metadata or encoding. Compare decoded pixels when preservation matters. QR placement changes visible layout.
- Audio/font modules are experimental. Some errors are swallowed or returned by submodules without being propagated by the main orchestrator. A printed step is not proof of a successful transformation.
- The merger concatenates bodies but does not comprehensively merge styles, media relationships, numbering, or namespaces.
- LSB helpers have no explicit capacity check; the DOCX helper can store PNG bytes under an existing JPEG filename. Test copies only.
- Custom-font embedding and font-key handling require additional compatibility testing.
- HTML reports incorporate source content; treat reports generated from untrusted documents as untrusted HTML.
- Reusing one injector instance can accumulate step/error state. Use a new instance per output.

## Privacy and release boundaries

No real candidate documents, runtime logs, screenshots, extracted text, submission databases or tuned state are distributed. Example identity: `Test Candidate`, `test@example.com`, `+15550000000`. These are synthetic placeholders, not a working inbox or delivery guarantee.

The `.gitignore` excludes common document and runtime outputs. It cannot prevent someone from force-adding files or placing personal information inside code or documentation. Always review staged content before publishing.

Successful file verification, different hashes, confirmation emails, and interview invitations do not by themselves prove that a prompt-injection technique influenced a decision.
