# PhantomResume Desktop

A native Windows document workbench with 38 tools, animated navigation, background
processing, drag-and-drop, local reports, and a standalone browser inspector.

## Run

Version 1.3 uses disposable background workers and bounded result previews. Closing
the app stops its active worker and owned browser processes, including during a run.
There are no installed background services. A Cancel button is available for active
runs; interrupted exports are marked INCOMPLETE. See ARCHITECTURE.md for details.

Double-click **PhantomResume Desktop.exe**. Python and Microsoft Word are not needed.
The EXE contains its runtime and a compressed Chromium bundle. The app runtime
extracts on startup; Chromium unpacks only for browser inspection. First startup
and browser inspection can take a little time. Allow roughly 1.5 GB of free space
for temporary files and exports. Browser work can use another fixed local drive
if the default temporary drive is low on space. Windows x64 is required.

Choose a resume, select a tool, and press the green action button. The **Try a sample
resume** button creates fictional Test Candidate documents for practice. Results
include an HTML report and JSON data. Saved files can be opened by double-clicking.

## Injection tools in version 1.1

The app opens in Injection studio. All 15 channels are visible in its form.
Use All channels to select nuclear mode and every channel, or check individual
channels. Each channel also has its own sidebar tool under INJECTION TOOLS.
The category filter and search help navigate the expanded tool list. Deep metadata
now exposes its five channels separately. Existing audio, fonts and header/footer
parts are required for those channels; absent parts are reported as skipped.

The injection payload strings are retained. The desktop copy is not byte-identical
to the original: integration and correctness fixes are recorded in CORE-COMPARISON.json.
The original project folder has not been edited.

## Tools

- Resume review: analysis score, issues, writing suggestions and extracted text.
- Document inspector: core metadata, hidden runs, comments, image metadata, QR
  decoding, audio tags, embedded-font inventory, ZIP comment and XML parsing.
- Injection studio: safe/aggressive/nuclear, individual selection of all 15 channels,
  eight metadata languages, optional PDF.
- Full pipeline and folder batch processing.
- PDF export with document text, images and optional metadata.
- Cover-letter drafting and cover-letter injection.
- Original/modified DOCX comparison.
- Randomized channel plans; deep metadata; embedded test-font generation.
- Image LSB encoding/decoding, in standalone images or DOCX.
- Document merging with linked media; font styling and random style seeds.
- Payload languages, A–D variants, Base64, whitespace and script transforms.
- Portal note variants.
- ATS URL/page fingerprinting, local extraction-marker analysis and tuning.
- Read-only browser inspection with screenshot and visible-control inventory.
- Local outcome tracker: create, view, update and summarize manual records.

## Controls and storage

- Ctrl+O: choose resume. Ctrl+Enter: run current tool.
- Tool search filters the navigation. Motion plays briefly and then rests; minimize
  or deactivate the window to stop it immediately. Reduce motion disables it.
  Every long form and the tool list can scroll.
- Exports default to Documents/PhantomResume Exports. Change this in the app.
- Settings are stored in the user's Windows profile. Tracking and tuning live in
  %LOCALAPPDATA%/PhantomResume Desktop. Errors are logged there as last-error.log.
- Input documents are never modified; each run gets a new folder. Documents stay
  local. ATS fingerprint and browser inspection contact the URL you explicitly enter.
- No personal resume is bundled. The only sample identity is Test Candidate.

## Practical limits

- Scores, ATS weights and channel recommendations are heuristic, not validated
  probabilities or proof of hiring impact. Marker detection is extraction evidence.
- Media channels require suitable media. Missing assets are reported, not created
  (except QR and the explicit embedded-font fixture). Unsupported/corrupt media can fail.
- Language selection changes core metadata; other channels retain their existing text.
- The portable PDF renderer reflows content. Complex tables, headers, Word layout,
  hidden formatting and some non-Latin glyphs may not render identically. Inspect PDFs.
- Cover letters use templates and inferred fields; review names, claims and grammar.
- Font styling changes fonts. The random seed's section order/accent is not applied.
- The browser inspector does not click Apply, fill fields, upload or submit. It
  stops on detected login/payment pages. Actual portal submission automation is
  deliberately not exposed in the desktop UI, consistent with the testing rules.
- Live ATS behavior and every possible media encoding have not been certified.
- This is a local unsigned build; it has not been tested on every Windows machine.
- Inputs are limited to 128 MB; expanded DOCX content to 512 MB / 5,000 parts.
  Each UI run has a 15-minute timeout. Large batches should be split into folders.
  The last three bounded result previews are retained; full reports stay on disk.

## Build from source

Use Windows x64 and Python 3.12:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m PyInstaller --noconfirm PhantomResume.spec
```

Output: dist/PhantomResume Desktop.exe. This is a one-file build containing Qt,
Python dependencies and Chromium. The source includes the original core modules
plus desktop integration fixes. No original project directory is changed.

## Acceptance tests

```powershell
python app.py --self-test .\test-output
# Or test the packaged executable:
& '.\PhantomResume Desktop.exe' --self-test .\test-output
```

Tests use fictional documents and a local HTTP server; they do not make real job
applications. They verify document channels, PDF extraction, image preservation,
fonts, encoding, merging, tracking, browser no-click/no-submit behavior and all UI
tool forms. Results are written to acceptance-results.json and screenshots.

See THIRD_PARTY_NOTICES.txt and licenses/ for component terms.

## 1.3 update

PDF, embedded-font and FLAC/WebM repairs are merged from the original project.
Addon verification runs seven local synthetic checks. Addon source is bundled,
but its API still has no configured document channels. This does not establish
live ATS payload recovery. See the current Build verification.json for packaged
app checks; older screenshots and results are not evidence for this build.
